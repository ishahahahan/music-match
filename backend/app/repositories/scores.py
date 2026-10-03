"""compatibility_scores — one document per ordered pair, with full breakdown (Phase 3/4)."""

from datetime import datetime, timezone

from app.repositories.db import get_db

COLLECTION = "compatibility_scores"


async def save_score(
    pair_id: str, user1_id: str, user2_id: str, components: dict
) -> None:
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


async def top_matches_for(user_id: str, limit: int = 20) -> list[dict]:
    """Candidates where the user participates, ranked by overall score."""
    cursor = (
        get_db()[COLLECTION]
        .find({"$or": [{"user1_id": user_id}, {"user2_id": user_id}]})
        .sort("overall", -1)
        .limit(limit)
    )
    return await cursor.to_list(length=limit)
