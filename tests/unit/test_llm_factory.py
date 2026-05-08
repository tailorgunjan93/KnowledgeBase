import pytest
from unittest.mock import patch, MagicMock
from src.services.llm_factory import LLMFactory
from src.shared.exceptions import ExternalServiceError

def test_llm_factory_create_groq():
    with patch('src.services.llm_factory.get_settings') as mock_settings:
        mock_settings.return_value.groq_api_key = 'test_key'
        with patch('src.services.llm_factory.LLMFactory.detect_provider', return_value='groq'):
            # It will instantiate GroqService
            service = LLMFactory.create()
            assert service.__class__.__name__ == 'GroqService'

def test_llm_factory_create_ollama_fallback():
    with patch('src.services.llm_factory.get_settings') as mock_settings:
        mock_settings.return_value.groq_api_key = None
        with patch('src.services.ollama_service.OllamaService.is_available', return_value=True):
            service = LLMFactory.create()
            assert service.__class__.__name__ == 'OllamaService'

def test_llm_factory_create_no_provider():
    with patch('src.services.llm_factory.get_settings') as mock_settings:
        mock_settings.return_value.groq_api_key = None
        with patch('src.services.ollama_service.OllamaService.is_available', return_value=False):
            with pytest.raises(ExternalServiceError):
                LLMFactory.create()

def test_llm_factory_detect_provider():
    with patch('src.services.llm_factory.get_settings') as mock_settings:
        mock_settings.return_value.groq_api_key = 'test_key'
        assert LLMFactory.detect_provider() == 'groq'
        
        mock_settings.return_value.groq_api_key = None
        with patch('src.services.ollama_service.OllamaService.check_available', return_value=True):
            assert LLMFactory.detect_provider() == 'ollama'
            
        with patch('src.services.ollama_service.OllamaService.check_available', return_value=False):
            assert LLMFactory.detect_provider() == 'none'
