"""Spotify Web API client: PKCE, pagination, retry/backoff (roadmap Phase 2).

Token exchange and paginated fetching are implemented here once — never in routers.
"""

import base64
import hashlib
import secrets
from urllib.parse import urlencode

AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE = "https://api.spotify.com/v1"


def generate_pkce_pair() -> tuple[str, str]:
    """Return (code_verifier, code_challenge) using the S256 method."""
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return verifier, challenge


def build_authorize_url(
    client_id: str,
    redirect_uri: str,
    challenge: str,
    scope: str,
    state: str,
) -> str:
    params = urlencode(
        {
            "client_id": client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "scope": scope,
            "state": state,
            "code_challenge_method": "S256",
            "code_challenge": challenge,
        }
    )
    return f"{AUTH_URL}?{params}"


async def exchange_code(
    client_id: str, client_secret: str, code: str, verifier: str
) -> dict:
    """Exchange the authorization code for tokens — server-side only (Phase 1 TODO)."""
    raise NotImplementedError("Phase 1: POST token endpoint with code_verifier")


async def paginated_get(access_token: str, path: str, **params: object) -> list[dict]:
    """Follow offset/limit until exhausted — no more limit=50 truncation (Phase 2 TODO)."""
    raise NotImplementedError("Phase 2: loop pages with Retry-After backoff on 429")
