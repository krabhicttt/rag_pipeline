"""
routes.py
---------
All HTTP endpoints for the RAG Chat API.

Endpoints
---------
GET  /api/health   — liveness check (called by the frontend status indicator)
POST /api/chat     — send a user message, get a RAG-grounded answer
POST /api/ingest   — trigger document ingestion into the vector store

Frontend expects these exact response shapes — do not rename the keys.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from config.settings import settings

# Uncomment this import once you implement retriever:
from rag.retriever import retrieve_and_answer
from rag.document_processor import ingest_documents

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str                    # the user's question
    model:   str = "llama3.2"       # Ollama model chosen in the frontend
    history: list[dict] = []        # previous messages [{"role": "user"|"assistant", "content": "..."}]


class SourceChunk(BaseModel):
    document: str                   # source document name / file path
    text:     str                   # the retrieved chunk text
    score:    float | None = None   # cosine similarity score (0-1)
    page:     int    | None = None  # page number inside the document
    section:  str    | None = None  # heading / section name
    metadata: dict   | None = None  # any extra metadata you stored


class ChatResponse(BaseModel):
    response: str                   # the model's answer
    sources:  list[SourceChunk] = []
    model:    str


class IngestRequest(BaseModel):
    directory: str                  # local path to folder containing documents


class IngestResponse(BaseModel):
    status:          str
    documents_added: int


# ---------------------------------------------------------------------------
# GET /api/health
# ---------------------------------------------------------------------------

@router.get("/health")
async def health():
    """
    Simple liveness check.
    The frontend polls this every 30 s to show the green/red status dot.

    TODO (optional): Add deeper checks — ping Ollama, ping Postgres.
    """
    return {"status": "ok", "model": settings.ollama_chat_model}


# ---------------------------------------------------------------------------
# POST /api/chat
# ---------------------------------------------------------------------------

@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    print(f"Received chat request: {req.message} (model={req.model}, history_len={len(req.history)})")
    """
    Main chat endpoint — the heart of the RAG pipeline.

    Flow you need to implement inside rag/retriever.py:
    1. Generate an embedding for req.message  (rag/embeddings.py)
    2. Search the vector store for top-k similar chunks  (rag/vector_store.py)
    3. Build a prompt: system instructions + retrieved chunks + conversation history
    4. Call Ollama with the prompt  (ollama.chat())
    5. Return the answer + source chunks

    Example Ollama call (add to retriever.py):
        import ollama
        response = ollama.chat(
            model=req.model,
            messages=messages_list,   # list of {role, content} dicts
        )
        answer = response["message"]["content"]
    """

    # TODO: Replace this stub with your real implementation
    answer, sources = await retrieve_and_answer(
        query=req.message,
        model=req.model,
        history=req.history,
     )

    # --- STUB RESPONSE (remove once retriever is implemented) ---
    raise HTTPException(
        status_code=501,
        detail=(
            "Chat endpoint not implemented yet. "
            "Open backend/api/routes.py and backend/rag/retriever.py to implement."
        ),
    )


# ---------------------------------------------------------------------------
# POST /api/ingest
# ---------------------------------------------------------------------------

@router.post("/ingest", response_model=IngestResponse)
async def ingest(req: IngestRequest):
    """
    Trigger the document ingestion pipeline.

    Flow you need to implement inside rag/document_processor.py:
    1. Walk the directory and load each file  (pypdf / python-docx / plain text)
    2. Extract metadata  (rag/metadata_extractor.py)
    3. Normalize text  (rag/normalizer.py)
    4. Chunk the text  (rag/document_processor.py)
    5. Generate embeddings for each chunk  (rag/embeddings.py)
    6. Store chunks + embeddings in Postgres  (rag/vector_store.py)

    Call this endpoint once per document set (or whenever docs change).
    You can trigger it with curl:
        curl -X POST http://localhost:8000/api/ingest \
             -H "Content-Type: application/json" \
             -d '{"directory": "/path/to/your/docs"}'
    """

    try:
        count = await ingest_documents(req.directory)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return IngestResponse(status="success", documents_added=count)
