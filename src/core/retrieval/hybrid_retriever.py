"""Hybrid Retriever combining FAISS and BM25."""

from typing import List, Dict, Any, Optional
import numpy as np

from . import FAISSStore
from .bm25_store import BM25Store


class HybridRetriever:
    """Combines dense (FAISS) and sparse (BM25) retrieval."""

    def __init__(
        self,
        faiss_store: Optional[FAISSStore] = None,
        bm25_store: Optional[BM25Store] = None,
        alpha: float = 0.5,
    ):
        self.faiss_store = faiss_store
        self.bm25_store = bm25_store
        self.alpha = alpha  # Weight for FAISS (1-alpha for BM25)

    def search(
        self, query_embedding: np.ndarray, query_text: str, k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search using both methods and combine scores."""
        faiss_results = []
        bm25_results = []

        if self.faiss_store:
            faiss_results = self.faiss_store.search(query_embedding, k * 2)

        if self.bm25_store:
            bm25_results = self.bm25_store.search(query_text, k * 2)

        return self._reciprocal_rank_fusion(faiss_results, bm25_results, k)

    def _reciprocal_rank_fusion(
        self, faiss_results: List[Dict], bm25_results: List[Dict], k: int
    ) -> List[Dict[str, Any]]:
        """Combine results using Reciprocal Rank Fusion."""
        scores: Dict[str, float] = {}

        for rank, result in enumerate(faiss_results):
            doc_id = result["doc_id"]
            score = self.alpha * (1 / (rank + 1))
            scores[doc_id] = scores.get(doc_id, 0) + score

        for rank, result in enumerate(bm25_results):
            doc_id = result["doc_id"]
            score = (1 - self.alpha) * (1 / (rank + 1))
            scores[doc_id] = scores.get(doc_id, 0) + score

        sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:k]

        doc_map = {r["doc_id"]: r for r in faiss_results + bm25_results}

        results = []
        for doc_id, score in sorted_docs:
            if doc_id in doc_map:
                result = doc_map[doc_id].copy()
                result["combined_score"] = score
                results.append(result)

        return results

    def add_documents(
        self,
        texts: List[str],
        embeddings: np.ndarray,
        doc_ids: Optional[List[str]] = None,
    ) -> None:
        """Add documents to both stores."""
        doc_ids = doc_ids or [str(i) for i in range(len(texts))]

        if self.faiss_store:
            self.faiss_store.add_documents(texts, embeddings, doc_ids)

        if self.bm25_store:
            self.bm25_store.add_documents(texts, doc_ids)
