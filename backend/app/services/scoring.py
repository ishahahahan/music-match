"""Compatibility scoring computed in application code — no SQL RPCs (roadmap Phase 3).

The legacy SQL path capped the overall score at 0.40 (artist/audio hardcoded to 0.0).
These functions implement all three components so the honest range is [0, 1].
"""

from math import sqrt

WEIGHTS = {"genre": 0.4, "artist": 0.3, "audio": 0.3}


def weighted_jaccard(weights_a: dict[str, float], weights_b: dict[str, float]) -> float:
    """Weighted Jaccard over rank-weighted sets: sum(min) / sum(max)."""
    keys = set(weights_a) | set(weights_b)
    if not keys:
        return 0.0
    numerator = sum(min(weights_a.get(k, 0.0), weights_b.get(k, 0.0)) for k in keys)
    denominator = sum(max(weights_a.get(k, 0.0), weights_b.get(k, 0.0)) for k in keys)
    return numerator / denominator if denominator else 0.0


def cosine_similarity(vector_a: list[float], vector_b: list[float]) -> float:
    """Cosine similarity of two normalized audio-feature centroids."""
    if not vector_a or len(vector_a) != len(vector_b):
        return 0.0
    dot = sum(a * b for a, b in zip(vector_a, vector_b))
    norm_a = sqrt(sum(a * a for a in vector_a))
    norm_b = sqrt(sum(b * b for b in vector_b))
    if not norm_a or not norm_b:
        return 0.0
    return dot / (norm_a * norm_b)


def compatibility_score(genre: float, artist: float, audio: float) -> dict[str, float]:
    """Overall = 0.4*genre + 0.3*artist + 0.3*audio, persisted with its breakdown."""
    clamped = {
        k: min(max(v, 0.0), 1.0)
        for k, v in {"genre": genre, "artist": artist, "audio": audio}.items()
    }
    overall = (
        WEIGHTS["genre"] * clamped["genre"]
        + WEIGHTS["artist"] * clamped["artist"]
        + WEIGHTS["audio"] * clamped["audio"]
    )
    return {**clamped, "overall": round(overall, 4)}
