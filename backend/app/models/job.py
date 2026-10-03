"""Pydantic shapes for sync job documents."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

JobStatus = Literal["pending", "running", "done", "error"]


class SyncJob(BaseModel):
    user_id: str
    status: JobStatus = "pending"
    items_fetched: int = 0
    started_at: datetime
    finished_at: datetime | None = None
    error: str | None = None
