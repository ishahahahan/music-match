"""sync_jobs collection — real job status replaces the fabricated last_synced (Phase 2)."""

from datetime import datetime, timezone
from uuid import uuid4

from app.repositories.db import get_db

COLLECTION = "sync_jobs"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def create_job(user_id: str) -> dict:
    doc = {
        "user_id": user_id,
        "status": "pending",
        "items_fetched": 0,
        "started_at": _utcnow(),
        "finished_at": None,
        "error": None,
    }
    doc["_id"] = uuid4().hex
    await get_db()[COLLECTION].insert_one(doc)
    return doc


async def update_job(job_id: str, **fields: object) -> None:
    fields["updated_at"] = _utcnow()
    await get_db()[COLLECTION].update_one({"_id": job_id}, {"$set": fields})


async def latest_job(user_id: str) -> dict | None:
    return await get_db()[COLLECTION].find_one({"user_id": user_id}, sort=[("started_at", -1)])
