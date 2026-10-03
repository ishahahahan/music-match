"""MongoDB connection — the ONLY module that imports motor (vendor swap point).

Everything else goes through repository functions, so moving to Firestore or
another store later touches this package only (roadmap: NoSQL data decision).
"""

from functools import lru_cache

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import settings


@lru_cache
def get_client() -> AsyncIOMotorClient:
    return AsyncIOMotorClient(settings.mongodb_uri)


def get_db() -> AsyncIOMotorDatabase:
    return get_client()[settings.mongodb_db]


def close_client() -> None:
    get_client().close()
