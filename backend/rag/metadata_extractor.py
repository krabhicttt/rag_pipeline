"""
metadata_extractor.py
----------------------
Step 2 of the RAG ingestion pipeline.

Responsibilities
----------------
Extract structured metadata from a document so that:
  - The vector store can filter results (e.g. "only search documents from 2024")
  - The chat UI can show "Source: Annual Report 2024, Section: Revenue"

Metadata you might want to extract
-----------------------------------
  title      — document title (from PDF properties or first heading)
  author     — from PDF properties or DOCX core properties
  created_at — file creation date or embedded document date
  source     — file name / path
  file_type  — pdf / docx / txt
  language   — detected language (optional)
  tags       — custom labels you assign manually or derive from content
  section    — heading of the section this chunk came from (optional)
  page       — page number (for PDFs)
"""

from __future__ import annotations

from pathlib import Path


def extract_metadata(file_path: Path, raw_text: str) -> dict:
    """
    Extract metadata from a document file.

    Parameters
    ----------
    file_path : The Path object pointing to the source file.
    raw_text  : The full raw text already read from the file.

    Returns
    -------
    A dict that will be stored alongside each chunk in Postgres.
    Keys should be consistent across all documents.

    TODO — starter implementation:
        metadata = {
            "source":    file_path.name,
            "file_type": file_path.suffix.lower().lstrip("."),
            "created_at": get_file_date(file_path),   # see helper below
        }

        # For PDFs — extract PDF properties:
        if file_path.suffix.lower() == ".pdf":
            from pypdf import PdfReader
            reader = PdfReader(str(file_path))
            info   = reader.metadata or {}
            metadata["title"]  = info.get("/Title", file_path.stem)
            metadata["author"] = info.get("/Author", "Unknown")

        # For DOCX — extract core properties:
        elif file_path.suffix.lower() == ".docx":
            from docx import Document
            doc  = Document(str(file_path))
            core = doc.core_properties
            metadata["title"]  = core.title or file_path.stem
            metadata["author"] = core.author or "Unknown"

        # Manual tags — add your own logic here:
        # metadata["tags"] = derive_tags(raw_text)

        return metadata
    """
    raise NotImplementedError("Implement extract_metadata")


def get_file_date(file_path: Path) -> str:
    """
    Return the file's last-modified date as an ISO string (YYYY-MM-DD).

    TODO:
        from datetime import datetime
        ts = file_path.stat().st_mtime
        return datetime.fromtimestamp(ts).date().isoformat()
    """
    raise NotImplementedError("Implement get_file_date")


def derive_tags(text: str, keywords: list[str] | None = None) -> list[str]:
    """
    Optional: derive topic tags from text by checking for keyword presence.

    Parameters
    ----------
    text     : The document or chunk text.
    keywords : A list of known domain keywords to look for.

    TODO:
        if not keywords:
            return []
        text_lower = text.lower()
        return [kw for kw in keywords if kw.lower() in text_lower]
    """
    raise NotImplementedError("Implement derive_tags (optional)")
