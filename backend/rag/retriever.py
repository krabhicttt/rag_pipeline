"""
retriever.py
-------------
The core RAG query pipeline — called by api/routes.py on every chat message.

Retrieval-Augmented Generation flow
-------------------------------------
1. Embed the user's query            → embeddings.generate_embedding()
2. Search the vector store           → vector_store.similarity_search()
3. Build a grounded prompt           → build_prompt()
4. Send the prompt to Ollama         → ollama.chat()
5. Return the answer + source chunks → back to routes.py

Why RAG?
---------
Without RAG, the LLM can only answer from its training data.
With RAG, we inject relevant document chunks into the prompt so the model
can answer questions about YOUR private documents.
"""

from __future__ import annotations

import asyncio

from config.settings import settings
from rag.embeddings import generate_embedding
from rag.vector_store import similarity_search

import ollama
from ollama import Message


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a helpful assistant that answers questions based on the provided document context.

Rules:
- Answer ONLY from the context below. Do not use outside knowledge.
- If the context does not contain enough information, say "I don't have enough information in the documents to answer this."
- Be concise and factual.
- When quoting from a source, mention the document name.
"""


def build_prompt(query: str, chunks: list[dict], history: list[dict]) -> list[Message]:
    """
    Build the list of messages to send to ollama.chat().

    Parameters
    ----------
    query   : The user's question.
    chunks  : Retrieved document chunks from vector_store.similarity_search().
    history : Previous conversation messages [{"role": ..., "content": ...}].

    Returns
    -------
    A list of message dicts compatible with the Ollama chat API.
    """
    # Build the context block from retrieved chunks
    context_parts = [
        f"[Source {i}: {chunk['source']}]\n{chunk['text']}"
        for i, chunk in enumerate(chunks, 1)
    ]
    context = "\n\n---\n\n".join(context_parts) if context_parts else "No relevant documents found."

    messages: list[Message] = [Message(role="system", content=SYSTEM_PROMPT)]
    for h in history[-6:]:
        messages.append(Message(role=h["role"], content=h["content"]))
    messages.append(Message(
        role    = "user",
        content = f"Context from documents:\n\n{context}\n\nQuestion: {query}",
    ))
    return messages


# ---------------------------------------------------------------------------
# Main retrieval function
# ---------------------------------------------------------------------------

async def retrieve_and_answer(
    query:   str,
    model:   str,
    history: list[dict],
) -> tuple[str, list[dict]]:
    """
    Full RAG query pipeline.

    Parameters
    ----------
    query   : User's question.
    model   : Ollama model name chosen in the frontend.
    history : Previous conversation messages.

    Returns
    -------
    (answer_text, source_chunks)

    """
    # Step 1 — embed the query (sync call; run in thread pool to avoid blocking)
    print ("Query:::", query)
    query_embedding = await asyncio.to_thread(generate_embedding, query)

    # Step 2 — retrieve the top-k most similar chunks from Postgres
    chunks = await asyncio.to_thread(similarity_search, query_embedding, settings.top_k_results)
    print ("chunks:::", chunks)
    
    # Step 3 — build the grounded prompt
    messages = build_prompt(query, chunks, history)

    # Step 4 — call Ollama (sync → run in thread pool)
    response = await asyncio.to_thread(ollama.chat, model=model, messages=messages)
    answer   = response["message"]["content"]

    # Step 5 — format source chunks for the frontend source panel
    sources = [
        {
            "document": chunk["source"],
            "text":     chunk["text"],
            "score":    chunk["score"],
            "metadata": chunk.get("metadata", {}),
        }
        for chunk in chunks
    ]

    return answer, sources
