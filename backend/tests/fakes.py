"""Deterministic in-memory stand-ins for the Mongo collections (roadmap Phase 8).

Implements exactly the motor/pymongo subset the repositories use, so API tests
exercise the real router -> service -> repository stack with zero network.
"""

import copy
from types import SimpleNamespace

import jwt

from app.config import settings
from app.repositories import jobs, matches, scores, tracks, users


def _matches_conditions(doc: dict, conditions: dict) -> bool:
    for key, expected in conditions.items():
        if key == "$or":
            if not any(_matches_conditions(doc, branch) for branch in expected):
                return False
        elif key == "$and":
            if not all(_matches_conditions(doc, branch) for branch in expected):
                return False
        elif (
            isinstance(expected, dict)
            and expected
            and all(str(operator).startswith("$") for operator in expected)
        ):
            actual = doc.get(key)
            for operator, value in expected.items():
                if operator == "$ne":
                    if actual == value:
                        return False
                elif operator == "$in":
                    if actual not in value:
                        return False
                elif operator == "$gte":
                    if actual is None or actual < value:
                        return False
                elif operator == "$lte":
                    if actual is None or actual > value:
                        return False
                else:
                    raise NotImplementedError(f"fake mongo: unsupported operator {operator}")
        elif doc.get(key) != expected:
            return False
    return True


class FakeCursor:
    def __init__(self, docs: list[dict]):
        self._docs = docs

    def sort(self, key, direction: int = 1):  # noqa: A002 - pymongo-compatible signature
        pairs = key if isinstance(key, list) else [(key, direction)]
        for field, order in reversed(pairs):
            self._docs.sort(key=lambda doc, f=field: doc.get(f), reverse=order < 0)
        return self

    def skip(self, count: int) -> "FakeCursor":
        self._docs = self._docs[count:]
        return self

    def limit(self, count: int) -> "FakeCursor":
        self._docs = self._docs[:count]
        return self

    async def to_list(self, length: int | None = None) -> list[dict]:
        docs = self._docs if length is None else self._docs[:length]
        return copy.deepcopy(docs)


class FakeCollection:
    def __init__(self) -> None:
        self.docs: dict = {}

    def _find(self, conditions: dict) -> list[dict]:
        return [doc for doc in self.docs.values() if _matches_conditions(doc, conditions)]

    async def insert_one(self, doc: dict):
        _id = doc.get("_id")
        if _id in self.docs:
            raise RuntimeError(f"fake mongo: duplicate key {_id!r}")
        self.docs[_id] = copy.deepcopy(doc)
        return SimpleNamespace(inserted_id=_id)

    async def replace_one(self, conditions: dict, doc: dict, upsert: bool = False):
        found = self._find(conditions)
        if found:
            self.docs[found[0]["_id"]] = copy.deepcopy(doc)
            return SimpleNamespace(matched_count=1, modified_count=1)
        if upsert:
            self.docs[doc["_id"]] = copy.deepcopy(doc)
            return SimpleNamespace(upserted_id=doc["_id"])
        return SimpleNamespace(matched_count=0, modified_count=0)

    @staticmethod
    def _apply_update(target: dict, update: dict, insert: bool) -> None:
        for field, value in (update.get("$set") or {}).items():
            target[field] = copy.deepcopy(value)
        if insert:
            for field, value in (update.get("$setOnInsert") or {}).items():
                target.setdefault(field, copy.deepcopy(value))
        unknown = set(update) - {"$set", "$setOnInsert"}
        if unknown:
            raise NotImplementedError(f"fake mongo: unsupported update operators {unknown}")

    async def update_one(self, conditions: dict, update: dict, upsert: bool = False):
        found = self._find(conditions)
        if found:
            self._apply_update(found[0], update, insert=False)
            return SimpleNamespace(matched_count=1, modified_count=1)
        if not upsert:
            return SimpleNamespace(matched_count=0, modified_count=0)
        if not all(isinstance(key, str) and not key.startswith("$") for key in conditions):
            raise NotImplementedError("fake mongo: upsert filters must be plain equality")
        seed = copy.deepcopy(conditions)
        self._apply_update(seed, update, insert=True)
        if "_id" not in seed:
            raise RuntimeError("fake mongo: upserted document is missing _id")
        self.docs[seed["_id"]] = seed
        return SimpleNamespace(upserted_id=seed["_id"])

    async def find_one(self, conditions: dict, sort=None) -> dict | None:
        found = self._find(conditions)
        if not found:
            return None
        cursor = FakeCursor(found)
        if sort is not None:
            cursor.sort(sort)
        return copy.deepcopy(cursor._docs[0])

    def find(self, conditions: dict) -> FakeCursor:
        return FakeCursor(copy.deepcopy(self._find(conditions)))

    async def count_documents(self, conditions: dict) -> int:
        return len(self._find(conditions))

    async def delete_many(self, conditions: dict):
        doomed = self._find(conditions)
        for doc in doomed:
            del self.docs[doc["_id"]]
        return SimpleNamespace(deleted_count=len(doomed))

    async def delete_one(self, conditions: dict):
        found = self._find(conditions)
        if not found:
            return SimpleNamespace(deleted_count=0)
        del self.docs[found[0]["_id"]]
        return SimpleNamespace(deleted_count=1)

    async def bulk_write(self, operations: list, ordered: bool = True):
        upserted = modified = 0
        for operation in operations:
            try:
                conditions = operation._filter
                update = operation._doc
                upsert = operation._upsert
            except AttributeError as exc:  # pragma: no cover - defensive
                raise RuntimeError("fake mongo: unsupported bulk operation") from exc
            result = await self.update_one(conditions, update, upsert=upsert)
            upserted += getattr(result, "upserted_id", None) is not None
            modified += getattr(result, "modified_count", 0)
        return SimpleNamespace(upserted_count=upserted, modified_count=modified)


class FakeDB:
    def __init__(self) -> None:
        self.collections: dict[str, FakeCollection] = {}

    def __getitem__(self, name: str) -> FakeCollection:
        return self.collections.setdefault(name, FakeCollection())


def install_fake_db(monkeypatch, db: FakeDB | None = None) -> FakeDB:
    """Point every repository module at one in-memory database."""
    fake = db or FakeDB()
    for module in (users, jobs, tracks, scores, matches):
        monkeypatch.setattr(module, "get_db", lambda fake=fake: fake)
    return fake


def auth_headers(user_id: str) -> dict[str, str]:
    """Mint a valid first-party token exactly the way Phase 1 issuance will."""
    token = jwt.encode({"sub": user_id}, settings.jwt_secret, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}
