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

# import ollama   # uncomment for step 4


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


def build_prompt(query: str, chunks: list[dict], history: list[dict]) -> list[dict]:
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

    TODO:
        # Build the context block from retrieved chunks
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            context_parts.append(
                f"[Source {i}: {chunk['source']}]\n{chunk['text']}"
            )
        context = "\n\n---\n\n".join(context_parts)

        # Assemble messages list
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Add recent conversation history (exclude the current query)
        messages.extend(history[-6:])   # last 3 turns

        # Add the user query with context attached
        messages.append({
            "role": "user",
            "content": f"Context from documents:\n\n{context}\n\nQuestion: {query}"
        })

        return messages
    """
    raise NotImplementedError("Implement build_prompt()")


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
    
    # TODO step 3: messages = build_prompt(query, chunks, history)
    # TODO step 4: response = await asyncio.to_thread(ollama.chat, model=model, messages=messages)
    #              answer   = response["message"]["content"]
    # TODO step 5: format sources and return answer, sources
    """
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
    """
    raise NotImplementedError("Steps 3–5 (prompt, Ollama call, format) not yet implemented")
