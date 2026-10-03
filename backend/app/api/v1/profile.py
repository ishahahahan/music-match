"""Auto-generated profiles (roadmap Phase 3): zero-input profile from listening history.

GET /me/profile     -> caller's derived profile (genre fingerprint, audio blurb, visibility)
GET /users/{user_id}-> public profile when visibility allows
"""

from fastapi import APIRouter, HTTPException, Path

router = APIRouter()


@router.get("/me/profile", summary="My auto-generated profile")
async def my_profile() -> None:
    raise HTTPException(status_code=501, detail="Phase 3: derive profile document")


@router.get("/users/{user_id}", summary="Public profile by id")
async def public_profile(
    user_id: str = Path(..., description="users/{spotify_id}")
) -> None:
    raise HTTPException(
        status_code=501, detail="Phase 3: visibility-aware profile read"
    )
