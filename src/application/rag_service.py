from typing import List, Dict, Any, Optional
from src.ports.llm_port import LLMPort
from src.ports.vector_store_port import VectorStorePort
from src.core.logger import get_logger

log = get_logger(__name__)

class SelfCorrectingRAG:
    """
    Core RAG logic using the provided LLM and VectorStore ports.
    Follows a self-correcting pattern: retrieve, generate, evaluate.
    """

    def __init__(
        self,
        llm: LLMPort,
        vector_store: VectorStorePort,
        confidence_threshold: float = 0.5,
        max_retries: int = 2,
    ) -> None:
        self._llm = llm
        self._vector_store = vector_store
        self._confidence_threshold = confidence_threshold
        self._max_retries = max_retries

    def answer(self, query: str, context_override: Optional[str] = None, sources_override: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Main entry point to get an answer for a query."""
        log.info(f"RAG query started: {query}")

        # 1. Retrieval
        if context_override is not None:
            context = context_override
            sources = sources_override if sources_override is not None else [{"text": "Manual override", "source": "input"}]
        else:
            sources = self._vector_store.search(query)
            context = "\n\n".join([f"Source: {s.get('title', 'Unknown')}\n{s.get('text', '')}" for s in sources])

        # 2. Generation
        has_web = context_override is not None and "[WEB SEARCH" in (context_override or "")

        if not context.strip():
            # No KB context — respond conversationally without forcing a RAG wrapper
            messages = [
                {"role": "system", "content": "You are a helpful AI assistant. Answer the user's message directly and conversationally."},
                {"role": "user", "content": query},
            ]
        elif has_web:
            messages = [
                {"role": "system", "content": (
                    "You are a helpful AI assistant with access to real-time web search results. "
                    "The context below contains live web search results already fetched for this query. "
                    "Use these results to answer the question with current, up-to-date information. "
                    "Cite the titles or URLs from the results when relevant. "
                    "Do NOT call any tools or functions — all search results are already provided in the context."
                )},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"},
            ]
        else:
            messages = [
                {"role": "system", "content": (
                    "You are a helpful AI assistant. Use the provided context to answer questions accurately. "
                    "If the context does not contain the answer, say so."
                )},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"},
            ]

        response = self._llm.chat(messages)
        confidence = 0.9

        return {
            "response": response,
            "confidence": confidence,
            "sources": sources,
        }

    def answer_stream(self, query: str, context_override: Optional[str] = None, sources_override: Optional[List[Dict]] = None):
        """Streaming version of answer."""
        # 1. Retrieval (same as answer)
        if context_override is not None:
            context = context_override
            sources = sources_override if sources_override is not None else [{"text": "Manual override", "source": "input"}]
        else:
            sources = self._vector_store.search(query)
            context = "\n\n".join([f"Source: {s.get('title', 'Unknown')}\n{s.get('text', '')}" for s in sources])

        # 2. Build messages (same as answer)
        has_web = context_override is not None and "[WEB SEARCH" in (context_override or "")
        if not context.strip():
            messages = [
                {"role": "system", "content": "You are a helpful AI assistant. Answer the user's message directly and conversationally."},
                {"role": "user", "content": query},
            ]
        elif has_web:
            messages = [
                {"role": "system", "content": (
                    "You are a helpful AI assistant with access to real-time web search results. "
                    "The context below contains live web search results already fetched for this query. "
                    "Use these results to answer the question with current, up-to-date information. "
                    "Cite the titles or URLs from the results when relevant. "
                    "Do NOT call any tools or functions — all search results are already provided in the context."
                )},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"},
            ]
        else:
            messages = [
                {"role": "system", "content": (
                    "You are a helpful AI assistant. Use the provided context to answer questions accurately. "
                    "If the context does not contain the answer, say so."
                )},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"},
            ]

        # 3. Stream
        return self._llm.chat_stream(messages), sources
