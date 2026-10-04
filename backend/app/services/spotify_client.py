"""Spotify Web API client: PKCE, pagination, retry/backoff (roadmap Phase 2).

Token exchange and paginated fetching are implemented here once — never in routers.
"""

import base64
import hashlib
import secrets
import asyncio
from urllib.parse import urlencode

import httpx

from app.config import settings

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
    client_id: str,
    client_secret: str,
    code: str,
    verifier: str,
    redirect_uri: str | None = None,
) -> dict:
    """Exchange an authorization code for Spotify tokens using PKCE."""
    body = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri or settings.spotify_redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret,
        "code_verifier": verifier,
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(TOKEN_URL, data=body, headers=headers)

    if response.status_code != httpx.codes.OK:
        raise RuntimeError(f"Token exchange failed: {response.status_code} {response.text}")

    token_response = response.json()
    if not isinstance(token_response, dict):
        raise RuntimeError("Token exchange failed: Spotify returned an invalid response")
    return token_response


async def paginated_get(access_token: str, path: str, **params: object) -> list[dict]:
    """Fetch every item from a Spotify paging endpoint with bounded retries."""
    if not path.startswith("/"):
        path = f"/{path}"

    query = dict(params)
    query.setdefault("limit", settings.spotify_page_size)
    offset = int(query.pop("offset", 0))
    items: list[dict] = []
    retries = 0

    async with httpx.AsyncClient(timeout=settings.spotify_request_timeout_seconds) as client:
        while True:
            page_params = {**query, "offset": offset}
            response = await client.get(
                f"{API_BASE}{path}",
                params=page_params,
                headers={"Authorization": f"Bearer {access_token}"},
            )

            if response.status_code == httpx.codes.TOO_MANY_REQUESTS:
                if retries >= settings.spotify_max_retries:
                    raise RuntimeError("Spotify request failed after rate-limit retries")
                retry_after = response.headers.get("Retry-After", "1")
                try:
                    delay = max(float(retry_after), 0.0)
                except ValueError:
                    delay = 1.0
                await asyncio.sleep(delay)
                retries += 1
                continue

            if response.status_code >= 500:
                if retries >= settings.spotify_max_retries:
                    raise RuntimeError(
                        f"Spotify request failed after retries: {response.status_code}"
                    )
                await asyncio.sleep(2**retries)
                retries += 1
                continue

            if response.status_code >= 400:
                raise RuntimeError(
                    f"Spotify request failed: {response.status_code} {response.text}"
                )

            retries = 0
            page = response.json()
            if not isinstance(page, dict) or not isinstance(page.get("items"), list):
                raise RuntimeError("Spotify returned an invalid paging response")

            page_items = [item for item in page["items"] if isinstance(item, dict)]
            items.extend(page_items)
            total = page.get("total")
            next_url = page.get("next")
            if (
                not page_items
                or (isinstance(total, int) and len(items) >= total)
                or (not isinstance(total, int) and next_url is None)
            ):
                return items
            offset += len(page_items)


async def _request_json(
    access_token: str, method: str, path: str, json_body: dict | None = None
) -> dict:
    """One Spotify call with the same bounded 429/5xx backoff as paginated_get."""
    retries = 0
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient(timeout=settings.spotify_request_timeout_seconds) as client:
        while True:
            response = await client.request(
                method, f"{API_BASE}{path}", json=json_body, headers=headers
            )
            if response.status_code == httpx.codes.TOO_MANY_REQUESTS:
                if retries >= settings.spotify_max_retries:
                    raise RuntimeError("Spotify request failed after rate-limit retries")
                try:
                    delay = max(float(response.headers.get("Retry-After", "1")), 0.0)
                except ValueError:
                    delay = 1.0
                await asyncio.sleep(delay)
                retries += 1
                continue
            if response.status_code >= 500:
                if retries >= settings.spotify_max_retries:
                    raise RuntimeError(
                        f"Spotify request failed after retries: {response.status_code}"
                    )
                await asyncio.sleep(2**retries)
                retries += 1
                continue
            if response.status_code >= 400:
                raise RuntimeError(f"Spotify request failed: {response.status_code}")
            payload = response.json()
            if not isinstance(payload, dict):
                raise RuntimeError("Spotify returned an invalid response")
            return payload


async def get_audio_features(access_token: str, track_ids: list[str]) -> list[dict]:
    """Audio features for up to 100 ids per call (Spotify's hard limit)."""
    features: list[dict] = []
    for start in range(0, len(track_ids), 100):
        chunk = track_ids[start : start + 100]
        payload = await _request_json(access_token, "GET", f"/audio-features?ids={','.join(chunk)}")
        features.extend(
            item for item in payload.get("audio_features", []) if isinstance(item, dict)
        )
    return features


async def get_current_user(access_token: str) -> dict:
    return await _request_json(access_token, "GET", "/me")


async def create_playlist(access_token: str, name: str, description: str = "") -> dict:
    """Create a private playlist for the token's owner (Blend, roadmap Phase 4.3)."""
    me = await get_current_user(access_token)
    user_id = me.get("id")
    if not user_id:
        raise RuntimeError("Spotify did not return a user id")
    return await _request_json(
        access_token,
        "POST",
        f"/users/{user_id}/playlists",
        {"name": name, "description": description, "public": False},
    )


async def add_playlist_tracks(access_token: str, playlist_id: str, uris: list[str]) -> None:
    """Append tracks in 100-uri batches (the documented add limit)."""
    for start in range(0, len(uris), 100):
        await _request_json(
            access_token,
            "POST",
            f"/playlists/{playlist_id}/tracks",
            {"uris": uris[start : start + 100]},
        )
