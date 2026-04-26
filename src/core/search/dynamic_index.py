"""Per-document FAISS index manager for dynamic search."""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import os
import pickle
import shutil
from pathlib import Path
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

try:
    import faiss
except ImportError:
    faiss = None

try:
    from rank_bm25 import BM25Okapi
except ImportError:
    BM25Okapi = None


class DocumentIndex:
    """Manages per-document FAISS and BM25 indices."""

    def __init__(
        self,
        document_id: int,
        base_path: str = "data_storage/indices",
        dimension: int = 384,
        chunk_size: int = 500,
    ):
        self.document_id = document_id
        self.base_path = Path(base_path)
        self.dimension = dimension
        self.chunk_size = chunk_size
        self.index_dir = self.base_path / str(document_id)

        self.faiss_index = None
        self.bm25_index = None
        self.chunks: List[str] = []
        self.chunk_ids: List[str] = []

    def build(self, text: str) -> bool:
        """Build indices for document text."""
        if faiss is None or BM25Okapi is None:
            raise ImportError("faiss-cpu and rank-bm25 required")

        try:
            # Create index directory
            self.index_dir.mkdir(parents=True, exist_ok=True)

            # Chunk the text
            self.chunks = self._chunk_text(text)
            self.chunk_ids = [f"chunk_{i}" for i in range(len(self.chunks))]

            # Build FAISS index
            self._build_faiss_index()

            # Build BM25 index
            self._build_bm25_index()

            # Save metadata
            self._save_metadata()

            logger.info(f"Built indices for document {self.document_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to build indices: {e}")
            return False

    def _chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks."""
        words = text.split()
        chunks = []

        for i in range(0, len(words), self.chunk_size // 2):
            chunk = " ".join(words[i : i + self.chunk_size])
            if chunk:
                chunks.append(chunk)

        return chunks if chunks else [text]

    def _build_faiss_index(self):
        """Build FAISS index from chunks."""
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer("all-MiniLM-L6-v2")
        embeddings = model.encode(self.chunks, convert_to_numpy=True)

        self.faiss_index = faiss.IndexFlatL2(self.dimension)
        self.faiss_index.add(embeddings)

    def _build_bm25_index(self):
        """Build BM25 index from chunks."""
        tokenized = [chunk.lower().split() for chunk in self.chunks]
        self.bm25_index = BM25Okapi(tokenized)

    def _save_metadata(self):
        """Save index metadata."""
        metadata = {
            "document_id": self.document_id,
            "dimension": self.dimension,
            "chunk_size": self.chunk_size,
            "chunk_count": len(self.chunks),
        }
        with open(self.index_dir / "metadata.pkl", "wb") as f:
            pickle.dump(metadata, f)

    def save(self):
        """Save indices to disk."""
        if self.faiss_index:
            faiss.write_index(self.faiss_index, str(self.index_dir / "faiss.index"))
        if self.bm25_index:
            with open(self.index_dir / "bm25.pkl", "wb") as f:
                pickle.dump(self.bm25_index, f)
        with open(self.index_dir / "chunks.pkl", "wb") as f:
            pickle.dump({"chunks": self.chunks, "chunk_ids": self.chunk_ids}, f)

    def load(self) -> bool:
        """Load indices from disk."""
        try:
            faiss_path = self.index_dir / "faiss.index"
            bm25_path = self.index_dir / "bm25.pkl"
            chunks_path = self.index_dir / "chunks.pkl"

            if faiss_path.exists():
                self.faiss_index = faiss.read_index(str(faiss_path))
            if bm25_path.exists():
                with open(bm25_path, "rb") as f:
                    self.bm25_index = pickle.load(f)
            if chunks_path.exists():
                with open(chunks_path, "rb") as f:
                    data = pickle.load(f)
                    self.chunks = data["chunks"]
                    self.chunk_ids = data["chunk_ids"]

            return bool(self.faiss_index or self.bm25_index)
        except Exception as e:
            logger.error(f"Failed to load indices: {e}")
            return False

    def search(
        self, query_embedding: np.ndarray, query_text: str, k: int = 5
    ) -> List[Dict]:
        """Search this document's index."""
        results = []

        # FAISS search
        if self.faiss_index and self.faiss_index.ntotal > 0:
            query_embedding = query_embedding.reshape(1, -1)
            distances, indices = self.faiss_index.search(
                query_embedding, min(k, self.faiss_index.ntotal)
            )

            for dist, idx in zip(distances[0], indices[0]):
                if idx < len(self.chunks):
                    results.append(
                        {
                            "doc_id": str(self.document_id),
                            "chunk_id": self.chunk_ids[idx],
                            "text": self.chunks[idx],
                            "faiss_score": float(1 / (1 + dist)),
                            "source": "faiss",
                        }
                    )

        # BM25 search
        if self.bm25_index:
            tokenized_query = query_text.lower().split()
            scores = self.bm25_index.get_scores(tokenized_query)

            top_indices = sorted(
                range(len(scores)), key=lambda i: scores[i], reverse=True
            )[:k]

            for idx in top_indices:
                if scores[idx] > 0:
                    results.append(
                        {
                            "doc_id": str(self.document_id),
                            "chunk_id": self.chunk_ids[idx],
                            "text": self.chunks[idx],
                            "bm25_score": float(scores[idx]),
                            "source": "bm25",
                        }
                    )

        return results

    def delete(self):
        """Delete indices from disk."""
        if self.index_dir.exists():
            shutil.rmtree(self.index_dir)


