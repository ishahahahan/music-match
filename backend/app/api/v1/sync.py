"""Listening-history sync (roadmap Phase 2): paginated fetch + real job status.

POST /sync/start -> spawn background job document
GET  /sync/status -> read sync_jobs document (no fabricated timestamps)
"""

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/start", summary="Start a listening-history sync")
async def start_sync() -> None:
    raise HTTPException(status_code=501, detail="Phase 2: paginated sync job")


@router.get("/status", summary="Current sync job status")
async def sync_status() -> None:
    raise HTTPException(status_code=501, detail="Phase 2: read job document")
