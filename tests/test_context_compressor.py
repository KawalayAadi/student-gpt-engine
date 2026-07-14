# tests/test_context_compressor.py
import pytest
from app.services import context_compressor
from app.services.context_compressor import get_summarize_prompt
from app.config import settings


def test_word_limit_scales_with_older_message_count():
    # 50 + (message_count * 10), uncapped case
    assert "110 words" in get_summarize_prompt(6)


def test_word_limit_caps_at_500():
    assert "500 words" in get_summarize_prompt(100)


async def test_no_compression_needed_when_under_recent_turn_limit():
    # fewer messages than context_recent_turns -> nothing to compress, returned as-is
    messages = [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
    ]
    result = await context_compressor.compress_history(messages)
    assert result == messages


async def test_older_history_gets_summarized(monkeypatch):
    messages = [{"role": "user", "content": f"msg{i}"} for i in range(10)]

    async def fake_chat(msgs):
        return {"choices": [{"message": {"content": "SUMMARY TEXT"}}]}

    monkeypatch.setattr(context_compressor.llm_client, "chat", fake_chat)

    result = await context_compressor.compress_history(messages)

    assert result[0]["role"] == "system"
    assert "SUMMARY TEXT" in result[0]["content"]
    # recent turns must be preserved verbatim, unchanged, in order
    assert result[1:] == messages[-settings.context_recent_turns:]


async def test_summarize_prompt_passed_to_llm(monkeypatch):
    captured = {}

    async def fake_chat(msgs):
        captured["system_prompt"] = msgs[0]["content"]
        captured["user_content"] = msgs[1]["content"]
        return {"choices": [{"message": {"content": "SUMMARY"}}]}

    monkeypatch.setattr(context_compressor.llm_client, "chat", fake_chat)

    messages = [{"role": "user", "content": f"msg{i}"} for i in range(8)]
    await context_compressor.compress_history(messages)

    assert "Summarize" in captured["system_prompt"]
    # the older messages (everything except the last context_recent_turns) should be in the prompt
    assert "msg0" in captured["user_content"]
    assert f"msg{7 - settings.context_recent_turns}" in captured["user_content"]