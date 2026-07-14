# tests/test_cache.py
import pytest
from app.services import semantic_cache


class FakeConn:
    """Stands in for an asyncpg connection. Records every execute() call
    so tests can assert on the SQL that would have run."""

    def __init__(self, fetchrow_result=None):
        self._fetchrow_result = fetchrow_result
        self.executed = []

    async def fetchrow(self, query, *args):
        return self._fetchrow_result

    async def execute(self, query, *args):
        self.executed.append((query, args))


class FakeAcquireCtx:
    def __init__(self, conn):
        self.conn = conn

    async def __aenter__(self):
        return self.conn

    async def __aexit__(self, *exc):
        return False


class FakePool:
    def __init__(self, conn):
        self.conn = conn

    def acquire(self):
        return FakeAcquireCtx(self.conn)


def _patch_pool(monkeypatch, conn: FakeConn):
    pool = FakePool(conn)

    async def fake_get_pool():
        return pool

    monkeypatch.setattr(semantic_cache, "get_pool", fake_get_pool)
    return pool


async def test_cache_hit_above_threshold(monkeypatch):
    # default threshold is 0.95 (see app/config.py) — 0.97 should hit
    fake_row = {"id": "abc-123", "response_text": "The answer is 42", "similarity": 0.97}
    conn = FakeConn(fetchrow_result=fake_row)
    _patch_pool(monkeypatch, conn)

    result = await semantic_cache.get_cached_response([0.1] * 1536, "qa")

    assert result == "The answer is 42"
    # hit_count update should have fired
    assert any("hit_count" in q for q, _ in conn.executed)


async def test_cache_miss_below_threshold(monkeypatch):
    # 0.80 similarity is below the 0.95 threshold — must NOT be treated as a hit
    fake_row = {"id": "abc-123", "response_text": "The answer is 42", "similarity": 0.80}
    conn = FakeConn(fetchrow_result=fake_row)
    _patch_pool(monkeypatch, conn)

    result = await semantic_cache.get_cached_response([0.1] * 1536, "qa")

    assert result is None
    assert conn.executed == []  # no hit_count update should fire on a miss


async def test_cache_miss_no_rows(monkeypatch):
    conn = FakeConn(fetchrow_result=None)
    _patch_pool(monkeypatch, conn)

    result = await semantic_cache.get_cached_response([0.1] * 1536, "qa")

    assert result is None


async def test_store_response_inserts(monkeypatch):
    conn = FakeConn()
    _patch_pool(monkeypatch, conn)

    await semantic_cache.store_response("query text", [0.1] * 1536, "response text", "qa")

    assert len(conn.executed) == 1
    query, args = conn.executed[0]
    assert "INSERT INTO semantic_cache" in query
    assert args[0] == "query text"
    assert args[2] == "response text"
    assert args[3] == "qa"


async def test_invalidate_sets_flag(monkeypatch):
    conn = FakeConn()
    _patch_pool(monkeypatch, conn)

    await semantic_cache.invalidate("abc-123")

    query, args = conn.executed[0]
    assert "invalidated = TRUE" in query
    assert args[0] == "abc-123"