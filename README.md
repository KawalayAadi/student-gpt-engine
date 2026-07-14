# Student GPT Engine

A stateless, asynchronous AI backend designed for educational use. This engine acts as an middle layer between frontend applications and LLMs. It is optimized for speed, cost-efficiency, and accuracy using semantic vector caching, dynamic context compression, and robust LaTeX parsing.

## Core Features
* **Semantic Vector Caching:** Uses `pgvector` to store and retrieve AI responses based on cosine similarity, bypassing the LLM for repeated questions.
* **Stateless Architecture:** The backend maintains zero active session state, requiring the frontend to pass context, which allows for infinite horizontal scaling.
* **Dynamic Context Compression:** Automatically summarizes older chat history to strictly maintain LLM token budgets.
* **Semantic Routing:** Analyzes user prompts to automatically trigger specific educational modes (QA, Flashcards, Pop Quizzes, Short Notes).
* **Safe Math Rendering:** Employs Regex to strictly validate and parse inline (`$`) and block (`$$`) LaTeX equations to prevent frontend crashes.

---

## Technology Stack
* **Framework:** FastAPI (Python 3.12+)
* **Database:** PostgreSQL (Dockerized) + `pgvector` extension
* **Driver:** `asyncpg` (for high-concurrency async operations)
* **LLM Provider:** OpenRouter (Models: Qwen 30B & text-embedding-3-small)
* **Validation:** Pydantic V2

---

## Installation & Setup

### 1. Prerequisites
* Python 3.12 or higher installed.
* Docker Desktop installed and running.
* Git Bash or a similar terminal emulator.
* An OpenRouter API Key.

### 2. Clone and Environment Setup
Clone the repository and set up your isolated Python environment:
```bash
git clone <your-repo-url>
cd student-gpt-engine
python -m venv .venv
source .venv/Scripts/activate  # On Windows Git Bash
pip install -r requirements.txt
```

### 3. Environment Variables

Create a `.env` file in the absolute root of your project. **Note:** Pydantic V2 requires strict type matching, and `httpx` requires trailing slashes to be perfectly formatted.

```env
# .env
LLM_BASE_URL=[https://openrouter.ai/api/v1/](https://openrouter.ai/api/v1/)
LLM_API_KEY=your_openrouter_api_key_here
LLM_MODEL=qwen/qwen3-30b-a3b-thinking-2507
EMBEDDING_MODEL=openai/text-embedding-3-small
DATABASE_URL=postgresql://postgres:mysecretpassword@localhost:5432/studentgpt

# Engine Settings
CONTEXT_RECENT_TURNS=4
CACHE_SIMILARITY_THRESHOLD=0.95

```

### 4. Database Initialization
I used docker to test it. This part is completely up to you. But if using docker: spin up a PostgreSQL container equipped with `pgvector`, and then populate it using the initialization script.

**Start the Database:**

```bash
docker run -d --name studentgpt-db \
  -e POSTGRES_PASSWORD=mysecretpassword \
  -e POSTGRES_DB=studentgpt \
  -p 5432:5432 \
  pgvector/pgvector:pg16

```

**Build the Tables & Schemas:**

```bash
docker exec -i studentgpt-db psql -U postgres -d studentgpt < migrations/001_init.sql

```

---

## Running the Engine

Start the FastAPI server using Uvicorn with auto-reload enabled:

```bash
uvicorn app.main:app --reload --port 8080

```

Once running, you can access the auto-generated API Documentation (Swagger UI) at:

 **http://localhost:8080/docs**

### API Testing (cURL)

You can test the core chat endpoint directly from your terminal:

```bash
curl -s -X POST http://localhost:8080/v1/chat \
  -F "conversation_id=$(python -c 'import uuid;print(uuid.uuid4())')" \
  -F "message=What is the derivative of x^2?" \
  -F 'history=[]' | python -m json.tool

```

---

## Frontend Handoff Guidelines

If you are connecting a UI to this backend, you must adhere to the following architectural rules:

1. **The History Rule (Statelessness):** The backend does **not** remember the chat. The frontend is entirely responsible for maintaining the state of the conversation. On every request, the frontend must pass the complete chat history as a JSON-encoded string inside the `history` form field.
* *Format:* `[{"role": "user", "content": "..."}]`


