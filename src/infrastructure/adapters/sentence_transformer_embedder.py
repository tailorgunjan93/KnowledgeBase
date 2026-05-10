"""Wrapper around sentence-transformers. Isolate import here."""
from sentence_transformers import SentenceTransformer


class SentenceTransformerEmbedder:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self._model = SentenceTransformer(model_name)

    def embed(self, text: str) -> list[float]:
        result = self._model.encode(text)
        if hasattr(result, 'tolist'):
            result = result.tolist()
        if not result:
            raise ValueError("Embedding model returned empty result")
        return result

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        result = self._model.encode(texts)
        if hasattr(result, 'tolist'):
            result = result.tolist()
        if not result:
            raise ValueError("Embedding model returned empty result")
        return result
