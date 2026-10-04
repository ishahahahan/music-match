"""Pydantic shapes for user documents."""

from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    """Normalized Spotify profile data stored on the user document."""

    display_name: str = ""
    images: list[str] = Field(default_factory=list)
    country: str | None = None


class ProfileRead(BaseModel):
    """Auto-generated profile returned by GET /me/profile (Phase 3)."""

    spotify_id: str
    display_name: str
    top_genres: list[str] = Field(default_factory=list)
    genre_fingerprint: dict[str, float] = Field(default_factory=dict)
    top_artists: list[str] = Field(default_factory=list)
    top_tracks: list[str] = Field(default_factory=list)
    audio_fingerprint: dict[str, float] = Field(default_factory=dict)
    music_blurb: str = ""
    discoverable: bool = True
    synced_track_count: int = 0


class ProfileVisibilityIn(BaseModel):
    """Profile control: discoverable (shown in matching) vs hidden."""

    discoverable: bool
