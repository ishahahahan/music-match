"""Listening-history sync (roadmap Phase 2): paginated fetch + real job status.

POST /sync/start -> spawn background job document
GET  /sync/status -> read sync_jobs document (no fabricated timestamps)
"""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.dependencies import current_user_id
from app.repositories.jobs import create_job, latest_job
from app.services.sync import run_user_sync

router = APIRouter()


class SyncStartRequest(BaseModel):
    access_token: str = Field(min_length=1)


@router.post("/start", summary="Start a listening-history sync")
async def start_sync(
    request: SyncStartRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(current_user_id),
) -> dict:
    existing = await latest_job(user_id)
    if existing and existing.get("status") in {"pending", "running"}:
        raise HTTPException(status_code=409, detail="A sync is already running")
    job = await create_job(user_id)
    background_tasks.add_task(run_user_sync, user_id, request.access_token, job["_id"])
    return {"job_id": job["_id"], "status": job["status"], "items_fetched": 0}


@router.get("/status", summary="Current sync job status")
async def sync_status(user_id: str = Depends(current_user_id)) -> dict:
    job = await latest_job(user_id)
    if job is None:
        raise HTTPException(status_code=404, detail="No sync has been started")
    job["_id"] = str(job["_id"])
    return job
