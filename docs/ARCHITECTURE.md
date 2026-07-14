# Student GPT Engine: System Architecture

## Core Technology Stack
* **Framework:** FastAPI (Python 3.12+)
* **Database:** PostgreSQL (Dockerized)
* **Vector Engine:** `pgvector` (for semantic caching)
* **Database Driver:** `asyncpg` (for high-concurrency async operations)
* **LLM Provider:** OpenRouter (Model: Qwen 30B / text-embedding-3-small)
* **Validation:** Pydantic V2



## The Request Pipeline
When a `POST` request hits the `/v1/chat` endpoint, it undergoes the following lifecycle:

1. **Pre-processing (Optional):** If an image is uploaded, it is routed through Tesseract OCR and resized to extract text context.
2. **Semantic Routing:** The raw prompt is evaluated for intent keywords (e.g., "flashcard", "quiz") to dynamically assign a response mode.
3. **Vectorization:** The prompt is converted into a 1536-dimensional float array using the embedding model.
4. **Semantic Cache Lookup:** The embedding is compared against the `semantic_cache` table using cosine distance (`<=>`). If a similarity match of `>= 0.95` is found, the LLM is bypassed entirely, and the cached response is instantly returned.
5. **Context Compression:** If a cache miss occurs, the provided chat history is analyzed. Recent turns are preserved, while older context is aggressively summarized by the LLM to preserve token limits.
6. **LLM Generation:** The compressed history, dynamic XML system prompt, and user query are sent to the primary LLM.
7. **Post-processing:** The LLM's response is parsed for mathematical equations. LaTeX is explicitly separated into inline and block arrays to guarantee safe rendering on the frontend.
8. **Telemetry & Caching:** The new response is vectorized, stored in the semantic cache, and the request metrics (latency, tokens, mode) are logged to the telemetry table.



## Database Architecture
The PostgreSQL database consists of isolated tables to handle telemetry, caching, and future-proofing for stateful features.

* `request_logs`: A flight-recorder table tracking latency, cache hits, token usage, and routing decisions for analytics.
* `semantic_cache`: Stores the `query_text`, `query_embedding` (VECTOR 1536), and `response_text`. Uses a `hit_count` and `last_used_at` timestamp for cache eviction strategies. Includes an `invalidated` boolean for user-flagged bad responses.
* `conversations` & `messages`: Currently inactive. Pre-built schemas for a potential transition from stateless frontend-memory to stateful backend-memory.



## Core Modules (`app/services/`)

* `chat.py` (Router): The primary FastAPI controller binding the multipart form data to the service layer.
* `semantic_router.py`: Determines the educational mode (QA, Flashcards, Pop Quiz, Short Notes) to format the AI's output.
* `semantic_cache.py`: Manages the `asyncpg` connection pool to execute highly optimized `pgvector` queries.
* `context_compressor.py`: A cost-saving module that injects a summary of older messages into the system prompt to maintain context without exceeding token budgets.
* `latex_postprocess.py`: Uses Regex to safely extract and validate `$$` (block) and `$` (inline) LaTeX, preventing frontend math rendering crashes.
* `micro_templates.py`: An XML-based prompt management system that strictly injects only the necessary instructions based on the active semantic route.


## Important Frontend Implementation Rules

### 1. The Stateless "History" Requirement
The backend does **not** store chat history for active sessions. The frontend is entirely responsible for maintaining the state of the conversation. 
* On every request, the frontend must pass the complete context window as a JSON-encoded string inside the `history` form field. 
* Schema required: `[{"role": "user", "content": "..."}]`

### 2. Math Rendering
The backend does not alter the AI's raw text. Instead, it provides metadata to assist the frontend renderer (like KaTeX or MathJax).
* Check the `balanced` boolean in the response. If `false`, the LLM hallucinated a broken LaTeX tag, and the frontend should render it as raw text to avoid application crashes.
* The `latex_blocks` and `latex_inline` arrays contain exactly what equations were detected. 

### 3. Cache Invalidation
If a user downvotes an answer, the frontend should issue a request to the `invalidate` endpoint (to be implemented) passing the cache ID. This flags the row in PostgreSQL so it is never served as a cache hit again.