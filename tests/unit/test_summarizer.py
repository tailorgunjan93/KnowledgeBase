import pytest
from unittest.mock import patch, MagicMock
from src.core.services.summarizer import Summarizer

def test_summarizer_extract_key_points():
    summarizer = Summarizer()
    summary = "- This is the first long key point that should be extracted.\n- This is the second long key point.\n* And a third one that is also long enough."
    points = summarizer._extract_key_points(summary)
    assert len(points) == 3
    assert points[0] == "This is the first long key point that should be extracted."
    assert points[1] == "This is the second long key point."
    assert points[2] == "And a third one that is also long enough."

def test_summarizer_extract_key_points_fallback():
    summarizer = Summarizer()
    summary = "This is a sentence that is long enough to be a key point. This is another long sentence. Short sentence."
    points = summarizer._extract_key_points(summary)
    assert len(points) == 2
    assert points[0] == "This is a sentence that is long enough to be a key point"
    assert points[1] == "This is another long sentence"

@patch('os.getenv')
def test_summarize_text_with_groq(mock_getenv):
    mock_getenv.return_value = "fake_key"
    summarizer = Summarizer()
    with patch.object(summarizer, '_summarize_with_groq', return_value="This is a test summary that is long enough."):
        res = summarizer.summarize_text("Sample text", api_key="test_key")
        assert res["summary"] == "This is a test summary that is long enough."

@patch('os.getenv')
def test_summarize_text_with_ollama_fallback(mock_getenv):
    mock_getenv.return_value = None
    summarizer = Summarizer()
    with patch.object(summarizer, '_summarize_with_ollama', return_value="This is a local summary that is also long enough."):
        res = summarizer.summarize_text("Sample text", api_key=None)
        assert res["summary"] == "This is a local summary that is also long enough."
