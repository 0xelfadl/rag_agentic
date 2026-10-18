import os

import psycopg

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://rag:rag@localhost:5433/rag")
EMBEDDING_DIM = 1024

SCHEMA = f"""
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
    id        serial PRIMARY KEY,
    slug      text UNIQUE NOT NULL,
    title     text NOT NULL,
    doc_type  text NOT NULL
);

CREATE TABLE IF NOT EXISTS chunks (
    id           bigserial PRIMARY KEY,
    document_id  int NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index  int NOT NULL,
    heading_path text NOT NULL,
    content      text NOT NULL,
    embedding    vector({EMBEDDING_DIM}) NOT NULL
);

CREATE INDEX IF NOT EXISTS chunks_embedding_idx
    ON chunks USING hnsw (embedding vector_cosine_ops);
"""

def connect():
    return psycopg.connect(DATABASE_URL);

def main():
    with connect() as conn:
        conn.execute(SCHEMA)
        version = conn.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector'").fetchone()[0]
        tables= conn.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename").fetchall()
    
    print(f"pgvector {version} is ready")
    print(f"Tables:", [row[0] for row in tables])

if __name__=="__main__":
    main()