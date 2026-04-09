"""
main.py
-------
FastAPI application entry point.

Run the server:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000

Then open the frontend index.html in a browser and start chatting.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import settings
from api.routes import router


# ---------------------------------------------------------------------------
# App instance
# ---------------------------------------------------------------------------
app = FastAPI(
    title="RAG Chat API",
    description="Retrieval-Augmented Generation chat backend powered by Ollama + pgvector",
    version="0.1.0",
)

# ---------------------------------------------------------------------------
# CORS  — allows the frontend (running on a different port) to call this API
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,   # set in .env → CORS_ORIGINS
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
app.include_router(router, prefix="/api")


# ---------------------------------------------------------------------------
# Startup / Shutdown events
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def on_startup():
    """
    TODO: Add startup logic here, for example:
      - Create the pgvector extension in Postgres
      - Create the embeddings table if it doesn't exist
      - Warm up the Ollama model
    """
    print("RAG Chat API started.")
    print(f"  Chat model  : {settings.ollama_chat_model}")
    print(f"  Embed model : {settings.ollama_embed_model}")
    print(f"  Postgres    : {settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}")


@app.on_event("shutdown")
async def on_shutdown():
    """
    TODO: Close database connections / clean up resources.
    """
    print("RAG Chat API shutting down.")
