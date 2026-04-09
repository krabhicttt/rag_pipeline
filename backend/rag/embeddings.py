"""
embeddings.py
--------------
Step 4 of the RAG ingestion pipeline (and also used at query time).

Responsibilities
----------------
Generate vector embeddings for text using a locally running Ollama model.

How embeddings work in RAG
--------------------------
Both document chunks and user queries are converted into high-dimensional
vectors (lists of floats).  Chunks whose vectors are "close" to the query
vector (measured by cosine similarity) are assumed to be relevant.

Recommended Ollama embedding models
-------------------------------------
  nomic-embed-text   — 768-dim, fast, good general purpose
  mxbai-embed-large  — 1024-dim, higher quality
  all-minilm         — 384-dim, very fast, smaller quality

Pull a model first:
    ollama pull nomic-embed-text
"""

from __future__ import annotations

from config.settings import settings

# import ollama   # uncomment when ready


def generate_embedding(text: str, model: str | None = None) -> list[float]:
    """
    Generate a single embedding vector for the given text.

    Parameters
    ----------
    text  : The text to embed (a chunk or a user query).
    model : Ollama model name. Defaults to settings.ollama_embed_model.

    Returns
    -------
    A list of floats (the embedding vector).

    TODO:
        import ollama
        model = model or settings.ollama_embed_model
        response = ollama.embeddings(model=model, prompt=text)
        return response["embedding"]

    Note: ollama.embeddings() is synchronous. For async FastAPI routes,
    consider running it in a thread pool:
        import asyncio
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: ollama.embeddings(model=model, prompt=text)
        )
        return response["embedding"]
    """
    raise NotImplementedError("Implement generate_embedding using ollama.embeddings()")


def generate_embeddings_batch(texts: list[str], model: str | None = None) -> list[list[float]]:
    """
    Generate embeddings for a list of texts (one at a time, Ollama has no batch API).

    TODO:
        return [generate_embedding(t, model) for t in texts]

    Tip: wrap with tqdm for a progress bar during ingestion:
        from tqdm import tqdm
        return [generate_embedding(t, model) for t in tqdm(texts, desc="Embedding")]
    """
    raise NotImplementedError("Implement generate_embeddings_batch")
