# RAG Chat — Backend Architecture

Python backend for the RAG Chat application.
This file explains the full architecture so you know exactly what to implement in each module.

---

## Tech Stack

| Component | Tool | Purpose |
|-----------|------|---------|
| Web framework | FastAPI | HTTP API server |
| LLM inference | Ollama | Run LLMs locally (llama3.2, mistral, …) |
| Embeddings | Ollama (nomic-embed-text) | Convert text → vectors |
| Vector store | Postgres + pgvector | Store & search embeddings |
| PDF loading | pypdf | Extract text from PDFs |
| DOCX loading | python-docx | Extract text from Word files |

---

## Folder Structure

```
backend/
├── main.py                    ← FastAPI app entry point
├── requirements.txt
├── .env.example               ← copy to .env and fill in your values
│
├── config/
│   └── settings.py            ← all config via environment variables
│
├── api/
│   └── routes.py              ← HTTP endpoints (chat, ingest, health)
│
└── rag/
    ├── document_processor.py  ← load files + chunk text
    ├── metadata_extractor.py  ← extract title, author, date, tags
    ├── normalizer.py          ← clean raw text
    ├── embeddings.py          ← call Ollama to get vectors
    ├── vector_store.py        ← read/write Postgres pgvector table
    └── retriever.py           ← full RAG query pipeline
```

---

## The Two Pipelines

### Pipeline A — Document Ingestion (run once per document set)

```
Your documents (PDF / DOCX / TXT)
         │
         ▼
[document_processor.py]  load_file()
         │  raw text
         ▼
[metadata_extractor.py]  extract_metadata()
         │  {title, author, date, tags, …}
         ▼
[normalizer.py]          normalize_text()
         │  clean text
         ▼
[document_processor.py]  chunk_text()
         │  ["chunk 1 …", "chunk 2 …", …]
         ▼
[embeddings.py]          generate_embedding()
         │  [[0.12, -0.34, …], …]
         ▼
[vector_store.py]        store_chunk()
         │
         ▼
  Postgres (pgvector)
```

Trigger via the API:
```bash
curl -X POST http://localhost:8000/api/ingest \
     -H "Content-Type: application/json" \
     -d '{"directory": "C:/path/to/your/docs"}'
```

---

### Pipeline B — Chat Query (runs on every user message)

```
User question  ("What is the refund policy?")
         │
         ▼
[embeddings.py]         generate_embedding()
         │  query vector [0.23, 0.11, …]
         ▼
[vector_store.py]       similarity_search()
         │  top-5 matching chunks
         ▼
[retriever.py]          build_prompt()
         │  system prompt + context + history + question
         ▼
  Ollama  ollama.chat(model="llama3.2", messages=[…])
         │  generated answer
         ▼
[api/routes.py]  → JSON response to frontend
```

---

## Setup Steps

### 1. Install Postgres and enable pgvector

```sql
-- In psql / pgAdmin:
CREATE DATABASE rag_db;
\c rag_db
CREATE EXTENSION IF NOT EXISTS vector;
```

### 2. Pull Ollama models

```bash
ollama pull llama3.2          # chat model
ollama pull nomic-embed-text  # embedding model
```

### 3. Create Python virtual environment

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 4. Configure environment

```bash
copy .env.example .env
# Edit .env with your Postgres credentials and model names
```

### 5. Run the server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## Implementation Order (recommended for learning)

Work through the modules in this order — each one depends on the previous:

1. **`config/settings.py`** — already done, just fill your `.env`
2. **`rag/normalizer.py`** — pure text functions, no external deps, great starting point
3. **`rag/metadata_extractor.py`** — file I/O + pypdf/docx
4. **`rag/document_processor.py`** — orchestrate loading + chunking
5. **`rag/vector_store.py`** — Postgres + pgvector connection
6. **`rag/embeddings.py`** — Ollama embedding call
7. **`rag/retriever.py`** — full query pipeline
8. **`api/routes.py`** — wire the pipeline to HTTP endpoints
9. **`main.py`** — call `create_table()` in startup, test end-to-end

---

## API Reference

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/health` | Liveness check |
| POST | `/api/chat` | Send a message, get an answer |
| POST | `/api/ingest` | Ingest documents into vector store |

### POST /api/chat

Request:
```json
{
  "message": "What is the refund policy?",
  "model": "llama3.2",
  "history": [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi, how can I help?"}
  ]
}
```

Response:
```json
{
  "response": "According to the policy document…",
  "model": "llama3.2",
  "sources": [
    {
      "document": "refund_policy.pdf",
      "text": "Customers may request a refund within 30 days…",
      "score": 0.91,
      "page": 3,
      "metadata": {"author": "Legal Team", "created_at": "2024-01-15"}
    }
  ]
}
```

---

## Tips for Learning Python

- Each function has a detailed `TODO` block with the exact code to write.
- Start simple: get one PDF loading, one chunk stored, one query working end-to-end.
- Use `print()` statements liberally while learning — FastAPI logs them to the terminal.
- Test individual functions in a Python REPL (`python` in the terminal) before wiring them into the API.
- The `tqdm` library gives you nice progress bars during ingestion — use it in `generate_embeddings_batch()`.
