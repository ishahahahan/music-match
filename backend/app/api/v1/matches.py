"""Matching surface (roadmap Phase 4): ranked matches, swipes, chat starters, Blend.

GET    /matches                       -> ranked candidates with score breakdown (cursor-paged)
POST   /matches/recompute             -> on-demand score batch for the caller
POST   /matches/{user_id}/accept      -> swipe + mutual match (users/{id}/swipes, matches/{pair_id})
POST   /matches/{user_id}/reject      -> pass swipe, closes any open match
GET    /matches/{user_id}/chat-starters -> generate_chat_starters() port
DELETE /matches/{user_id}             -> unmatch
POST   /matches/{user_id}/blend       -> create the Blend playlist via Spotify Web API
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel

from app.api.dependencies import current_user_id
from app.repositories.matches import (
    delete_match,
    get_match,
    get_swipe,
    list_swipes,
    record_swipe,
    set_match_field,
    upsert_match,
)
from app.repositories.scores import count_scores_for, top_matches_for
from app.repositories.users import get_user
from app.services.matching import (
    blend_track_order,
    chat_starters,
    pair_id,
    recompute_for_user,
)
from app.services.spotify_client import add_playlist_tracks, create_playlist
from app.models.match import (
    BlendRequest,
    BlendResult,
    ChatStartersOut,
    MatchCandidate,
    MatchesPage,
    RecomputeResult,
    SwipeResult,
)

logger = logging.getLogger("musicmatch.matches")

router = APIRouter()


class SelfAction(BaseModel):
    """Response for DELETE /matches/{user_id}."""

    unmatched: bool
    pair_id: str


async def _other_user(user_id: str, target_id: str) -> dict:
    if target_id == user_id:
        raise HTTPException(status_code=422, detail="Cannot match with yourself")
    target = await get_user(target_id)
    if target is None or not target.get("discoverable", True):
        raise HTTPException(status_code=404, detail="User not found")
    return target


def _other_id(score_doc: dict, user_id: str) -> str:
    other = score_doc["user1_id"] if score_doc["user2_id"] == user_id else score_doc["user2_id"]
    return str(other)


def _candidate(score_doc: dict, user_id: str, other: dict | None) -> MatchCandidate:
    components = score_doc.get("components") or {}
    score = {
        key: float(components.get(key, score_doc.get("overall", 0.0)))
        for key in ("genre", "artist", "audio", "overall")
    }
    return MatchCandidate(
        pair_id=score_doc["_id"],
        user_id=_other_id(score_doc, user_id),
        display_name=str((other or {}).get("display_name", "")),
        score=score,  # type: ignore[arg-type]
        headline={
            "top_genre": ((other or {}).get("top_genres") or [None])[0],
            "top_artist": ((other or {}).get("top_artists") or [None])[0],
        },
    )


@router.get("/matches", response_model=MatchesPage, summary="Ranked match candidates")
async def list_matches(
    limit: int = Query(20, ge=1, le=50),
    cursor: str | None = Query(None, pattern=r"^\d+$", description="Offset cursor"),
    user_id: str = Depends(current_user_id),
) -> MatchesPage:
    offset = int(cursor) if cursor else 0
    # On-demand compute for new/re-invalidated users (roadmap Phase 4.1 v1).
    if await count_scores_for(user_id) == 0:
        await recompute_for_user(user_id)

    swiped = {swipe["target_id"] for swipe in await list_swipes(user_id)}
    collected: list[MatchCandidate] = []
    raw_offset = offset
    exhausted = False
    while len(collected) < limit:
        page = await top_matches_for(user_id, limit=limit + 1, skip=raw_offset)
        if not page:
            exhausted = True
            break
        consumed = 0
        for score_doc in page:
            consumed += 1
            if _other_id(score_doc, user_id) in swiped:
                continue
            other = await get_user(_other_id(score_doc, user_id))
            if other is None:
                continue
            collected.append(_candidate(score_doc, user_id, other))
            if len(collected) >= limit:
                break
        raw_offset += consumed
        if len(page) < limit + 1:
            # Short page == raw scores exhausted (a full consume of a short page
            # is guaranteed: hitting `limit` requires consumed >= limit >= len(page)).
            exhausted = True
            break
        # Full page fully consumed but still hungry -> fetch more; if we stopped
        # mid-page the cursor rewinds to the first unconsumed score.
    return MatchesPage(
        items=collected,
        next_cursor=None if exhausted else str(raw_offset),
        limit=limit,
    )


@router.post("/matches/recompute", response_model=RecomputeResult, summary="Recompute my scores")
async def recompute(user_id: str = Depends(current_user_id)) -> RecomputeResult:
    return RecomputeResult(scores_written=await recompute_for_user(user_id))


@router.post(
    "/matches/{target_id}/accept",
    response_model=SwipeResult,
    summary="Accept a candidate",
)
async def accept(
    target_id: str = Path(...), user_id: str = Depends(current_user_id)
) -> SwipeResult:
    await _other_user(user_id, target_id)
    await record_swipe(user_id, target_id, "like")
    reverse = await get_swipe(target_id, user_id)
    status = "matched" if reverse and reverse.get("action") == "like" else "liked"
    key = pair_id(user_id, target_id)
    low, high = sorted((user_id, target_id))
    await upsert_match(key, low, high, status)
    return SwipeResult(target_id=target_id, action="like", pair_id=key, match_status=status)


@router.post(
    "/matches/{target_id}/reject",
    response_model=SwipeResult,
    summary="Reject a candidate",
)
async def reject(
    target_id: str = Path(...), user_id: str = Depends(current_user_id)
) -> SwipeResult:
    await _other_user(user_id, target_id)
    await record_swipe(user_id, target_id, "pass")
    key = pair_id(user_id, target_id)
    match = await get_match(key)
    status = None
    if match is not None:
        status = "passed"
        await set_match_field(key, status=status)
    return SwipeResult(target_id=target_id, action="pass", pair_id=key, match_status=status)


@router.get(
    "/matches/{target_id}/chat-starters",
    response_model=ChatStartersOut,
    summary="Chat starters for a match",
)
async def chat_starters_for(
    target_id: str = Path(...), user_id: str = Depends(current_user_id)
) -> ChatStartersOut:
    key = pair_id(user_id, target_id)
    match = await get_match(key)
    if match is None:
        raise HTTPException(status_code=404, detail="No match between these users")
    if match.get("status") != "matched":
        raise HTTPException(status_code=409, detail="Not mutually matched yet")
    me = await get_user(user_id)
    other = await get_user(target_id)
    if me is None or other is None:
        raise HTTPException(status_code=404, detail="User not found")
    starters = chat_starters(me, other)
    if not match.get("chat_starter") and starters:
        await set_match_field(key, chat_starter=starters[0])
    return ChatStartersOut(pair_id=key, starters=starters)


@router.delete("/matches/{target_id}", response_model=SelfAction, summary="Unmatch a candidate")
async def unmatch(
    target_id: str = Path(...), user_id: str = Depends(current_user_id)
) -> SelfAction:
    key = pair_id(user_id, target_id)
    deleted = await delete_match(key)
    if deleted == 0:
        raise HTTPException(status_code=404, detail="No match between these users")
    await record_swipe(user_id, target_id, "pass")
    return SelfAction(unmatched=True, pair_id=key)


@router.post(
    "/matches/{target_id}/blend",
    response_model=BlendResult,
    summary="Create the Blend playlist",
)
async def blend(
    request: BlendRequest,
    target_id: str = Path(...),
    user_id: str = Depends(current_user_id),
) -> BlendResult:
    key = pair_id(user_id, target_id)
    match = await get_match(key)
    if match is None:
        raise HTTPException(status_code=404, detail="No match between these users")
    if match.get("status") != "matched":
        raise HTTPException(status_code=409, detail="Not mutually matched yet")
    me = await get_user(user_id)
    other = await get_user(target_id)
    if me is None or other is None:
        raise HTTPException(status_code=404, detail="User not found")
    track_ids = blend_track_order(me.get("top_tracks") or [], other.get("top_tracks") or [])
    if not track_ids:
        raise HTTPException(
            status_code=409, detail="Not enough synced listening history to blend yet"
        )
    try:
        playlist = await create_playlist(
            request.access_token,
            name=f"MusicMatch Blend — {me.get('display_name', 'you')} & "
            f"{other.get('display_name', 'them')}",
            description="Created by MusicMatch from your shared taste.",
        )
        playlist_id = str(playlist.get("id", ""))
        if not playlist_id:
            raise RuntimeError("Spotify did not return a playlist id")
        await add_playlist_tracks(
            request.access_token, playlist_id, [f"spotify:track:{tid}" for tid in track_ids]
        )
    except RuntimeError as exc:
        logger.warning("blend_failed pair_id=%s error=%s", key, exc)
        raise HTTPException(status_code=502, detail="Spotify could not create the playlist")
    await set_match_field(key, blend_playlist_id=playlist_id)
    return BlendResult(
        pair_id=key,
        playlist_id=playlist_id,
        playlist_url=(playlist.get("external_urls") or {}).get("spotify"),
        track_count=len(track_ids),
    )
