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

from config.settings import settings

# Uncomment when ready:
# import ollama
# from rag.embeddings    import generate_embedding
# from rag.vector_store  import similarity_search


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

    TODO:
        # Step 1 — embed the query
        query_embedding = generate_embedding(query)

        # Step 2 — retrieve similar chunks
        chunks = similarity_search(query_embedding, top_k=settings.top_k_results)

        # Step 3 — build prompt
        messages = build_prompt(query, chunks, history)

        # Step 4 — call Ollama
        import ollama
        response = ollama.chat(model=model, messages=messages)
        answer   = response["message"]["content"]

        # Step 5 — format chunks for the frontend source panel
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

    Async note: ollama.chat() is synchronous. Run it in a thread pool:
        import asyncio
        loop     = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: ollama.chat(model=model, messages=messages)
        )
    """
    raise NotImplementedError("Implement retrieve_and_answer()")
