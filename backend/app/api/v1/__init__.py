"""Versioned API surface (/api/v1) — the contract web and mobile clients share."""

from fastapi import APIRouter

from app.api.v1 import auth, health, matches, profile, sync

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(sync.router, prefix="/sync", tags=["sync"])
api_router.include_router(profile.router, tags=["profile"])
api_router.include_router(matches.router, tags=["matches"])
