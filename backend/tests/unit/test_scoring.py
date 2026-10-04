"""All three score components — proves the legacy 0.40 cap is gone (roadmap Phase 3)."""

from app.services.matching import pair_id
from app.services.scoring import (
    compatibility_score,
    cosine_similarity,
    weighted_jaccard,
)


def test_identical_histories_score_high():
    weights = {"indie": 1.0, "rock": 0.6, "house": 0.3}
    assert weighted_jaccard(weights, dict(weights)) == 1.0
    score = compatibility_score(genre=1.0, artist=1.0, audio=1.0)
    assert score["overall"] >= 0.95


def test_disjoint_histories_score_low():
    a = {"indie": 1.0, "rock": 0.6}
    b = {"afrobeats": 1.0, "jazz": 0.5}
    assert weighted_jaccard(a, b) == 0.0
    score = compatibility_score(genre=0.0, artist=0.0, audio=0.0)
    assert score["overall"] <= 0.1


def test_genre_only_fixture_is_not_capped_at_040():
    genre_only = compatibility_score(genre=0.9, artist=0.0, audio=0.0)
    assert genre_only["overall"] == 0.36
    full = compatibility_score(genre=0.9, artist=0.5, audio=0.5)
    assert full["overall"] == 0.66, "artist/audio components must lift the score past 0.40"


def test_overall_is_bounded():
    score = compatibility_score(genre=3.0, artist=-1.0, audio=0.5)
    assert 0.0 <= score["overall"] <= 1.0


def test_cosine_similarity():
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0
    assert cosine_similarity([], [1.0]) == 0.0


def test_pair_id_is_order_invariant():
    assert pair_id("b", "a") == pair_id("a", "b")
