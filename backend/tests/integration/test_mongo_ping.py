"""Live MongoDB check — skipped unless MONGODB_URI is exported (opt-in, roadmap Phase 8)."""

import os

import pytest

pytestmark = pytest.mark.skipif(
    not os.getenv("MONGODB_URI"), reason="set MONGODB_URI to run integration tests"
)


@pytest.mark.integration
def test_database_ping():
    from pymongo import MongoClient

    client = MongoClient(os.environ["MONGODB_URI"], serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    client.close()
