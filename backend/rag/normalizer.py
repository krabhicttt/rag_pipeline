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

    TODO — starter implementation:
        text = unicode_normalize(text)
        text = remove_control_characters(text)
        text = fix_whitespace(text)
        text = remove_page_numbers(text)
        # text = remove_boilerplate(text)   # add if needed
        return text.strip()
    """
    raise NotImplementedError("Implement normalize_text")


def unicode_normalize(text: str) -> str:
    """
    Normalise unicode to NFC form so that equivalent characters are identical.

    TODO:
        return unicodedata.normalize("NFC", text)
    """
    raise NotImplementedError("Implement unicode_normalize")


def remove_control_characters(text: str) -> str:
    """
    Remove invisible control characters (except newlines and tabs).

    TODO:
        return "".join(
            ch for ch in text
            if unicodedata.category(ch)[0] != "C" or ch in "\n\t"
        )
    """
    raise NotImplementedError("Implement remove_control_characters")


def fix_whitespace(text: str) -> str:
    """
    Collapse multiple spaces/tabs into one, and limit consecutive newlines to 2.

    TODO:
        text = re.sub(r"[ \t]+",   " ",  text)   # collapse spaces
        text = re.sub(r"\n{3,}",  "\n\n", text)  # max 2 blank lines
        return text
    """
    raise NotImplementedError("Implement fix_whitespace")


def remove_page_numbers(text: str) -> str:
    """
    Remove common page-number patterns like "Page 1 of 10" or standalone digits
    on their own line.

    TODO:
        text = re.sub(r"(?i)\bpage\s+\d+\s+of\s+\d+\b", "", text)
        text = re.sub(r"^\s*\d+\s*$", "", text, flags=re.MULTILINE)
        return text
    """
    raise NotImplementedError("Implement remove_page_numbers")


def remove_boilerplate(text: str, patterns: list[str] | None = None) -> str:
    """
    Remove repeating header/footer text that appears on every page.

    Parameters
    ----------
    text     : The document text.
    patterns : List of regex patterns to strip (e.g. company name, confidential label).

    TODO:
        if not patterns:
            return text
        for pattern in patterns:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.MULTILINE)
        return text
    """
    raise NotImplementedError("Implement remove_boilerplate (optional, domain-specific)")
