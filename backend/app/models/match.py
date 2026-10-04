"""Pydantic shapes for swipes and matches."""

from typing import Literal

from pydantic import BaseModel, Field

from app.models.score import ScoreBreakdown

Action = Literal["like", "pass"]
MatchStatus = Literal["pending", "liked", "matched", "passed"]


class SwipeIn(BaseModel):
    target_id: str
    action: Action


class MatchDoc(BaseModel):
    pair_id: str
    user1_id: str
    user2_id: str
    status: MatchStatus = "pending"
    chat_starter: str | None = None
    blend_playlist_id: str | None = None


class Headline(BaseModel):
    """One-line taste preview shown on a candidate card."""

    top_genre: str | None = None
    top_artist: str | None = None


class MatchCandidate(BaseModel):
    pair_id: str
    user_id: str
    display_name: str
    score: ScoreBreakdown
    headline: Headline


class MatchesPage(BaseModel):
    """Cursor-paginated ranked candidates (Phase 5 pagination contract)."""

    items: list[MatchCandidate]
    next_cursor: str | None = None
    limit: int


class SwipeResult(BaseModel):
    target_id: str
    action: Action
    pair_id: str
    match_status: MatchStatus | None = None


class ChatStartersOut(BaseModel):
    pair_id: str
    starters: list[str]


class BlendRequest(BaseModel):
    # Phase 1 will replace this with the server-held refresh token; until then the
    # client passes its short-lived Spotify token the same way POST /sync/start does.
    access_token: str = Field(min_length=1)


class BlendResult(BaseModel):
    pair_id: str
    playlist_id: str
    playlist_url: str | None = None
    track_count: int


class RecomputeResult(BaseModel):
    scores_written: int
