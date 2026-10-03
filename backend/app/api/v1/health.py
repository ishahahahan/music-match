"""Liveness probe — used by uvicorn boot checks and the Docker healthcheck."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health", summary="Service liveness")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "musicmatch-api"}
