"""tracks/artists/playlist documents — bulkWrite upserts kill the legacy N+1 storm (Phase 2.5)."""

from motor.motor_asyncio import UpdateOne

from app.repositories.db import get_db


async def bulk_upsert_tracks(tracks: list[dict]) -> int:
    """One ordered bulkWrite per page of results; idempotent on re-sync."""
    if not tracks:
        return 0
    ops = [UpdateOne({"_id": t["_id"]}, {"$set": t}, upsert=True) for t in tracks]
    result = await get_db()["tracks"].bulk_write(ops, ordered=True)
    return result.upserted_count + result.modified_count


async def bulk_upsert_playlist_tracks(playlist_id: str, track_ids: list[str]) -> None:
    """Replace the mirror in one document write — never delete-then-insert."""
    await get_db()["playlists"].replace_one(
        {"_id": playlist_id},
        {"_id": playlist_id, "track_ids": track_ids},
        upsert=True,
    )