class DynamicSearchEngine:
    """Searches across multiple document indices."""

    def __init__(self, base_path: str = "data_storage/indices"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.embedding_cache: Dict[str, np.ndarray] = {}

    def search(
        self, query: str, document_ids: List[int], top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search across multiple document indices."""
        # Get query embedding
        query_embedding = self._get_embedding(query)

        all_results = []

        # Search each document index in parallel
        with ThreadPoolExecutor(max_workers=min(10, len(document_ids))) as executor:
            futures = {
                executor.submit(
                    self._search_document, doc_id, query_embedding, query, top_k
                ): doc_id
                for doc_id in document_ids
            }

            for future in as_completed(futures):
                try:
                    results = future.result()
                    all_results.extend(results)
                except Exception as e:
                    logger.error(f"Search failed for document: {e}")

        # Apply RRF fusion
        return self._rrf_fusion(all_results, top_k)

    def _search_document(
        self, doc_id: int, query_embedding: np.ndarray, query_text: str, k: int
    ) -> List[Dict]:
        """Search a single document index."""
        index = DocumentIndex(doc_id, str(self.base_path))
        if index.load():
            return index.search(query_embedding, query_text, k)
        return []

    def _get_embedding(self, text: str) -> np.ndarray:
        """Get or create query embedding."""
        cache_key = text[:50]  # Simple cache key

        if cache_key in self.embedding_cache:
            return self.embedding_cache[cache_key]

        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer("all-MiniLM-L6-v2")
        embedding = model.encode([text], convert_to_numpy=True)[0]

        self.embedding_cache[cache_key] = embedding
        return embedding

    def _rrf_fusion(self, results: List[Dict], k: int = 60) -> List[Dict]:
        """Reciprocal Rank Fusion combining FAISS and BM25 results."""
        scores: Dict[str, float] = {}
        doc_map: Dict[str, Dict] = {}

        for result in results:
            doc_id = f"{result['doc_id']}_{result['chunk_id']}"

            # Get score based on source
            score = result.get("faiss_score", 0) or result.get("bm25_score", 0)

            # Track best result for each doc
            if doc_id not in doc_map or score > doc_map[doc_id].get("score", 0):
                doc_map[doc_id] = {**result, "score": score}

            # RRF scoring
            rank = results.index(result) + 1
            rrf_score = score * (1 / (k + rank))
            scores[doc_id] = scores.get(doc_id, 0) + rrf_score

        # Sort by combined score
        sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        # Return top results with full data
        final_results = []
        for doc_id, _ in sorted_docs[:10]:
            result = doc_map[doc_id].copy()
            result["combined_score"] = scores[doc_id]
            final_results.append(result)

        return final_results


class IndexManager:
    """Manages all document indices for a knowledge base."""

    def __init__(self, kb_id: int, base_path: str = "data_storage/indices"):
        self.kb_id = kb_id
        self.base_path = Path(base_path) / str(kb_id)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def create_document_index(self, document_id: int, text: str) -> bool:
        """Create index for a new document."""
        index = DocumentIndex(document_id, str(self.base_path.parent))
        success = index.build(text)
        if success:
            index.save()
        return success

    def search_kb(
        self, query: str, document_ids: List[int], top_k: int = 5
    ) -> List[Dict]:
        """Search across all documents in KB."""
        engine = DynamicSearchEngine(str(self.base_path.parent))
        return engine.search(query, document_ids, top_k)

    def delete_document_index(self, document_id: int):
        """Delete index for a document."""
        index = DocumentIndex(document_id, str(self.base_path.parent))
        index.delete()
