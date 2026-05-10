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
        import sys
        log.info(f"RAG query started: {query}")
        print(f"DEBUG RAGService: query={query[:50]}", file=sys.stderr)
        sys.stderr.flush()
        
        # 1. Retrieval
        if context_override:
            context = context_override
            sources = [{"text": "Manual override", "source": "input"}]
        else:
            print(f"DEBUG RAGService: calling vector_store.search()", file=sys.stderr)
            sys.stderr.flush()
            sources = self._vector_store.search(query)
            print(f"DEBUG RAGService: retrieved {len(sources)} sources", file=sys.stderr)
            sys.stderr.flush()
            for i, s in enumerate(sources):
                print(f"  source[{i}]: {s.get('doc_id')}, chunk_id={s.get('chunk_id')}, text_len={len(s.get('text',''))}", file=sys.stderr)
            context = "\n\n".join([f"Source: {s.get('title', 'Unknown')}\n{s.get('text', '')}" for s in sources])

        # 2. Generation
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant. Use the provided context to answer questions accurately."},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
        ]
        
        print(f"DEBUG RAGService: calling LLM.chat() with {len(messages)} messages", file=sys.stderr)
        sys.stderr.flush()
        response = self._llm.chat(messages)
        print(f"DEBUG RAGService: LLM response len={len(response)}", file=sys.stderr)
        sys.stderr.flush()
        
        # 3. Evaluation (Self-Correction placeholder)
        confidence = 0.9 # Placeholder
        
        return {
            "response": response,
            "confidence": confidence,
            "sources": sources
        }
