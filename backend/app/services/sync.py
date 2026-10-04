"""Background Spotify ingestion and persisted sync progress."""

from datetime import datetime, timezone

from app.repositories.jobs import create_job, update_job
from app.repositories.scores import delete_scores_for
from app.repositories.tracks import bulk_upsert_tracks, bulk_upsert_user_items
from app.repositories.users import update_user_fields
from app.services.genres import extract_genres
from app.services.spotify_client import get_audio_features, paginated_get

TIME_RANGES = ("short_term", "medium_term", "long_term")
AUDIO_FEATURE_KEYS = (
    "danceability",
    "energy",
    "valence",
    "acousticness",
    "instrumentalness",
    "liveness",
    "speechiness",
    "tempo",
    "duration_ms",
)


def _audio_fingerprint(features: list[dict]) -> dict[str, float]:
    """Mean of each numeric audio feature across the sampled tracks (Phase 3 input)."""
    means: dict[str, float] = {}
    for key in AUDIO_FEATURE_KEYS:
        values = [
            float(feature[key])
            for feature in features
            if isinstance(feature.get(key), (int, float))
        ]
        if values:
            means[key] = round(sum(values) / len(values), 4)
    return means


def _track_document(item: dict, user_id: str, time_range: str | None = None) -> dict:
    track = item.get("track", item)
    track_id = track.get("id")
    if not track_id:
        return {}
    return {
        "_id": track_id,
        "spotify_id": track_id,
        "user_id": user_id,
        "name": track.get("name", ""),
        "artists": [
            {"id": artist.get("id"), "name": artist.get("name", "")}
            for artist in track.get("artists", [])
            if artist.get("id")
        ],
        "album": track.get("album", {}).get("name", ""),
        "time_range": time_range,
        "added_at": item.get("added_at"),
    }


async def run_user_sync(spotify_id: str, access_token: str, job_id: str | None = None) -> dict:
    """Ingest top and saved tracks, updating one durable job document."""
    job = await create_job(spotify_id) if job_id is None else {"_id": job_id}
    job_id = job["_id"]
    await update_job(job_id, status="running")
    total = 0
    top_artists: list[str] = []
    top_tracks: list[str] = []
    genre_tags: list[str] = []
    genre_weights: dict[str, float] = {}
    try:
        for time_range in TIME_RANGES:
            tracks = await paginated_get(access_token, "/me/top/tracks", time_range=time_range)
            artists = await paginated_get(access_token, "/me/top/artists", time_range=time_range)
            documents = [
                document
                for document in (_track_document(track, spotify_id, time_range) for track in tracks)
                if document
            ]
            total += await bulk_upsert_tracks(documents)
            top_tracks.extend(track.get("id") for track in tracks if track.get("id"))
            top_artists.extend(artist.get("name") for artist in artists if artist.get("name"))
            artist_count = max(len(artists), 1)
            for position, artist in enumerate(artists):
                weight = (artist_count - position) / artist_count
                for genre in artist.get("genres", []):
                    if isinstance(genre, str):
                        genre_tags.append(genre)
                        normalized = extract_genres([genre], limit=1)
                        if normalized:
                            genre_weights[normalized[0]] = (
                                genre_weights.get(normalized[0], 0.0) + weight
                            )

        saved = await paginated_get(access_token, "/me/tracks")
        saved_documents = [
            document
            for document in (_track_document(track, spotify_id) for track in saved)
            if document
        ]
        total += await bulk_upsert_user_items("saved_tracks", saved_documents)
        fields = {
            "top_tracks": list(dict.fromkeys(top_tracks))[:200],
            "top_artists": list(dict.fromkeys(top_artists))[:200],
            "top_genres": extract_genres(genre_tags),
            "genre_fingerprint": dict(
                sorted(genre_weights.items(), key=lambda item: item[1], reverse=True)[:50]
            ),
            "synced_track_count": total,
        }
        # Phase 3 input: audio centroid from the sampled top tracks (one API call).
        sample_ids = list(dict.fromkeys(track_id for track_id in top_tracks if track_id))[:100]
        if sample_ids:
            fingerprint = _audio_fingerprint(await get_audio_features(access_token, sample_ids))
            if fingerprint:
                fields["audio_fingerprint"] = fingerprint
        await update_user_fields(spotify_id, fields)
        # Phase 4.4: a re-sync invalidates this user's pair scores (lazy recompute).
        await delete_scores_for(spotify_id)
        await update_job(
            job_id,
            status="done",
            items_fetched=total,
            finished_at=datetime.now(timezone.utc),
        )
        return {"job_id": job_id, "items_fetched": total, "status": "done"}
    except Exception as exc:
        await update_job(
            job_id,
            status="error",
            error=str(exc),
            finished_at=datetime.now(timezone.utc),
        )
        raise
