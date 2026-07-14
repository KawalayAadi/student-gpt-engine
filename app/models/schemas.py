# app/models/schemas.py
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class HistoryMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatRequest(BaseModel):
    """
    Mirrors the multipart form fields accepted by POST /v1/chat.
    Used for validating the JSON-encoded `history` field before it's
    parsed in the router, and for generating accurate API docs.
    """
    conversation_id: str
    message: str
    history: list[HistoryMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    conversation_id: str
    mode: Literal["qa", "flashcards", "pop_quiz", "short_notes"]
    cache_hit: bool
    text: str
    latex_blocks: list[str] = Field(default_factory=list)
    latex_inline: list[str] = Field(default_factory=list)
    balanced: bool


class CacheEntry(BaseModel):
    id: str
    query_text: str
    response_text: str
    mode: str
    hit_count: int
    invalidated: bool
    created_at: datetime
    last_used_at: datetime


class InvalidateCacheRequest(BaseModel):
    """Payload for a thumbs-down / feedback endpoint that flags a bad cached answer."""
    cache_id: str
    reason: Optional[str] = None


class RequestLog(BaseModel):
    conversation_id: str
    route: str
    cache_hit: bool
    ttft_ms: Optional[int] = None
    total_latency_ms: int
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded", "down"]
    db_connected: bool = True
    llm_reachable: bool = True