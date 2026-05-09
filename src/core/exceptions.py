class KnowledgeBaseError(Exception):
    """Base exception for this app."""


class DocumentNotFoundError(KnowledgeBaseError):
    def __init__(self, doc_id: str):
        super().__init__(f"Document '{doc_id}' not found.")


class LowConfidenceError(KnowledgeBaseError):
    def __init__(self, score: float):
        super().__init__(f"Answer confidence too low: {score:.2f}")


class VectorStoreError(KnowledgeBaseError):
    pass


class LLMError(KnowledgeBaseError):
    pass
