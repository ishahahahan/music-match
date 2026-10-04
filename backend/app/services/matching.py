"""Match discovery (roadmap Phase 4).

v1: pairwise batch over all discoverable users (fine to ~10k), scores persisted as
compatibility documents keyed by ordered pair id (min-max), so each pair exists once.
v2: profile embeddings + Atlas Vector Search when O(n²) grows.

All scoring math is pure (`score_pair`, `chat_starters`, `blend_track_order`) so
tests can drive fixtures without a DB.
"""

from app.repositories.scores import save_score
from app.repositories.users import get_user, list_users
from app.services.scoring import compatibility_score, cosine_similarity, weighted_jaccard

# Fixed per-feature ranges used to min-max normalize audio centroids into [0, 1]
# before cosine (roadmap Phase 3: z-score across population OR min-max).
AUDIO_RANGES: dict[str, tuple[float, float]] = {
    "danceability": (0.0, 1.0),
    "energy": (0.0, 1.0),
    "valence": (0.0, 1.0),
    "acousticness": (0.0, 1.0),
    "instrumentalness": (0.0, 1.0),
    "liveness": (0.0, 1.0),
    "speechiness": (0.0, 1.0),
    "tempo": (40.0, 220.0),
    "duration_ms": (0.0, 600_000.0),
}


def pair_id(user_a: str, user_b: str) -> str:
    """Deterministic ordered pair key so (x,y) and (y,x) are one document."""
    low, high = sorted((user_a, user_b))
    return f"{low}:{high}"


def rank_weights(names: list[str]) -> dict[str, float]:
    """Rank-decay weights w=(N-p)/N over a top-N list (earliest rank wins ties)."""
    unique: dict[str, float] = {}
    total = len(names)
    if not total:
        return unique
    for position, name in enumerate(names):
        unique.setdefault(name, (total - position) / total)
    return unique


def audio_vector(user: dict) -> list[float]:
    """Min-max normalized audio centroid; empty when no fingerprint was synced."""
    fingerprint = user.get("audio_fingerprint") or {}
    if not fingerprint:
        return []
    vector = []
    for feature, (low, high) in AUDIO_RANGES.items():
        raw = fingerprint.get(feature)
        if not isinstance(raw, (int, float)):
            continue
        vector.append(min(max((float(raw) - low) / (high - low), 0.0), 1.0))
    return vector


def score_pair(user_a: dict, user_b: dict) -> dict[str, float]:
    """All three components — genre 0.4 / artist 0.3 / audio 0.3, honest in [0, 1]."""
    genre = weighted_jaccard(
        user_a.get("genre_fingerprint") or {}, user_b.get("genre_fingerprint") or {}
    )
    artist = weighted_jaccard(
        rank_weights(user_a.get("top_artists") or []),
        rank_weights(user_b.get("top_artists") or []),
    )
    audio = cosine_similarity(audio_vector(user_a), audio_vector(user_b))
    return compatibility_score(genre, artist, audio)


async def recompute_for_user(spotify_id: str) -> int:
    """Recompute and persist scores for one user's candidates; returns count written."""
    me = await get_user(spotify_id)
    if me is None:
        return 0
    written = 0
    for other in await list_users(exclude=spotify_id):
        other_id = str(other.get("_id", ""))
        if not other_id:
            continue
        components = score_pair(me, other)
        low, high = sorted((spotify_id, other_id))
        await save_score(f"{low}:{high}", low, high, components)
        written += 1
    return written


def _shared(values_a: list[str], values_b: list[str], limit: int = 3) -> list[str]:
    present_b = set(values_b)
    seen: dict[str, None] = {}
    for value in values_a:
        if value in present_b:
            seen.setdefault(value)
        if len(seen) >= limit:
            break
    return list(seen)


def chat_starters(user_a: dict, user_b: dict, limit: int = 3) -> list[str]:
    """Deterministic prompts from genuinely shared taste (no randomness, testable)."""
    starters: list[str] = []
    shared_artists = _shared(user_a.get("top_artists") or [], user_b.get("top_artists") or [])
    if shared_artists:
        starters.append(f"You both had {shared_artists[0]} in heavy rotation — favorite track?")
    shared_genres = _shared(user_a.get("top_genres") or [], user_b.get("top_genres") or [])
    if shared_genres:
        starters.append(f"Your feeds both lean {shared_genres[0]} — what pulled you in first?")
    fingerprint_a = user_a.get("audio_fingerprint") or {}
    fingerprint_b = user_b.get("audio_fingerprint") or {}
    energy_a = fingerprint_a.get("energy")
    energy_b = fingerprint_b.get("energy")
    if isinstance(energy_a, (int, float)) and isinstance(energy_b, (int, float)):
        energy = (float(energy_a) + float(energy_b)) / 2
        mood = "high-energy" if energy >= 0.6 else "mellow" if energy < 0.4 else "balanced"
        starters.append(f"You both run {mood} — what's your ideal listening setting?")
    while len(starters) < limit:
        fallbacks = [
            "What's the first song you'd put on a road-trip playlist?",
            "Which concert would you travel to see?",
            "What's an album you'd defend to anyone?",
        ]
        starters.append(fallbacks[len(starters) % len(fallbacks)])
    return starters[:limit]


def blend_track_order(tracks_a: list[str], tracks_b: list[str], cap: int = 100) -> list[str]:
    """Union of both users' top tracks ranked by rank-sum; shared tracks float up."""
    if cap <= 0:
        return []
    rank_a: dict[str, int] = {}
    rank_b: dict[str, int] = {}
    for position, track in enumerate(tracks_a):
        rank_a.setdefault(track, position)
    for position, track in enumerate(tracks_b):
        rank_b.setdefault(track, position)
    missing = max(len(tracks_a), len(tracks_b), 1)
    union = set(rank_a) | set(rank_b)
    ranked = sorted(
        union,
        key=lambda track: (
            rank_a.get(track, missing) + rank_b.get(track, missing),
            track,
        ),
    )
    return ranked[:cap]
