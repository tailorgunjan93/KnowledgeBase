"""Wrapper around FAISS. All `import faiss` calls live here."""
import faiss
import numpy as np
import logging
from src.infrastructure.adapters.sentence_transformer_embedder import SentenceTransformerEmbedder

logger = logging.getLogger(__name__)


class FAISSAdapter:
    """Implements VectorStorePort backed by FAISS + in-memory metadata.

    Uses int8 scalar quantization by default (4× memory reduction, ~1% recall
    loss).  Controlled by FAISS_QUANTIZE / FAISS_QUANTIZE_TYPE app settings.
    The index is created lazily on the first ``add()`` call so that quantizer
    training has real vectors to learn from.
    """

    def __init__(self, embedder: SentenceTransformerEmbedder, dim: int = 384) -> None:
        self._embedder = embedder
        self._dim = dim
        self._index: faiss.Index | None = None   # created lazily on first add
        self._metadata: list[dict] = []

    # ── internal ──────────────────────────────────────────────────────────────

    def _build_index(self, embeddings: np.ndarray) -> faiss.Index:
        """Create and train the FAISS index for *embeddings*."""
        from src.core.search.dynamic_index import _make_faiss_index
        from src.core.settings import get_settings
        settings = get_settings()

        index = _make_faiss_index(
            self._dim,
            embeddings,
            quantize=settings.faiss_quantize,
            quantize_type=settings.faiss_quantize_type,
        )
        qt_label = f"SQ{settings.faiss_quantize_type[-1].upper()}" if settings.faiss_quantize else "FlatL2"
        logger.info(f"FAISSAdapter: initialised {qt_label} index (dim={self._dim}).")
        return index

    # ── public API ────────────────────────────────────────────────────────────

    def add(self, texts: list[str], metadatas: list[dict]) -> None:
        vectors = np.array(self._embedder.embed_batch(texts), dtype="float32")

        if self._index is None:
            # First batch: build + train the index, then add vectors
            self._index = self._build_index(vectors)
        else:
            # Subsequent batches: just add (index is already trained)
            self._index.add(vectors)

        self._metadata.extend(metadatas)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        if self._index is None or self._index.ntotal == 0:
            return []

        vector = np.array([self._embedder.embed(query)], dtype="float32")
        distances, indices = self._index.search(vector, top_k)
        results = []

        if not len(distances) or not len(indices) or not len(distances[0]) or not len(indices[0]):
            return results

        for dist, idx in zip(distances[0], indices[0]):
            if 0 <= idx < len(self._metadata):
                results.append({**self._metadata[idx], "score": float(1 / (1 + dist))})
        return results

    def delete(self, ids: list[str]) -> None:
        # Flat/SQ indices don't support in-place deletion; filter metadata only.
        self._metadata = [m for m in self._metadata if m.get("id") not in ids]
        # Full rebuild would be needed to actually remove vectors — extend if required.
