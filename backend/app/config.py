"""Environment-driven application settings (roadmap: backend/app/config.py)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All runtime configuration comes from env / .env — never hardcode secrets."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_env: str = "dev"
    cors_origins: list[str] = ["http://localhost:3000"]
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db: str = "musicmatch"
    spotify_client_id: str = ""
    spotify_client_secret: str = ""
    spotify_redirect_uri: str = "http://localhost:8000/api/v1/auth/callback"
    spotify_scope: str = "user-read-private user-top-read user-library-read"
    jwt_secret: str = "change-me-in-production"
    jwt_ttl_seconds: int = 3600


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
