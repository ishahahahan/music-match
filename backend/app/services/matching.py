"""Match discovery (roadmap Phase 4).

v1: nightly pairwise batch over all users (fine to ~10k), scores persisted as
compatibility documents keyed by ordered pair id (min-max), so each pair exists once.
v2: profile embeddings + Atlas Vector Search when O(n²) grows.
"""


def pair_id(user_a: str, user_b: str) -> str:
    """Deterministic ordered pair key so (x,y) and (y,x) are one document."""
    low, high = sorted((user_a, user_b))
    return f"{low}:{high}"


async def recompute_for_user(spotify_id: str) -> int:
    """Recompute and persist scores for one user's candidates; returns count written."""
    raise NotImplementedError("Phase 4: batch score job")
