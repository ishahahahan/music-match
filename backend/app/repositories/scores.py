"""compatibility_scores — one document per ordered pair, with full breakdown (Phase 3/4)."""

from datetime import datetime, timezone

from app.repositories.db import get_db

COLLECTION = "compatibility_scores"


async def save_score(pair_id: str, user1_id: str, user2_id: str, components: dict) -> None:
    doc = {
        "_id": pair_id,
        "user1_id": user1_id,
        "user2_id": user2_id,
        "components": components,
        "overall": components["overall"],
        "updated_at": datetime.now(timezone.utc),
    }
    await get_db()[COLLECTION].replace_one({"_id": pair_id}, doc, upsert=True)


async def get_pair_score(pair_id: str) -> dict | None:
    return await get_db()[COLLECTION].find_one({"_id": pair_id})


async def count_scores_for(user_id: str) -> int:
    return await get_db()[COLLECTION].count_documents(
        {"$or": [{"user1_id": user_id}, {"user2_id": user_id}]}
    )


async def delete_scores_for(user_id: str) -> int:
    """Invalidate a user's pair scores (Phase 4.4: re-sync marks scores stale)."""
    result = await get_db()[COLLECTION].delete_many(
        {"$or": [{"user1_id": user_id}, {"user2_id": user_id}]}
    )
    return result.deleted_count


async def top_matches_for(user_id: str, limit: int = 20, skip: int = 0) -> list[dict]:
    """Candidates where the user participates, ranked by overall score."""
    cursor = (
        get_db()[COLLECTION]
        .find({"$or": [{"user1_id": user_id}, {"user2_id": user_id}]})
        .sort("overall", -1)
        .skip(skip)
        .limit(limit)
    )
    return await cursor.to_list(length=limit)
