"""Phase 3: auto-profile endpoints — derivation, auth, and visibility rules."""

from tests.fakes import auth_headers, install_fake_db

ALICE = {
    "_id": "alice",
    "display_name": "Alice",
    "top_genres": ["indie rock", "dream pop"],
    "genre_fingerprint": {"indie rock": 2.0, "dream pop": 1.2},
    "top_artists": ["Radiohead", "Beach House"],
    "top_tracks": ["t1", "t2"],
    "audio_fingerprint": {"energy": 0.72, "valence": 0.61, "tempo": 118.0},
    "discoverable": True,
    "synced_track_count": 42,
}


def test_profile_requires_bearer_token(client):
    res = client.get("/api/v1/me/profile")
    assert res.status_code == 401
    body = res.json()
    assert body["error"]["code"] == 401
    assert body["request_id"]


def test_profile_rejects_garbage_token(client, monkeypatch):
    install_fake_db(monkeypatch)
    res = client.get("/api/v1/me/profile", headers={"Authorization": "Bearer nope"})
    assert res.status_code == 401


def test_profile_derives_from_sync_fields(client, monkeypatch):
    db = install_fake_db(monkeypatch)
    db["users"].docs["alice"] = dict(ALICE)

    res = client.get("/api/v1/me/profile", headers=auth_headers("alice"))

    assert res.status_code == 200
    data = res.json()["data"]
    assert data["display_name"] == "Alice"
    assert data["top_genres"] == ["indie rock", "dream pop"]
    assert data["genre_fingerprint"] == {"indie rock": 2.0, "dream pop": 1.2}
    assert data["audio_fingerprint"]["energy"] == 0.72
    assert data["music_blurb"]
    assert data["discoverable"] is True
    assert data["synced_track_count"] == 42


def test_profile_missing_user_returns_404(client, monkeypatch):
    install_fake_db(monkeypatch)
    res = client.get("/api/v1/me/profile", headers=auth_headers("ghost"))
    assert res.status_code == 404
    assert res.json()["error"]["message"] == "User profile not found"


def test_public_profile_hides_discoverable_false(client, monkeypatch):
    db = install_fake_db(monkeypatch)
    db["users"].docs["alice"] = dict(ALICE, discoverable=False)

    hidden = client.get("/api/v1/users/alice")
    assert hidden.status_code == 404  # indistinguishable from missing

    visible = client.get("/api/v1/users/alice", headers=auth_headers("someone"))
    assert visible.status_code == 404


def test_public_profile_visible_by_default(client, monkeypatch):
    db = install_fake_db(monkeypatch)
    db["users"].docs["alice"] = dict(ALICE)

    res = client.get("/api/v1/users/alice")
    assert res.status_code == 200
    assert res.json()["data"]["spotify_id"] == "alice"


def test_visibility_patch_roundtrip(client, monkeypatch):
    db = install_fake_db(monkeypatch)
    db["users"].docs["alice"] = dict(ALICE)

    patched = client.patch(
        "/api/v1/me/profile",
        headers=auth_headers("alice"),
        json={"discoverable": False},
    )
    assert patched.status_code == 200
    assert patched.json()["data"]["discoverable"] is False
    assert db["users"].docs["alice"]["discoverable"] is False

    public = client.get("/api/v1/users/alice")
    assert public.status_code == 404


def test_visibility_patch_validates_body(client, monkeypatch):
    db = install_fake_db(monkeypatch)
    db["users"].docs["alice"] = dict(ALICE)

    res = client.patch("/api/v1/me/profile", headers=auth_headers("alice"), json={})
    assert res.status_code == 422
    body = res.json()
    assert body["error"]["code"] == 422
    assert body["error"]["details"]
