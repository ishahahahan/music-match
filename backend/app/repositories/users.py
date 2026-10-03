"""users collection — documents replace the legacy SQL users table (Phase 1).

No foreign keys: users/{spotify_id} is created on first login and profile data
is denormalized into the document, so models evolve field-by-field.
"""

from datetime import datetime, timezone

from app.repositories.db import get_db

COLLECTION = "users"


async def create_or_update_user(spotify_id: str, profile: dict) -> dict:
    """Upsert the user document keyed by Spotify id (replaces the FK-broken upsert)."""
    now = datetime.now(timezone.utc)
    doc = {"_id": spotify_id, **profile, "created_at": now, "updated_at": now}
    await get_db()[COLLECTION].replace_one({"_id": spotify_id}, doc, upsert=True)
    return doc


async def get_user(spotify_id: str) -> dict | None:
    return await get_db()[COLLECTION].find_one({"_id": spotify_id})


async def set_visibility(spotify_id: str, discoverable: bool) -> None:
    await get_db()[COLLECTION].update_one(
        {"_id": spotify_id}, {"$set": {"discoverable": discoverable}}
    )
