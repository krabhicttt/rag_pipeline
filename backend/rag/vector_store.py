"""
vector_store.py
----------------
Step 5 of the RAG ingestion pipeline.

Responsibilities
----------------
- Create and manage the Postgres table that stores chunks + their embeddings
- Store a new chunk (insert)
- Search for the most similar chunks to a query embedding (similarity search)

Why Postgres + pgvector?
-------------------------
pgvector adds a new column type `vector(N)` to Postgres and provides
approximate nearest-neighbour (ANN) index support (IVFFlat / HNSW).
This means you do NOT need a separate vector database — your existing
Postgres instance can serve as the vector store.

Setup (run once in psql or pgAdmin):
    CREATE EXTENSION IF NOT EXISTS vector;

Then create the table (see create_table() below).
"""

from __future__ import annotations

from config.settings import settings

# Uncomment when ready:
# import psycopg2
# from pgvector.psycopg2 import register_vector


# ---------------------------------------------------------------------------
# Table definition (SQL)
# ---------------------------------------------------------------------------

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS document_chunks (
    id          SERIAL PRIMARY KEY,
    source      TEXT        NOT NULL,        -- file name / path
    chunk_idx   INTEGER     NOT NULL,        -- chunk number within the document
    text        TEXT        NOT NULL,        -- the chunk text
    embedding   vector(768),                 -- change 768 to match your model's dimension
    metadata    JSONB       DEFAULT '{}',    -- arbitrary metadata dict
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- HNSW index for fast approximate nearest-neighbour search
-- Create this AFTER you have inserted data (indexes are faster to build on existing data)
-- CREATE INDEX ON document_chunks USING hnsw (embedding vector_cosine_ops);
"""


def get_connection():
    """
    Return a new psycopg2 connection with the pgvector type registered.
    Each caller is responsible for closing the connection.
    """
    import psycopg2
    from pgvector.psycopg2 import register_vector

    conn = psycopg2.connect(settings.postgres_dsn)
    register_vector(conn)
    return conn


def create_table() -> None:
    """
    Create the pgvector extension and document_chunks table if they don't exist.
    Called once from main.py → on_startup().
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            cur.execute(CREATE_TABLE_SQL)
        conn.commit()
    finally:
        conn.close()


def store_chunk(
    text:      str,
    embedding: list[float],
    source:    str,
    chunk_idx: int,
    metadata:  dict | None = None,
) -> None:
    """
    Insert one chunk (text + embedding + metadata) into document_chunks.
    """
    import json

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO document_chunks (source, chunk_idx, text, embedding, metadata)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (source, chunk_idx, text, embedding, json.dumps(metadata or {})),
            )
        conn.commit()
    finally:
        conn.close()


def similarity_search(
    query_embedding: list[float],
    top_k: int | None = None,
) -> list[dict]:
    """
    Return the top-k chunks whose embeddings are closest to query_embedding.

    Uses pgvector cosine distance (<=>). Score = 1 - cosine_distance,
    so higher score means more similar.

    Parameters
    ----------
    query_embedding : Embedding of the user's query (from embeddings.py).
    top_k           : Number of results. Defaults to settings.top_k_results.
    """
    top_k = top_k or settings.top_k_results
    conn  = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT text, source, chunk_idx, metadata,
                       1 - (embedding <=> %s::vector) AS score
                FROM document_chunks
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """,
                (query_embedding, query_embedding, top_k),
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    return [
        {
            "text":      row[0],
            "source":    row[1],
            "chunk_idx": row[2],
            "metadata":  row[3],
            "score":     float(row[4]),
        }
        for row in rows
    ]


def delete_document(source: str) -> int:
    """
    Remove all chunks belonging to *source* (file path).
    Returns the number of rows deleted.
    Useful when a document is updated and needs to be re-ingested.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM document_chunks WHERE source = %s", (source,)
            )
            count = cur.rowcount
        conn.commit()
    finally:
        conn.close()
    return count
