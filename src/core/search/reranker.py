import logging
from typing import List, Dict, Any
from sentence_transformers import CrossEncoder

logger = logging.getLogger(__name__)

class CrossEncoderReranker:
    """Reranks search results using a Cross-Encoder model."""
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        self._model = None

    @property
    def model(self):
        if self._model is None:
            logger.info(f"Loading Cross-Encoder model: {self.model_name}")
            self._model = CrossEncoder(self.model_name)
        return self._model

    def rerank(self, query: str, items: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Reranks a list of retrieved chunks based on their cross-encoder score.
        """
        if not items:
            return []

        # Prepare pairs for cross-encoder: (query, passage)
        pairs = [[query, item["text"]] for item in items]
        
        # Compute scores
        scores = self.model.predict(pairs)
        
        # Attach scores to items
        for i, score in enumerate(scores):
            items[i]["rerank_score"] = float(score)
            
        # Sort by rerank_score descending
        ranked_items = sorted(items, key=lambda x: x["rerank_score"], reverse=True)
        
        return ranked_items[:top_k]
