"""BM25 Store for keyword-based retrieval."""

from typing import List, Dict, Any
from rank_bm25 import BM25Okapi
import pickle
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class BM25Store:
    """BM25-based keyword store."""

    def __init__(self, index_path: str = None):
        self.index_path = index_path
        self.bm25: BM25Okapi = None
        self.documents: List[str] = []
        self.doc_ids: List[str] = []

        if index_path and Path(index_path).exists():
            self.load(index_path)

    def add_documents(self, texts: List[str], doc_ids: List[str] = None) -> None:
        """Add documents to the index."""
        self.documents = texts
        self.doc_ids = doc_ids or [str(i) for i in range(len(texts))]

        tokenized_docs = [doc.lower().split() for doc in texts]
        self.bm25 = BM25Okapi(tokenized_docs)

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant documents."""
        if not self.bm25:
            return []

        tokenized_query = query.lower().split()
        scores = self.bm25.get_scores(tokenized_query)

        # DEBUG: Log array sizes
        import sys
        print(f"DEBUG BM25Store: len(documents)={len(self.documents)}, len(doc_ids)={len(self.doc_ids)}, len(scores)={len(scores)}, k={k}", file=sys.stderr)

        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[
            :k
        ]

        print(f"DEBUG BM25Store: top_indices={top_indices}", file=sys.stderr)

        results = []
        for idx in top_indices:
            # Check bounds FIRST, then access scores[idx]
            if 0 <= idx < len(scores) and scores[idx] > 0 and 0 <= idx < len(self.documents) and 0 <= idx < len(self.doc_ids):
                results.append(
                    {
                        "doc_id": self.doc_ids[idx],
                        "text": self.documents[idx],
                        "score": float(scores[idx]),
                    }
                )
            else:
                print(f"DEBUG BM25Store: SKIPPED idx={idx}, len(scores)={len(scores)}, len(docs)={len(self.documents)}", file=sys.stderr)

        return results

    def save(self, path: str) -> None:
        """Save the index to disk."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(
                {
                    "bm25": self.bm25,
                    "documents": self.documents,
                    "doc_ids": self.doc_ids,
                },
                f,
            )

    def load(self, path: str) -> None:
        """Load the index from disk."""
        with open(path, "rb") as f:
            data = pickle.load(f)
            self.bm25 = data["bm25"]
            self.documents = data["documents"]
            self.doc_ids = data["doc_ids"]
