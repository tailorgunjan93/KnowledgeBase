"""Unit tests for retrieval."""

import pytest
import numpy as np
from src.core.retrieval import FAISSStore
from src.core.retrieval.bm25_store import BM25Store
from src.core.retrieval.hybrid_retriever import HybridRetriever


def test_faiss_store_add_and_search():
    """Test FAISS store add and search."""
    store = FAISSStore(dimension=4)

    texts = ["hello world", "python programming", "machine learning"]
    embeddings = np.array(
        [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0]]
    )

    store.add_documents(texts, embeddings, ["1", "2", "3"])

    query_embedding = np.array([1.0, 0.1, 0.0, 0.0])
    results = store.search(query_embedding, k=2)

    assert len(results) == 2
    assert results[0]["doc_id"] == "1"


def test_bm25_store_add_and_search():
    """Test BM25 store add and search."""
    store = BM25Store()

    texts = ["hello world", "python programming", "machine learning"]
    store.add_documents(texts, ["1", "2", "3"])

    results = store.search("python programming", k=2)

    assert len(results) > 0
    assert any(r["doc_id"] in ["2", "3"] for r in results)


def test_hybrid_retriever():
    """Test hybrid retriever."""
    faiss_store = FAISSStore(dimension=4)
    bm25_store = BM25Store()

    texts = ["hello world", "python programming", "machine learning"]
    embeddings = np.array(
        [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0]]
    )

    faiss_store.add_documents(texts, embeddings, ["1", "2", "3"])
    bm25_store.add_documents(texts, ["1", "2", "3"])

    retriever = HybridRetriever(faiss_store, bm25_store, alpha=0.5)

    query_embedding = np.array([1.0, 0.0, 0.0, 0.0])
    results = retriever.search(query_embedding, "hello world", k=2)

    assert len(results) <= 2
    assert results[0]["doc_id"] == "1"