2. **Math Rendering (LaTeX):** The backend provides metadata to assist frontend renderers (KaTeX/MathJax).
* Check the `balanced` boolean in the JSON response. If `false`, the LLM hallucinated a broken LaTeX tag, and you should render it as raw text to avoid application crashes.
* The `latex_blocks` and `latex_inline` arrays contain the exact equations detected.



---

## 🧪 Testing

The testing suite uses `pytest` and `pytest-asyncio` to mock database connections and validate the pipeline.

**1. Setup `pytest.ini**`
Ensure you have a `pytest.ini` file in the root directory:

```ini
[pytest]
asyncio_mode = auto

```

**2. Run the Suite**
Always run tests from the absolute root of the project so Pydantic can locate the `.env` file:

```bash
pytest

```

---

## Common Issues & Debugging

During setup, theres a lot of annoying things for gods sake. Here are some of them:

### 1. "The Ghost Database" (Port 5432 Conflict)

* **Error:** `asyncpg.exceptions.InvalidPasswordError` or `role does not exist`, even though your `.env` perfectly matches your Docker run command.
* **Cause:** A native Windows PostgreSQL service is running silently in the background and has hijacked port `5432`. Uvicorn is talking to your Windows database, not your Docker container.
* **Fix:** Press the Windows Key -> Type `services.msc` -> Find `PostgreSQL` -> Right-click and **Stop**. Then restart your Docker container (`docker restart studentgpt-db`).

### 2. HTTPX DNS or 404 Errors

* **Error:** `[Errno 11001] getaddrinfo failed` or HTTP 404 Not Found from OpenRouter.
* **Cause:** The `httpx` library is extremely strict about slashes. If `LLM_BASE_URL` ends without a slash, and the endpoint begins with a slash, `httpx` will mangle the URL (e.g., stripping `api/v1` away).
* **Fix:** Ensure `LLM_BASE_URL` in your `.env` ends with a `/`. Ensure internal `client.post()` calls do *not* start with a `/` (e.g., use `"chat/completions"`, not `"/chat/completions"`).

### 3. Pydantic `ValidationError` on Boot

* **Error:** `A non-annotated attribute was detected... All model fields require a type annotation.`
* **Cause:** Pydantic V2 strictly requires type hints.
* **Fix:** Check `app/config.py`. Ensure every variable has a type (e.g., `context_recent_turns: int = 4`).

### 4. Pytest `RuntimeWarning: coroutine was never awaited`

* **Error:** Tests are skipped or throw coroutine warnings.
* **Cause:** Standard `pytest` cannot run `async def` functions out of the box.
* **Fix:** Install `pytest-asyncio` and ensure your `pytest.ini` file is configured with `asyncio_mode = auto`.

### 5. `asyncpg` DatatypeMismatchError (UUIDs)

* **Error:** PostgreSQL crashes when attempting to update the cache via the `invalidate` function.
* **Cause:** `asyncpg` does not automatically cast Python strings to PostgreSQL UUIDs.
* **Fix:** Explicitly cast the parameter in the raw SQL string inside `app/services/semantic_cache.py`:
`WHERE id = $1::uuid`

## Future Considerations (next ver. v2)

I intentionally left a few complex features out to prioritize speed and stability. Here is some stuff which is directly improvable:

* **Backend Session Memory (Statefulness):** Right now, the engine is entirely stateless (the frontend passes the history back and forth). I already built the `conversations` and `messages` SQL tables—V2 will transition to JWT-based user authentication and store chat histories directly in PostgreSQL. This feature could/count not help with costs, I'm not fully sure, do look into it.
* **Token Streaming (Server-Sent Events):** Currently, the API waits for the LLM to finish generating the entire response before returning the JSON. V2 will implement SSE or WebSockets to stream the response token-by-token for a ChatGPT-like real-time UI experience.
* **True Multimodal Support:** V1 uses local Tesseract OCR to extract text from uploaded images. V2 will route images directly to vision-capable LLMs. Basically multi-modal usage.
* **Advanced Cache Management:** Right now, bad answers are flagged via an `invalidated` boolean. V2 will include a Redis/Celery background worker to automatically prune dead cache entries and recalculate embeddings for updated educational materials.
* **Rate Limiting & Cost Controls:** Before putting this into production, V2 will implement strict IP-based rate limiting (via Redis) to protect the OpenRouter API key from abuse.
* **Mode recognition:** currently its just looking for keywords in a prompt to toggle mode. Having a pgvector and database for the same would be ideal but increase costs a bit.