"""Environment-driven application settings (roadmap: backend/app/config.py)."""

from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEV_JWT_SECRET = "dev-only-jwt-secret-not-for-production-0123456789"


class Settings(BaseSettings):
    """All runtime configuration comes from env / .env — never hardcode secrets."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "dev"
    cors_origins: list[str] = ["http://localhost:3000"]
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db: str = "musicmatch"
    spotify_client_id: str = ""
    spotify_client_secret: str = ""
    spotify_redirect_uri: str = "http://localhost:8000/api/v1/auth/callback"
    spotify_scope: str = "user-read-private user-top-read user-library-read"
    jwt_secret: str = DEV_JWT_SECRET
    jwt_ttl_seconds: int = 3600
    spotify_page_size: int = 50
    spotify_max_retries: int = 4
    spotify_request_timeout_seconds: float = 10.0

    @model_validator(mode="after")
    def _require_strong_jwt_secret_in_prod(self) -> "Settings":
        """HS256 keys must be >= 32 bytes (RFC 7518); dev default never ships."""
        if self.app_env == "prod":
            if self.jwt_secret == DEV_JWT_SECRET or len(self.jwt_secret.encode()) < 32:
                raise ValueError(
                    "JWT_SECRET must be overridden with a strong >=32 byte secret in prod"
                )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
