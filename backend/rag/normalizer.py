"""
normalizer.py
--------------
Step 3 of the RAG ingestion pipeline.

Responsibilities
----------------
Clean and standardise raw text before chunking and embedding.
Normalisation improves embedding quality and retrieval accuracy.

Common normalisation steps
--------------------------
1. Strip extra whitespace / newlines
2. Remove or replace special characters (bullets, dashes, ligatures)
3. Expand abbreviations (optional, domain-specific)
4. Unicode normalisation (NFC / NFKC)
5. Remove boilerplate (headers, footers, page numbers)
6. Optionally lowercase (be careful — case matters for named entities)

Important: Do NOT lowercase before embedding if you are using a model that
is case-sensitive (most modern Ollama embedding models are NOT, but check).
"""

from __future__ import annotations

import re
import unicodedata


def normalize_text(text: str) -> str:
    """
    Main normalisation function — apply all steps in order.

    Parameters
    ----------
    text : Raw text extracted from the document loader.

    Returns
    -------
    Cleaned text ready for chunking.
    """
    text = unicode_normalize(text)
    text = remove_control_characters(text)
    text = fix_whitespace(text)
    text = remove_page_numbers(text)
    # text = remove_boilerplate(text)   # add domain-specific patterns if needed
    return text.strip()


def unicode_normalize(text: str) -> str:
    """Normalise unicode to NFC form so equivalent characters are identical."""
    return unicodedata.normalize("NFC", text)


def remove_control_characters(text: str) -> str:
    """Remove invisible control characters, keeping newlines and tabs."""
    return "".join(
        ch for ch in text
        if unicodedata.category(ch)[0] != "C" or ch in "\n\t"
    )


def fix_whitespace(text: str) -> str:
    """Collapse multiple spaces/tabs into one; limit consecutive newlines to 2."""
    text = re.sub(r"[ \t]+",  " ",    text)
    text = re.sub(r"\n{3,}", "\n\n",  text)
    return text


def remove_page_numbers(text: str) -> str:
    """Remove 'Page N of M' patterns and lines that contain only a number."""
    text = re.sub(r"(?i)\bpage\s+\d+\s+of\s+\d+\b", "", text)
    text = re.sub(r"^\s*\d+\s*$", "", text, flags=re.MULTILINE)
    return text


def remove_boilerplate(text: str, patterns: list[str] | None = None) -> str:
    """
    Remove repeating header/footer text that appears on every page.

    Parameters
    ----------
    text     : The document text.
    patterns : Regex patterns to strip (e.g. company name, confidential label).
    """
    if not patterns:
        return text
    for pattern in patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.MULTILINE)
    return text
