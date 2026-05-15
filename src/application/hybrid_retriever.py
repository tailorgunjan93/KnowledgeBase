from src.infrastructure.adapters.bm25_adapter import BM25Adapter
from src.ports.vector_store_port import VectorStorePort


class HybridRetriever:
    """
    Combines dense (FAISS) and sparse (BM25) retrieval
    using Reciprocal Rank Fusion.
    Single Responsibility: retrieval only, no generation.
    """

    def __init__(
        self,
        dense_store: VectorStorePort,
        sparse_store: BM25Adapter,
        rrf_k: int = 60,
    ) -> None:
        self._dense = dense_store
        self._sparse = sparse_store
        self._rrf_k = rrf_k

    def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
        dense_results = self._dense.search(query, top_k=top_k * 2)
        sparse_results = self._sparse.search(query, top_k=top_k * 2)
        return self._rrf_fuse(dense_results, sparse_results, top_k)

    def _rrf_fuse(
        self,
        dense: list[dict],
        sparse: list[dict],
        top_k: int,
    ) -> list[dict]:
        scores: dict[str, float] = {}
        doc_map: dict[str, dict] = {}

        for rank, doc in enumerate(dense):
            key = doc.get("id", doc.get("text", str(rank)))
            scores[key] = scores.get(key, 0) + 1 / (self._rrf_k + rank + 1)
            doc_map[key] = doc

        for rank, doc in enumerate(sparse):
            key = doc.get("id", doc.get("text", str(rank)))
            scores[key] = scores.get(key, 0) + 1 / (self._rrf_k + rank + 1)
            doc_map[key] = doc

        sorted_keys = sorted(scores, key=lambda k: scores[k], reverse=True)
        return [doc_map[k] for k in sorted_keys[:top_k]]
