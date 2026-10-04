"""Phase 4: the matching surface end-to-end — rank, swipe, match, starters, blend.

Runs the real router -> service -> repository stack against the in-memory fake DB.
"""

from tests.fakes import auth_headers, install_fake_db

from app.services.matching import pair_id


def _users() -> dict:
    return {
        "alice": {
            "_id": "alice",
            "display_name": "Alice",
            "top_artists": ["Radiohead", "Beach House", "Tycho"],
            "top_genres": ["indie rock", "dream pop"],
            "genre_fingerprint": {"indie rock": 2.0, "dream pop": 1.0},
            "audio_fingerprint": {"energy": 0.7, "valence": 0.6, "tempo": 120.0},
            "discoverable": True,
        },
        "bob": {
            "_id": "bob",
            "display_name": "Bob",
            "top_artists": ["Radiohead", "Beach House", "Tycho"],
            "top_genres": ["indie rock", "dream pop"],
            "genre_fingerprint": {"indie rock": 2.0, "dream pop": 1.0},
            "audio_fingerprint": {"energy": 0.7, "valence": 0.6, "tempo": 120.0},
            "discoverable": True,
        },
        "carol": {
            "_id": "carol",
            "display_name": "Carol",
            "top_artists": ["Burna Boy"],
            "top_genres": ["afrobeats"],
            "genre_fingerprint": {"afrobeats": 2.0},
            "audio_fingerprint": {"energy": 0.9, "valence": 0.9, "tempo": 105.0},
            "discoverable": True,
        },
        "dave": {
            "_id": "dave",
            "display_name": "Dave",
            "top_artists": ["Dave Band"],
            "top_genres": ["drill"],
            "genre_fingerprint": {"drill": 1.0},
            "discoverable": False,
        },
    }


def _seed(monkeypatch):
    db = install_fake_db(monkeypatch)
    db["users"].docs = _users()
    return db


def test_matches_requires_auth(client):
    assert client.get("/api/v1/matches").status_code == 401


def test_matches_recomputes_and_ranks_best_candidate_first(client, monkeypatch):
    _seed(monkeypatch)

    res = client.get("/api/v1/matches", headers=auth_headers("alice"))

    assert res.status_code == 200
    body = res.json()
    items = body["data"]["items"]
    assert [item["user_id"] for item in items][0] == "bob", "twin history ranks first"
    assert "carol" in [item["user_id"] for item in items]
    assert "dave" not in [item["user_id"] for item in items], "hidden users excluded"
    top = items[0]
    assert top["display_name"] == "Bob"
    assert top["headline"]["top_genre"] == "indie rock"
    assert set(top["score"]) == {"genre", "artist", "audio", "overall"}
    assert body["data"]["next_cursor"] is None
    assert body["request_id"]


def test_matches_pagination_cursor_walks_pages(client, monkeypatch):
    _seed(monkeypatch)

    first = client.get("/api/v1/matches?limit=1", headers=auth_headers("alice")).json()["data"]
    assert len(first["items"]) == 1
    assert first["next_cursor"] is not None

    second = client.get(
        f"/api/v1/matches?limit=1&cursor={first['next_cursor']}",
        headers=auth_headers("alice"),
    ).json()["data"]
    assert len(second["items"]) == 1
    assert second["items"][0]["user_id"] != first["items"][0]["user_id"]
    assert second["next_cursor"] is None


def test_matches_rejects_malformed_cursor(client, monkeypatch):
    _seed(monkeypatch)
    res = client.get("/api/v1/matches?cursor=abc", headers=auth_headers("alice"))
    assert res.status_code == 422
    assert res.json()["error"]["code"] == 422


def test_swipe_flow_reaches_mutual_match(client, monkeypatch):
    db = _seed(monkeypatch)

    first = client.post("/api/v1/matches/bob/accept", headers=auth_headers("alice")).json()["data"]
    assert first["action"] == "like"
    assert first["match_status"] == "liked"
    assert first["pair_id"] == pair_id("alice", "bob")

    second = client.post("/api/v1/matches/alice/accept", headers=auth_headers("bob")).json()["data"]
    assert second["match_status"] == "matched"

    match = db["matches"].docs[pair_id("alice", "bob")]
    assert match["status"] == "matched"
    assert match["user1_id"] == "alice" and match["user2_id"] == "bob"


def test_accepted_candidates_leave_the_ranked_list(client, monkeypatch):
    _seed(monkeypatch)
    client.post("/api/v1/matches/bob/accept", headers=auth_headers("alice"))

    items = client.get("/api/v1/matches", headers=auth_headers("alice")).json()["data"]["items"]
    assert "bob" not in [item["user_id"] for item in items]
    assert "carol" in [item["user_id"] for item in items]


