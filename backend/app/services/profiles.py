"""Deterministic profile derivation from the normalized user document."""


def derive_profile(user: dict) -> dict:
    """Build a complete, zero-input profile from sync-derived user fields."""
    genres = [genre for genre in user.get("top_genres", []) if isinstance(genre, str)]
    artists = [artist for artist in user.get("top_artists", []) if isinstance(artist, str)]
    tracks = [track for track in user.get("top_tracks", []) if isinstance(track, str)]
    audio = {
        key: float(value)
        for key, value in user.get("audio_fingerprint", {}).items()
        if isinstance(value, (int, float))
    }
    if genres:
        genre_text = ", ".join(genres[:3])
        blurb = f"A {genre_text} listener who likes discovering new sounds."
    else:
        blurb = "A curious listener building a music profile."
    return {
        "spotify_id": str(user.get("_id", user.get("spotify_id", ""))),
        "display_name": user.get("display_name", ""),
        "top_genres": genres,
        "genre_fingerprint": user.get("genre_fingerprint", {}),
        "top_artists": artists[:200],
        "top_tracks": tracks[:200],
        "audio_fingerprint": audio,
        "music_blurb": blurb,
        "discoverable": user.get("discoverable", True),
        "synced_track_count": int(user.get("synced_track_count", 0)),
    }
