"""swipes + matches — dormant SQL user_matches model brought to life (Phase 4)."""

from datetime import datetime, timezone

from app.repositories.db import get_db


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def record_swipe(user_id: str, target_id: str, action: str) -> None:
    """action: 'like' | 'pass'. _id = '{user}:{target}' keeps writes idempotent."""
    await get_db()["swipes"].replace_one(
        {"_id": f"{user_id}:{target_id}"},
        {
            "_id": f"{user_id}:{target_id}",
            "user_id": user_id,
            "target_id": target_id,
            "action": action,
            "at": _utcnow(),
        },
        upsert=True,
    )


async def get_swipe(user_id: str, target_id: str) -> dict | None:
    return await get_db()["swipes"].find_one({"_id": f"{user_id}:{target_id}"})


async def upsert_match(pair_id: str, user1_id: str, user2_id: str, status: str) -> None:
    await get_db()["matches"].replace_one(
        {"_id": pair_id},
        {
            "_id": pair_id,
            "user1_id": user1_id,
            "user2_id": user2_id,
            "status": status,
            "chat_starter": None,
            "blend_playlist_id": None,
            "updated_at": _utcnow(),
        },
        upsert=True,
    )


async def get_match(pair_id: str) -> dict | None:
    return await get_db()["matches"].find_one({"_id": pair_id})
