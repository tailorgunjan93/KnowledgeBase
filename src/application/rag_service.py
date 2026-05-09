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

    def answer(self, query: str, context_override: Optional[str] = None) -> Dict[str, Any]:
        """Main entry point to get an answer for a query."""
        log.info(f"RAG query started: {query}")
        
        # 1. Retrieval
        if context_override:
            context = context_override
            sources = [{"text": "Manual override", "source": "input"}]
        else:
            sources = self._vector_store.search(query)
            context = "\n\n".join([f"Source: {s.get('title', 'Unknown')}\n{s.get('text', '')}" for s in sources])

        # 2. Generation
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant. Use the provided context to answer questions accurately."},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
        ]
        
        response = self._llm.chat(messages)
        
        # 3. Evaluation (Self-Correction placeholder)
        # In a full implementation, we'd call the LLM again to evaluate the response.
        confidence = 0.9 # Placeholder
        
        return {
            "response": response,
            "confidence": confidence,
            "sources": sources
        }
