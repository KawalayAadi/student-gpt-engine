-- 1. Enable the vector math engine
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Create the Telemetry flight-recorder table
CREATE TABLE IF NOT EXISTS request_logs (
    id SERIAL PRIMARY KEY,
    conversation_id VARCHAR(255),
    route VARCHAR(50),
    cache_hit BOOLEAN,
    ttft_ms INTEGER,
    total_latency_ms INTEGER,
    input_tokens INTEGER,
    output_tokens INTEGER,
    error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Create the Semantic Cache table
CREATE TABLE IF NOT EXISTS semantic_cache (
    -- Changed to UUID to match Pydantic's 'str' requirement
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_text TEXT NOT NULL,
    -- Fixed typo: embedding -> query_embedding
    query_embedding VECTOR(1536),
    response_text TEXT NOT NULL,
    mode VARCHAR(50) NOT NULL,
    hit_count INTEGER DEFAULT 0,
    invalidated BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    -- Added missing column
    last_used_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Create the standard Chat History tables
CREATE TABLE IF NOT EXISTS conversations (
    id VARCHAR(255) PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    conversation_id VARCHAR(255) REFERENCES conversations(id),
    role VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);