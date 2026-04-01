 
CREATE EXTENSION IF NOT EXISTS vector;

CREATE SCHEMA IF NOT EXISTS vector;

CREATE TABLE vector.law_chunks (
    id         SERIAL PRIMARY KEY,
    law        TEXT NOT NULL,
    article_id TEXT NOT NULL,
    title      TEXT,
    content    TEXT NOT NULL,
    embedding  vector(3072)
);

CREATE INDEX IF NOT EXISTS law_chunks_embedding_idx
    ON vector.law_chunks USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 10);
