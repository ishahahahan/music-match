"""Matching surface (roadmap Phase 4): ranked matches, swipes, chat starters, Blend.

GET    /matches                     -> ranked candidates with score breakdown
POST   /matches/{user_id}/accept    -> write users/{id}/swipes + matches/{pair_id}
POST   /matches/{user_id}/reject
GET    /matches/{user_id}/chat-starters -> generate_chat_starters() port
POST   /matches/{user_id}/blend     -> create the Blend playlist via Spotify Web API
"""

from fastapi import APIRouter, HTTPException, Path

router = APIRouter()


@router.get("/matches", summary="Ranked match candidates")
async def list_matches() -> None:
    raise HTTPException(status_code=501, detail="Phase 4: ranked compatibility docs")


@router.post("/matches/{user_id}/accept", summary="Accept a candidate")
async def accept(user_id: str = Path(...)) -> None:
    raise HTTPException(status_code=501, detail="Phase 4: swipe + mutual match")


@router.post("/matches/{user_id}/reject", summary="Reject a candidate")
async def reject(user_id: str = Path(...)) -> None:
    raise HTTPException(status_code=501, detail="Phase 4: swipe write")


@router.get("/matches/{user_id}/chat-starters", summary="Chat starters for a match")
async def chat_starters(user_id: str = Path(...)) -> None:
    raise HTTPException(
        status_code=501, detail="Phase 4: generate_chat_starters() port"
    )


@router.post("/matches/{user_id}/blend", summary="Create the Blend playlist")
async def blend(user_id: str = Path(...)) -> None:
    raise HTTPException(status_code=501, detail="Phase 4: Spotify playlist creation")
