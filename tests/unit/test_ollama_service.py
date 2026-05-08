import pytest
from unittest.mock import patch, MagicMock
from src.services.ollama_service import OllamaService, ChatMessage
from src.shared.exceptions import ExternalServiceError

def test_ollama_service_is_available_true():
    with patch('src.services.ollama_service.OllamaService.check_available', return_value=True):
        service = OllamaService()
        assert service.is_available() is True

def test_ollama_service_is_available_false():
    with patch('src.services.ollama_service.OllamaService.check_available', return_value=False):
        service = OllamaService()
        assert service.is_available() is False

def test_ollama_chat_completion_success():
    with patch('src.services.ollama_service.OllamaService.is_available', return_value=True):
        with patch('httpx.Client') as MockClient:
            mock_client_instance = MockClient.return_value.__enter__.return_value
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"message": {"content": "Test response"}}
            mock_client_instance.post.return_value = mock_response
            
            service = OllamaService()
            messages = [ChatMessage(role="user", content="Hello")]
            response = service.chat_completion(messages)
            assert response == "Test response"

def test_ollama_chat_completion_unavailable():
    with patch('src.services.ollama_service.OllamaService.is_available', return_value=False):
        service = OllamaService()
        messages = [ChatMessage(role="user", content="Hello")]
        with pytest.raises(ExternalServiceError):
            service.chat_completion(messages)
