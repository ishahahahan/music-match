"""Pydantic shapes for compatibility documents."""

from pydantic import BaseModel, Field


class ScoreBreakdown(BaseModel):
    """All three components — no more silent 0.40 cap."""

    genre: float = Field(ge=0, le=1)
    artist: float = Field(ge=0, le=1)
    audio: float = Field(ge=0, le=1)
    overall: float = Field(ge=0, le=1)


class CompatibilityScore(BaseModel):
    pair_id: str
    user1_id: str
    user2_id: str
    components: ScoreBreakdown
