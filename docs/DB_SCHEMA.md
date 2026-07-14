-- docs/DB_SCHEMA.md / migrations/001_init.sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE conversations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  student_id TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id UUID REFERENCES conversations(id),
  role TEXT NOT NULL CHECK (role IN ('user','assistant','system')),
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- semantic cache table
CREATE TABLE semantic_cache (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  query_text TEXT NOT NULL,
  query_embedding VECTOR(1536) NOT NULL,
  response_text TEXT NOT NULL,
  mode TEXT,                          -- e.g. 'qa', 'flashcards', 'pop_quiz'
  hit_count INT DEFAULT 0,
  invalidated BOOLEAN DEFAULT FALSE,   -- manual/automatic invalidation flag
  created_at TIMESTAMPTZ DEFAULT now(),
  last_used_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX semantic_cache_embedding_idx
  ON semantic_cache USING ivfflat (query_embedding vector_cosine_ops)
  WITH (lists = 100);

-- telemetry
CREATE TABLE request_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id UUID,
  route TEXT,                -- which semantic-router path was taken
  cache_hit BOOLEAN,
  ttft_ms INT,                -- time to first token
  total_latency_ms INT,
  input_tokens INT,
  output_tokens INT,
  error TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);