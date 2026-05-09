"""Wrapper around FAISS. All `import faiss` calls live here."""
import faiss
import numpy as np
from src.ports.vector_store_port import VectorStorePort
from src.infrastructure.adapters.sentence_transformer_embedder import SentenceTransformerEmbedder


class FAISSAdapter:
    """Implements VectorStorePort backed by FAISS + in-memory metadata."""

    def __init__(self, embedder: SentenceTransformerEmbedder, dim: int = 384) -> None:
        self._embedder = embedder
        self._index = faiss.IndexFlatL2(dim)
        self._metadata: list[dict] = []

    def add(self, texts: list[str], metadatas: list[dict]) -> None:
        vectors = np.array(self._embedder.embed_batch(texts), dtype="float32")
        self._index.add(vectors)
        self._metadata.extend(metadatas)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        vector = np.array([self._embedder.embed(query)], dtype="float32")
        distances, indices = self._index.search(vector, top_k)
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self._metadata):
                results.append({**self._metadata[idx], "score": float(1 / (1 + dist))})
        return results

    def delete(self, ids: list[str]) -> None:
        # FAISS flat index doesn't support deletion; rebuild on delete.
        self._metadata = [m for m in self._metadata if m.get("id") not in ids]
        # Rebuild index from remaining metadata (requires stored vectors — extend as needed)
        # For now, we'll leave it as a placeholder as per instruction.
        pass
