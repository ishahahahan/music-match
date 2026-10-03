"""Spotify OAuth 2.0 authorization-code + PKCE + first-party JWT (roadmap Phase 1).

GET  /auth/login     -> redirect to Spotify with code_challenge
GET  /auth/callback  -> exchange code server-side, create users/{spotify_id}, mint JWT
POST /auth/token     -> issue access + refresh JWTs for API clients
"""

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/login", summary="Start Spotify PKCE login")
async def login() -> None:
    raise HTTPException(status_code=501, detail="Phase 1: build PKCE authorize URL")
