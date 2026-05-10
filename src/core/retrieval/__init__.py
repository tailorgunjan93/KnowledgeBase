"""FAISS Vector Store for dense retrieval."""

from typing import List, Dict, Any, Optional
import numpy as np
import faiss
import pickle
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class FAISSStore:
    """FAISS-based vector store."""

    def __init__(self, dimension: int = 384, index_path: Optional[str] = None):
        self.dimension = dimension
        self.index_path = index_path
        self.index: Optional[faiss.Index] = None
        self.documents: List[str] = []
        self.doc_ids: List[str] = []

        if index_path and Path(index_path).exists():
            self.load(index_path)
        else:
            self.index = faiss.IndexFlatL2(dimension)

    def add_documents(
        self,
        texts: List[str],
        embeddings: np.ndarray,
        doc_ids: Optional[List[str]] = None,
    ) -> None:
        """Add documents to the index."""
        if embeddings.shape[1] != self.dimension:
            raise ValueError(
                f"Embedding dimension {embeddings.shape[1]} != {self.dimension}"
            )

        self.index.add(embeddings)
        self.documents.extend(texts)
        self.doc_ids.extend(doc_ids or [str(i) for i in range(len(texts))])

    def search(self, query_embedding: np.ndarray, k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        if self.index.ntotal == 0:
            return []

        query_embedding = query_embedding.reshape(1, -1)
        distances, indices = self.index.search(
            query_embedding, min(k, self.index.ntotal)
        )

        # DEBUG
        import sys
        print(f"DEBUG FAISSStore: ntotal={self.index.ntotal}, k={k}, indices[0]={indices[0].tolist() if len(indices) > 0 else []}, len(docs)={len(self.documents)}, len(doc_ids)={len(self.doc_ids)}", file=sys.stderr)

        results = []
        # Additional safety check before accessing [0]
        if len(distances) == 0 or len(indices) == 0 or len(distances[0]) == 0 or len(indices[0]) == 0:
            return results
            
        for dist, idx in zip(distances[0], indices[0]):
            # FAISS may return -1 for invalid indices when asking for more neighbors than available
            if idx >= 0 and idx < len(self.documents) and idx < len(self.doc_ids):
                results.append(
                    {
                        "doc_id": self.doc_ids[idx],
                        "text": self.documents[idx],
                        "distance": float(dist),
                        "score": float(1 / (1 + dist)),
                    }
                )
            else:
                print(f"DEBUG FAISSStore: SKIPPED idx={idx}, dist={dist}", file=sys.stderr)

        return results

    def save(self, path: str) -> None:
        """Save the index to disk."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, path)
        with open(path + ".docs", "wb") as f:
            pickle.dump({"documents": self.documents, "doc_ids": self.doc_ids}, f)

    def load(self, path: str) -> None:
        """Load the index from disk."""
        self.index = faiss.read_index(path)
        self.dimension = self.index.d
        with open(path + ".docs", "rb") as f:
            data = pickle.load(f)
            self.documents = data["documents"]
            self.doc_ids = data["doc_ids"]
