"""Auto-generated profiles (roadmap Phase 3): zero-input profile from listening history.

GET   /me/profile      -> caller's derived profile (genre fingerprint, audio blurb, visibility)
PATCH /me/profile      -> update profile controls (discoverable / hidden)
GET   /users/{user_id} -> public profile when visibility allows
"""

from fastapi import APIRouter, Depends, HTTPException, Path

from app.api.dependencies import current_user_id
from app.models.user import ProfileRead, ProfileVisibilityIn
from app.repositories.users import get_user, set_visibility
from app.services.profiles import derive_profile

router = APIRouter()


@router.get("/me/profile", response_model=ProfileRead, summary="My auto-generated profile")
async def my_profile(user_id: str = Depends(current_user_id)) -> dict:
    user = await get_user(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User profile not found")
    return derive_profile(user)


@router.patch("/me/profile", response_model=ProfileRead, summary="Update profile controls")
async def update_profile(
    changes: ProfileVisibilityIn, user_id: str = Depends(current_user_id)
) -> dict:
    user = await get_user(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User profile not found")
    await set_visibility(user_id, changes.discoverable)
    user["discoverable"] = changes.discoverable
    return derive_profile(user)


@router.get("/users/{user_id}", response_model=ProfileRead, summary="Public profile by id")
async def public_profile(
    user_id: str = Path(..., description="users/{spotify_id}"),
) -> dict:
    user = await get_user(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User profile not found")
    if not user.get("discoverable", True):
        raise HTTPException(status_code=404, detail="User profile not found")
    return derive_profile(user)
