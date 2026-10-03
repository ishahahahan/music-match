"""Pydantic shapes for swipes and matches."""

from typing import Literal

from pydantic import BaseModel

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