def test_reject_records_pass_without_creating_match(client, monkeypatch):
    db = _seed(monkeypatch)
    res = client.post("/api/v1/matches/carol/reject", headers=auth_headers("alice"))
    body = res.json()["data"]
    assert body["action"] == "pass"
    assert body["match_status"] is None
    assert pair_id("alice", "carol") not in db["matches"].docs
    assert db["swipes"].docs["alice:carol"]["action"] == "pass"


def test_self_action_is_rejected(client, monkeypatch):
    _seed(monkeypatch)
    res = client.post("/api/v1/matches/alice/accept", headers=auth_headers("alice"))
    assert res.status_code == 422


def test_chat_starters_gate_on_mutual_match(client, monkeypatch):
    db = _seed(monkeypatch)
    key = pair_id("alice", "bob")

    before = client.get("/api/v1/matches/bob/chat-starters", headers=auth_headers("alice"))
    assert before.status_code == 404

    client.post("/api/v1/matches/bob/accept", headers=auth_headers("alice"))
    one_sided = client.get("/api/v1/matches/bob/chat-starters", headers=auth_headers("alice"))
    assert one_sided.status_code == 409

    client.post("/api/v1/matches/alice/accept", headers=auth_headers("bob"))
    starters = client.get("/api/v1/matches/bob/chat-starters", headers=auth_headers("alice"))
    assert starters.status_code == 200
    lines = starters.json()["data"]["starters"]
    assert len(lines) == 3
    assert any("Radiohead" in line or "Beach House" in line for line in lines)
    assert db["matches"].docs[key]["chat_starter"] == lines[0]


def test_unmatch_deletes_and_hides_candidate(client, monkeypatch):
    db = _seed(monkeypatch)
    key = pair_id("alice", "bob")
    client.post("/api/v1/matches/bob/accept", headers=auth_headers("alice"))
    client.post("/api/v1/matches/alice/accept", headers=auth_headers("bob"))

    res = client.request("DELETE", "/api/v1/matches/bob", headers=auth_headers("alice"))
    assert res.status_code == 200
    assert res.json()["data"]["unmatched"] is True
    assert key not in db["matches"].docs

    again = client.request("DELETE", "/api/v1/matches/bob", headers=auth_headers("alice"))
    assert again.status_code == 404

    items = client.get("/api/v1/matches", headers=auth_headers("alice")).json()["data"]["items"]
    assert "bob" not in [item["user_id"] for item in items]


def test_blend_requires_mutual_match_and_history(client, monkeypatch):
    _seed(monkeypatch)
    token = auth_headers("alice")

    missing_body = client.post("/api/v1/matches/bob/blend", headers=token, json={})
    assert missing_body.status_code == 422  # body validated (missing access_token)

    client.post("/api/v1/matches/bob/accept", headers=token)
    one_sided = client.post("/api/v1/matches/bob/blend", headers=token, json={"access_token": "x"})
    assert one_sided.status_code == 409

    client.post("/api/v1/matches/alice/accept", headers=auth_headers("bob"))
    matched = client.post("/api/v1/matches/bob/blend", headers=token, json={"access_token": "x"})
    assert matched.status_code == 409, "no synced top tracks yet -> refuse, not crash"


def test_blend_creates_playlist_via_spotify(client, monkeypatch):
    db = _seed(monkeypatch)
    db["users"].docs["alice"]["top_tracks"] = ["t1", "t2", "t3"]
    db["users"].docs["bob"]["top_tracks"] = ["t3", "t2", "t1"]
    token = auth_headers("alice")
    client.post("/api/v1/matches/bob/accept", headers=token)
    client.post("/api/v1/matches/alice/accept", headers=auth_headers("bob"))

    created: dict = {}

    async def fake_create(access_token, name, description=""):
        created["name"] = name
        return {"id": "playlist-9", "external_urls": {"spotify": "https://open/x"}}

    async def fake_add(access_token, playlist_id, uris):
        created["playlist_id"] = playlist_id
        created["uris"] = uris

    from app.api.v1 import matches as matches_router

    monkeypatch.setattr(matches_router, "create_playlist", fake_create)
    monkeypatch.setattr(matches_router, "add_playlist_tracks", fake_add)

    res = client.post(
        "/api/v1/matches/bob/blend", headers=token, json={"access_token": "spot-token"}
    )

    assert res.status_code == 200, res.text
    data = res.json()["data"]
    assert data["playlist_id"] == "playlist-9"
    assert data["track_count"] == 3
    assert created["uris"][0].startswith("spotify:track:")
    key = pair_id("alice", "bob")
    assert db["matches"].docs[key]["blend_playlist_id"] == "playlist-9"
    assert "spot-token" not in str(res.json()), "tokens must never be echoed back"
