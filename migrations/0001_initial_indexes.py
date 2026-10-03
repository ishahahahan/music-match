"""Create the indexes the app relies on. Run: python migrations/0001_initial_indexes.py"""

import os
import sys

from pymongo import MongoClient


def main() -> int:
    uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    db = MongoClient(uri)[os.getenv("MONGODB_DB", "musicmatch")]
    db["compatibility_scores"].create_index([("overall", -1)])
    db["compatibility_scores"].create_index([("user1_id", 1), ("user2_id", 1)])
    db["swipes"].create_index([("user_id", 1), ("target_id", 1)], unique=True)
    db["sync_jobs"].create_index([("user_id", 1), ("started_at", -1)])
    db["users"].create_index([("discoverable", 1)])
    print("indexes ready:", sorted(db.list_collection_names()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
