"""Phase 3/4 scoring math — identical/disjoint fixtures prove the 0.40 cap is gone."""

from tests.fakes import install_fake_db
from app.services.matching import (
    audio_vector,
    blend_track_order,
    chat_starters,
    rank_weights,
    recompute_for_user,
    score_pair,
)


def user(**overrides) -> dict:
    base = {
        "_id": "u",
        "top_artists": ["Radiohead", "Beach House", "Tycho"],
        "top_genres": ["indie rock", "dream pop"],
        "genre_fingerprint": {"indie rock": 2.0, "dream pop": 1.0, "synthwave": 0.4},
        "audio_fingerprint": {
            "energy": 0.7,
            "valence": 0.6,
            "danceability": 0.55,
            "acousticness": 0.2,
            "instrumentalness": 0.1,
            "liveness": 0.12,
            "speechiness": 0.04,
            "tempo": 120.0,
            "duration_ms": 240_000.0,
        },
        "discoverable": True,
    }
    base.update(overrides)
    return base


def test_identical_histories_score_at_least_095():
    twin_a, twin_b = user(_id="a"), user(_id="b")
    components = score_pair(twin_a, twin_b)
    assert components["genre"] == 1.0
    assert components["artist"] == 1.0
    assert components["audio"] == 1.0
    assert components["overall"] >= 0.95


def test_disjoint_histories_score_at_most_01():
    a = user(
        _id="a",
        top_artists=["Radiohead"],
        top_genres=["indie rock"],
        genre_fingerprint={"indie rock": 1.0},
    )
    b = user(
        _id="b",
        top_artists=["Burna Boy"],
        top_genres=["afrobeats"],
        genre_fingerprint={"afrobeats": 1.0},
        audio_fingerprint={"energy": 0.9, "valence": 0.9, "tempo": 105.0},
    )
    components = score_pair(a, b)
    assert components["overall"] <= 0.1


def test_artist_and_audio_lift_score_past_legacy_cap():
    genre_only = user(
        _id="a",
        top_artists=["OnlyA"],
        genre_fingerprint={"x": 1.0},
        audio_fingerprint={},
    )
    other = user(
        _id="b",
        top_artists=["OnlyB"],
        genre_fingerprint={"x": 1.0},
        audio_fingerprint={},
    )
    capped = score_pair(genre_only, other)
    # genre perfect, artist disjoint, no audio data -> honest result under 0.40+...
    assert capped["artist"] == 0.0
    assert capped["audio"] == 0.0

    full = score_pair(user(_id="a"), user(_id="b"))
    assert full["overall"] > 0.4, "artist/audio components must lift the score"


def test_audio_vector_empty_without_fingerprint_and_clamped_with():
    assert audio_vector(user(audio_fingerprint={})) == []
    vector = audio_vector(user(audio_fingerprint={"tempo": 5000.0, "energy": -3.0}))
    assert all(0.0 <= value <= 1.0 for value in vector)


def test_rank_weights_prefer_earlier_ranks():
    weights = rank_weights(["first", "second", "third"])
    assert weights["first"] > weights["second"] > weights["third"] > 0


def test_chat_starters_reference_genuinely_shared_taste():
    a = user(_id="a")
    b = user(_id="b", top_artists=["Beach House", "Radiohead", "Tycho"])
    starters = chat_starters(a, b)
    assert any("Beach House" in line or "Radiohead" in line for line in starters)
    assert chat_starters(a, b) == starters, "starters must be deterministic"
    assert len(starters) == 3


def test_blend_track_order_shared_tracks_float_up():
    mine = ["s1", "s2", "s3"]
    theirs = ["s3", "s2", "s1", "exclusive"]
    ordered = blend_track_order(mine, theirs, cap=3)
    assert set(ordered) == {"s1", "s2", "s3"}
    exclusive_ranked = blend_track_order(mine, theirs, cap=10)
    assert exclusive_ranked.index("s3") < exclusive_ranked.index("exclusive")
    assert len(blend_track_order(mine, theirs, cap=2)) == 2


def test_recompute_writes_one_score_per_discoverable_user(monkeypatch):
    db = install_fake_db(monkeypatch)
    db["users"].docs = {
        "alice": dict(user(_id="alice")),
        "bob": dict(user(_id="bob")),
        "carol": dict(user(_id="carol", discoverable=False)),
    }

    import asyncio

    written = asyncio.run(recompute_for_user("alice"))

    assert written == 1, "hidden users must not be scored; pairs are order-invariant"
    assert "alice:bob" in db["compatibility_scores"].docs
    score = db["compatibility_scores"].docs["alice:bob"]
    assert set(score["components"]) == {"genre", "artist", "audio", "overall"}
    assert score["overall"] == score["components"]["overall"]
