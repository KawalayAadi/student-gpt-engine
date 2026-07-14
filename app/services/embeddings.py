# app/services/embeddings.py
import httpx
from app.config import settings

_client = httpx.AsyncClient(
    base_url=settings.llm_base_url,   # same provider as the chat model, unless you point this elsewhere
    headers={"Authorization": f"Bearer {settings.llm_api_key}"},
    timeout=30.0,
)


async def embed_text(text: str) -> list[float]:
    """
    Returns a single embedding vector for the given text.
    Assumes an OpenAI-compatible POST /embeddings endpoint. If your embedding
    model is hosted separately from the chat model (e.g. self-hosted bge/e5),
    swap `settings.llm_base_url` / `settings.llm_api_key` here for dedicated
    embedding-service settings instead.
    """
    payload = {
        "model": settings.embedding_model,
        "input": text,
    }
    resp = await _client.post("embeddings", json=payload)
    resp.raise_for_status()
    data = resp.json()
    return data["data"][0]["embedding"]


async def embed_batch(texts: list[str]) -> list[list[float]]:
    """Batch version — use this when embedding multiple items at once (cheaper, fewer round trips)."""
    payload = {
        "model": settings.embedding_model,
        "input": texts,
    }
    resp = await _client.post("embeddings", json=payload)
    resp.raise_for_status()
    data = resp.json()
    return [item["embedding"] for item in sorted(data["data"], key=lambda x: x["index"])]