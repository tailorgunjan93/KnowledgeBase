"""Retrieval Worker for FAISS/BM25 search."""

import numpy as np

from ..workers import Worker, Task, TaskResult, WorkerType
from ..retrieval.hybrid_retriever import HybridRetriever


class RetrievalWorker(Worker):
    """Worker for document retrieval."""

    def __init__(self, retriever: HybridRetriever):
        super().__init__(WorkerType.RETRIEVAL)
        self.retriever = retriever

    async def process(self, task: Task) -> TaskResult:
        """Search for relevant documents."""
        try:
            query_embedding = np.array(task.input_data["query_embedding"])
            query_text = task.input_data["query_text"]
            k = task.input_data.get("k", 5)

            results = self.retriever.search(query_embedding, query_text, k)

            return TaskResult(task.task_id, True, {"results": results})
        except Exception as e:
            return TaskResult(task.task_id, False, error=str(e))
