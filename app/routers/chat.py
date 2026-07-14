# app/routers/chat.py
import time, uuid
from fastapi import APIRouter, UploadFile, File, Form
from app.services import (
    image_preproc, semantic_router, semantic_cache,
    context_compressor, latex_postprocess, telemetry,
)
from app.services.llm_client import llm_client, extract_final_answer
from app.services.embeddings import embed_text
from app.templates.micro_templates import build_system_prompt

router = APIRouter()

@router.post("/v1/chat")
async def chat(
    conversation_id: str = Form(...),
    message: str = Form(...),
    history: str = Form("[]"),          # JSON-encoded prior messages
    image: UploadFile | None = File(None),
):
    start = time.time()
    error = None
    cache_hit = False

    ocr_text = None
    if image is not None:
        result = image_preproc.preprocess_image(await image.read())
        ocr_text = result["ocr_text"]

    full_query = message if not ocr_text else f"{message}\n[OCR extracted text]: {ocr_text}"

    mode = semantic_router.classify(full_query)
    embedding = await embed_text(full_query)

    cached = await semantic_cache.get_cached_response(embedding, mode.value)
    if cached:
        cache_hit = True
        response_text = cached
    else:
        import json
        messages = json.loads(history)
        messages = await context_compressor.compress_history(messages)

        system_prompt = build_system_prompt(mode.value)
        messages = [{"role": "system", "content": system_prompt}] + messages
        messages.append({"role": "user", "content": full_query})

        result = await llm_client.chat(messages)
        raw = result["choices"][0]["message"]["content"]
        response_text = extract_final_answer(raw)
        await semantic_cache.store_response(full_query, embedding, response_text, mode.value)

    latex_result = latex_postprocess.validate_and_wrap_latex(response_text)

    await telemetry.log_request(
        conversation_id=conversation_id,
        route=mode.value,
        cache_hit=cache_hit,
        ttft_ms=None,  # populate properly once streaming is wired in
        total_latency_ms=int((time.time() - start) * 1000),
        input_tokens=None,   # populate from provider response if available
        output_tokens=None,
        error=error,
    )

    return {
        "conversation_id": conversation_id,
        "mode": mode.value,
        "cache_hit": cache_hit,
        **latex_result,
    }