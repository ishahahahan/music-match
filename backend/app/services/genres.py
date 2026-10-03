"""Genre extraction — port of legacy/lastfm.py GenreExtractor (roadmap Phase 2.7).

Known fix vs legacy: the old regex blocklist killed valid genres ("dancehall",
"big band" matched .*dance.* / .*live.*). Anchor patterns to word boundaries.
"""

import re

_NON_ALNUM = re.compile(r"[^a-z0-9 ]+")
_WS = re.compile(r"\s+")


def normalize_genre(raw: str) -> str:
    """Normalize a raw tag to a canonical genre key ("Indie  Rock" -> "indie rock")."""
    cleaned = _NON_ALNUM.sub(" ", raw.strip().lower())
    return _WS.sub(" ", cleaned).strip()


def extract_genres(tags: list[str], limit: int = 10) -> list[str]:
    """Deduplicate + normalize tags, preserving order (full 5-stage pipeline: TODO port)."""
    seen: dict[str, None] = {}
    for tag in tags:
        key = normalize_genre(tag)
        if key:
            seen.setdefault(key)
    return list(seen)[:limit]
