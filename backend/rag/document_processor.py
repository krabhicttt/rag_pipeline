"""
document_processor.py
----------------------
Step 1 of the RAG ingestion pipeline.

Responsibilities
----------------
- Walk a directory and detect file types (.pdf, .docx, .txt, …)
- Load raw text from each file
- Split the text into overlapping chunks suitable for embedding
- Coordinate the full ingestion flow (calls other rag/ modules)

Key concepts
------------
Chunking strategy:  Split by a fixed character count (CHUNK_SIZE) with a
sliding window overlap (CHUNK_OVERLAP) so that context is not lost at
chunk boundaries.  You can also split by paragraph or sentence — experiment
and see which gives better retrieval quality.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from config.settings import settings
from rag.embeddings import generate_embedding
from rag.metadata_extractor import extract_metadata
from rag.normalizer import normalize_text
from rag.vector_store import store_chunk


# ---------------------------------------------------------------------------
# Data structure for a single chunk
# ---------------------------------------------------------------------------

class DocumentChunk:
    """Represents one piece of text that will be embedded and stored."""

    def __init__(
        self,
        text:      str,
        source:    str,           # file name or path
        chunk_idx: int,           # chunk index within the document
        metadata:  dict | None = None,
    ):
        self.text      = text
        self.source    = source
        self.chunk_idx = chunk_idx
        self.metadata  = metadata or {}


# ---------------------------------------------------------------------------
# File loaders — one function per file type
# ---------------------------------------------------------------------------

def load_pdf(file_path: Path) -> str:
    """Extract plain text from a PDF file using pypdf."""
    from pypdf import PdfReader

    reader = PdfReader(str(file_path))
    pages  = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages)


def load_docx(file_path: Path) -> str:
    """Extract plain text from a Word document (.docx) using python-docx."""
    from docx import Document

    doc   = Document(str(file_path))
    paras = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paras)


def load_txt(file_path: Path) -> str:
    """Read a plain-text file."""
    return file_path.read_text(encoding="utf-8", errors="replace")


SUPPORTED_SUFFIXES = {".pdf", ".docx", ".txt", ".md"}


def load_file(file_path: Path) -> str:
    """Dispatch to the correct loader based on file extension."""
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return load_pdf(file_path)
    elif suffix == ".docx":
        return load_docx(file_path)
    elif suffix in (".txt", ".md"):
        return load_txt(file_path)
    else:
        raise ValueError(f"Unsupported file type: {suffix}")


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """
    Split text into overlapping chunks.

    Parameters
    ----------
    text       : The full document text (already normalised).
    chunk_size : Max characters per chunk.
    overlap    : Characters repeated between consecutive chunks to preserve context.
    """
    chunks: list[str] = []
    start = 0
    while start < len(text):
        chunks.append(text[start : start + chunk_size])
        start += chunk_size - overlap
    return chunks


# ---------------------------------------------------------------------------
# Main ingestion entry point (called from api/routes.py)
# ---------------------------------------------------------------------------

async def ingest_documents(directory: str) -> int:
    """
    Walk *directory* recursively, load every supported file, and return the
    number of documents loaded.

    Steps implemented
    -----------------
    1. Walk the directory and load each file (pypdf / python-docx / plain text)
    2. Extract metadata (metadata_extractor.py)
    3. Normalise text (normalizer.py)
    4. Chunk the text (chunk_text)
    5. Generate an embedding per chunk via Ollama (embeddings.py)
    6. Store each chunk + embedding in Postgres (vector_store.py)

    Returns the total number of chunks stored.
    """
    root = Path(directory)
    if not root.exists() or not root.is_dir():
        raise ValueError(f"Not a valid directory: {directory}")

    total_chunks = 0

    for file_path in sorted(root.rglob("*")):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue
        if not file_path.name.__eq__("liq_use_liqexit1_interface_dev.pdf"):
             print(f"--- Skipping {file_path} (not the target file) ---")
             continue
        
        raw_text = load_file(file_path)
        if not raw_text.strip():
            continue

        print(f"[ingest] Loaded {file_path.name} ({len(raw_text):,} chars)")

        metadata = extract_metadata(file_path, raw_text)
        print(f"metadata for {file_path.name}: {metadata}")

        clean_text = normalize_text(raw_text)
        chunks = chunk_text(clean_text, settings.chunk_size, settings.chunk_overlap)
        for idx, chunk in enumerate(chunks):
            embedding = await asyncio.to_thread(generate_embedding, chunk)
            print(f"[ingest]   chunk {idx}: {len(embedding)}-dim embedding")
            await asyncio.to_thread(store_chunk, chunk, embedding, str(file_path), idx, metadata)
            total_chunks += 1

    return total_chunks
