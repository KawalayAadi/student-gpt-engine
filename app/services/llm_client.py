# app/services/llm_client.py
import httpx
from app.config import settings

class LLMClient:
    def __init__(self):
        self.client = httpx.AsyncClient(
            base_url=settings.llm_base_url,
            headers={"Authorization": f"Bearer {settings.llm_api_key}"},
            timeout=60.0,
        )

    async def chat(self, messages: list[dict], stream: bool = False):
        payload = {
            "model": settings.llm_model,
            "messages": messages,
            "stream": stream,
        }
        resp = await self.client.post("chat/completions", json=payload)
        resp.raise_for_status()
        return resp.json()

llm_client = LLMClient()

# might need to change
def extract_final_answer(raw_content: str) -> str:
    if "<think>" in raw_content and "</think>" in raw_content:
        return raw_content.split("</think>", 1)[1].strip()
    return raw_content.strip()