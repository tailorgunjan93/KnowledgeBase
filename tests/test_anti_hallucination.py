"""Unit tests for anti-hallucination."""

import pytest
from src.core.anti_hallucination import AntiHallucination, SelfCorrector, Source


def test_confidence_high_with_good_sources():
    """Test high confidence with good sources."""
    anti_hallu = AntiHallucination(min_confidence=0.5)

    answer = "Python is a programming language."
    sources = [
        {
            "doc_id": "1",
            "text": "Python is a high-level programming language.",
            "score": 0.9,
        },
        {
            "doc_id": "2",
            "text": "Python supports multiple programming paradigms.",
            "score": 0.8,
        },
    ]

    result = anti_hallu.evaluate(answer, sources)

    assert result.confidence >= 0.5
    assert len(result.sources) == 2


def test_confidence_low_with_poor_sources():
    """Test low confidence with poor sources."""
    anti_hallu = AntiHallucination(min_confidence=0.5)

    answer = "The sky is purple today."
    sources = [
        {"doc_id": "1", "text": "Python is a programming language.", "score": 0.1},
    ]

    result = anti_hallu.evaluate(answer, sources)

    assert result.confidence < 0.5
    assert result.needs_correction is True


def test_confidence_no_sources():
    """Test confidence with no sources."""
    anti_hallu = AntiHallucination(min_confidence=0.5)

    answer = "Some random statement."
    sources = []

    result = anti_hallu.evaluate(answer, sources)

    assert result.confidence == 0.0
    assert result.needs_correction is True


def test_source_attribution():
    """Test source attribution."""
    anti_hallu = AntiHallucination()

    answer = "Python is a programming language."
    sources = [
        {"doc_id": "1", "text": "Python is a programming language.", "score": 0.9}
    ]

    result = anti_hallu.evaluate(answer, sources)

    assert len(result.sources) == 1
    assert result.sources[0].doc_id == "1"
    assert result.sources[0].text == "Python is a programming language."
