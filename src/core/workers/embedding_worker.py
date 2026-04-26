"""Embedding Worker using Sentence Transformers."""

from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer

from ..workers import Worker, Task, TaskResult, WorkerType


class EmbeddingWorker(Worker):
    """Worker for generating text embeddings."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        super().__init__(WorkerType.EMBEDDING)
        self.model_name = model_name
        self.model: SentenceTransformer = None

    async def initialize(self) -> None:
        """Initialize the embedding model."""
        self.model = SentenceTransformer(self.model_name)

    async def process(self, task: Task) -> TaskResult:
        """Generate embeddings for text."""
        try:
            texts = task.input_data.get("texts", [])
            if isinstance(texts, str):
                texts = [texts]

            embeddings = self.model.encode(texts, convert_to_numpy=True)

            return TaskResult(
                task.task_id,
                True,
                {"embeddings": embeddings.tolist(), "shape": embeddings.shape},
            )
        except Exception as e:
            return TaskResult(task.task_id, False, error=str(e))

    async def cleanup(self) -> None:
        """Cleanup model resources."""
        del self.model
        self.model = None
