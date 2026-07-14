# app/services/context_compressor.py
from app.services.llm_client import llm_client
from app.config import settings

def get_summarize_prompt(message_count: int) -> str:
    word_limit = min(500, 50 + (message_count * 10))
    
    return (
        f"Summarize the following conversation history in under {word_limit} words, "
        "preserving the student's topic, unresolved questions, and any facts "
        "the assistant has already stated. Do not add new information."
    )

async def compress_history(messages: list[dict]) -> list[dict]:
    recent = messages[-settings.context_recent_turns:]
    older = messages[:-settings.context_recent_turns]
    
    if not older:
        return recent

    older_text = "\n".join(f"{m['role']}: {m['content']}" for m in older)
    
    dynamic_prompt = get_summarize_prompt(len(older))
    
    result = await llm_client.chat([
        {"role": "system", "content": dynamic_prompt},
        {"role": "user", "content": older_text},
    ])
    
    summary = result["choices"][0]["message"]["content"]
    return [{"role": "system", "content": f"[Earlier conversation summary]: {summary}"}] + recent