# app/services/telemetry.py
import structlog
import time
from app.utils.db import get_pool

logger = structlog.get_logger()

async def log_request(*, conversation_id, route, cache_hit, ttft_ms,
                       total_latency_ms, input_tokens, output_tokens, error=None):
    logger.info(
        "request_complete",
        conversation_id=str(conversation_id),
        route=route,
        cache_hit=cache_hit,
        ttft_ms=ttft_ms,
        total_latency_ms=total_latency_ms,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        error=error,
    )
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO request_logs
            (conversation_id, route, cache_hit, ttft_ms, total_latency_ms,
             input_tokens, output_tokens, error)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
            """,
            conversation_id, route, cache_hit, ttft_ms, total_latency_ms,
            input_tokens, output_tokens, error,
        )