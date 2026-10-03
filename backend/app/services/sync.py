"""Background sync jobs (roadmap Phase 2).

Runs as an asyncio task behind POST /sync/start; writes real progress into the
sync_jobs collection — timestamps and counts come from the job document,
never datetime.now() fabricated at the edge.
"""


async def run_user_sync(spotify_id: str) -> None:
    """Paginate Spotify, bulkWrite upserts, extract genres, update the job doc."""
    raise NotImplementedError("Phase 2: paginated ingestion with backoff")
