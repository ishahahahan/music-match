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


async def list_swipes(user_id: str) -> list[dict]:
    """Every swipe this user has made — used to filter ranked candidates."""
    return await get_db()["swipes"].find({"user_id": user_id}).to_list(length=10_000)


async def upsert_match(pair_id: str, user1_id: str, user2_id: str, status: str) -> None:
    # $set/$setOnInsert instead of replace_one so repeat accepts never wipe
    # chat_starter or blend_playlist_id once they exist.
    await get_db()["matches"].update_one(
        {"_id": pair_id},
        {
            "$set": {
                "user1_id": user1_id,
                "user2_id": user2_id,
                "status": status,
                "updated_at": _utcnow(),
            },
            "$setOnInsert": {"chat_starter": None, "blend_playlist_id": None},
        },
        upsert=True,
    )


async def set_match_field(pair_id: str, **fields: object) -> None:
    await get_db()["matches"].update_one(
        {"_id": pair_id}, {"$set": {**fields, "updated_at": _utcnow()}}
    )


async def get_match(pair_id: str) -> dict | None:
    return await get_db()["matches"].find_one({"_id": pair_id})


async def delete_match(pair_id: str) -> int:
    result = await get_db()["matches"].delete_one({"_id": pair_id})
    return result.deleted_count
