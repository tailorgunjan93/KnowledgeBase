"""Test LangGraph nodes."""

import pytest
from src.core.langgraph.nodes import RAGOrchestrator, IntentType


def test_intent_evaluator_qa():
    """Test QA intent detection."""
    orch = RAGOrchestrator()
    result = orch.process("What is Python?", kb_context={"has_kb": True})
    assert result["intent"] == "qa"
    assert result["intent_confidence"] > 0.5


def test_intent_evaluator_search():
    """Test search intent detection."""
    orch = RAGOrchestrator()
    result = orch.process("Find information about AI", kb_context={"has_kb": False})
    assert result["intent"] == "search"


def test_intent_evaluator_summarize():
    """Test summarize intent detection."""
    orch = RAGOrchestrator()
    result = orch.process("Summarize this document", kb_context={"has_kb": True})
    assert result["intent"] == "summarize"


def test_intent_evaluator_chat():
    """Test chat intent detection."""
    orch = RAGOrchestrator()
    result = orch.process("Hello there!", kb_context={"has_kb": False})
    assert result["intent"] in ["chat", "qa"]


def test_query_evaluator():
    """Test query refinement."""
    orch = RAGOrchestrator()
    result = orch.process("What is Python programming?", kb_context={"has_kb": True})
    assert result["refined_query"] is not None
    assert result["query_valid"] is True


def test_result_evaluator():
    """Test result evaluation."""
    orch = RAGOrchestrator()
    results = [{"text": "Python is a programming language", "score": 0.9}]
    eval_result = orch.evaluate_result(
        results, "Python is a programming language.", "What is Python?"
    )
    assert eval_result.confidence > 0.5
    assert eval_result.is_valid is True
