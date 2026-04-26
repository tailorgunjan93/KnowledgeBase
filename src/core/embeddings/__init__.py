"""Sentence Transformers Embeddings."""

from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer


class EmbeddingsService:
    """Service for generating text embeddings."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model: SentenceTransformer = None

    def load(self) -> None:
        """Load the embedding model."""
        self.model = SentenceTransformer(self.model_name)

    def encode(self, texts: List[str]) -> np.ndarray:
        """Encode texts to embeddings."""
        if self.model is None:
            self.load()
        return self.model.encode(texts, convert_to_numpy=True)

    def encode_single(self, text: str) -> np.ndarray:
        """Encode a single text."""
        return self.encode([text])[0]

    def get_dimension(self) -> int:
        """Get embedding dimension."""
        if self.model is None:
            self.load()
        return self.model.get_sentence_embedding_dimension()

    def unload(self) -> None:
        """Unload the model."""
        del self.model
        self.model = None
