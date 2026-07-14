# app/utils/db.py
import asyncpg
from pgvector.asyncpg import register_vector
from app.config import settings

_pool: asyncpg.Pool | None = None


async def _init_connection(conn: asyncpg.Connection):
    # makes asyncpg understand the `vector` column type so we can pass
    # plain python lists/np arrays straight into queries as VECTOR(...)
    await register_vector(conn)


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            dsn=settings.database_url,
            min_size=2,
            max_size=10,
            init=_init_connection,
        )
    return _pool


async def close_pool():
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


async def check_connection() -> bool:
    """Used by the /health endpoint to report real DB status instead of always 'ok'."""
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return True
    except Exception:
        return False