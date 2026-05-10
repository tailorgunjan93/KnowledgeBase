"""Wrapper around rank_bm25. All BM25 imports live here."""
from rank_bm25 import BM25Okapi


class BM25Adapter:
    def __init__(self) -> None:
        self._corpus_tokens: list[list[str]] = []
        self._corpus_meta: list[dict] = []
        self._index: BM25Okapi | None = None

    def add(self, texts: list[str], metadatas: list[dict]) -> None:
        for text, meta in zip(texts, metadatas):
            self._corpus_tokens.append(text.lower().split())
            self._corpus_meta.append(meta)
        self._index = BM25Okapi(self._corpus_tokens)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        if self._index is None:
            return []
        tokens = query.lower().split()
        scores = self._index.get_scores(tokens)

        ranked = sorted(
            enumerate(scores), key=lambda x: x[1], reverse=True
        )[:top_k]

        results = []
        for i, s in ranked:
            if s > 0 and 0 <= i < len(self._corpus_meta):
                results.append({**self._corpus_meta[i], "score": float(s)})
        return results
