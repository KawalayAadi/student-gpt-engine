# app/services/semantic_cache.py
import numpy as np
from app.utils.db import get_pool
from app.config import settings

async def get_cached_response(embedding: list[float], mode: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, response_text, 1 - (query_embedding <=> $1::vector) AS similarity
            FROM semantic_cache
            WHERE mode = $2 AND invalidated = FALSE
            ORDER BY query_embedding <=> $1::vector
            LIMIT 1
            """,
            embedding, mode,
        )
        if row and row["similarity"] >= settings.cache_similarity_threshold:
            await conn.execute(
                "UPDATE semantic_cache SET hit_count = hit_count + 1, last_used_at = now() WHERE id = $1",
                row["id"],
            )
            return row["response_text"]
        return None

async def store_response(query_text: str, embedding: list[float], response_text: str, mode: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO semantic_cache (query_text, query_embedding, response_text, mode)
            VALUES ($1, $2::vector, $3, $4)
            """,
            query_text, embedding, response_text, mode,
        )

async def invalidate(cache_id: str):
    """Call this from a feedback/thumbs-down endpoint to stop a wrong answer from being served again."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Here is the ::uuid fix in the correct function!
        await conn.execute("UPDATE semantic_cache SET invalidated = TRUE WHERE id = $1::uuid", cache_id)