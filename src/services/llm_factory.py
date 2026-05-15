"""LLM Factory — auto-selects the best available LLM provider.

Priority:
1. Groq API key is set → GroqService (cloud)
2. Ollama is running locally → OllamaService (free, local)
3. Raise helpful error
"""

import logging
from typing import Union

from ..shared.config import get_settings
from ..shared.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)


# Type alias for any LLM service (forward references resolved at runtime)
LLMService = Union["GroqService", "OllamaService"]  # noqa: F821


class LLMFactory:
    """Factory that auto-selects the best available LLM provider."""

    @staticmethod
    def create(
        api_key: str | None = None,
        prefer_local: bool = False,
    ) -> "LLMService":
        """Create the best available LLM service.

        Args:
            api_key: Optional Groq API key override.
            prefer_local: If True, prefer Ollama even when Groq is available.

        Returns:
            GroqService or OllamaService instance.

        Raises:
            ExternalServiceError: If no LLM provider is available.
        """
        from .groq_service import GroqService
        from .ollama_service import OllamaService

        settings = get_settings()
        resolved_key = api_key or settings.groq_api_key

        # If user prefers local, try Ollama first
        if prefer_local:
            ollama = OllamaService()
            if ollama.is_available():
                logger.info("Using local Ollama LLM (user preference)")
                return ollama

        # Priority 1: Groq (cloud)
        if resolved_key:
            logger.info("Using Groq cloud LLM")
            return GroqService(api_key=resolved_key)

        # Priority 2: Ollama (local, free)
        ollama = OllamaService()
        if ollama.is_available():
            logger.info("No Groq API key — using local Ollama LLM (free)")
            return ollama

        # No provider available
        raise ExternalServiceError(
            "No LLM provider available. Either:\n"
            "1. Set GROQ_API_KEY in .env (get free key at https://console.groq.com)\n"
            "2. Install Ollama from https://ollama.com and run 'ollama pull llama3.1:8b'"
        )

    @staticmethod
    def detect_provider(api_key: str | None = None) -> str:
        """Detect which LLM provider would be used.

        Returns:
            'groq', 'ollama', or 'none'
        """
        from .ollama_service import OllamaService

        settings = get_settings()
        resolved_key = api_key or settings.groq_api_key

        if resolved_key:
            return "groq"

        if OllamaService.check_available():
            return "ollama"

        return "none"

    @staticmethod
    def get_provider_info(api_key: str | None = None) -> dict:
        """Get detailed info about available LLM providers."""
        from .ollama_service import OllamaService

        settings = get_settings()
        resolved_key = api_key or settings.groq_api_key

        ollama_available = OllamaService.check_available(
            settings.ollama_base_url
        )
        ollama_models = []
        if ollama_available:
            svc = OllamaService()
            ollama_models = svc.list_models()

        return {
            "active_provider": LLMFactory.detect_provider(api_key),
            "groq": {
                "configured": bool(resolved_key),
                "model": settings.groq_model,
            },
            "ollama": {
                "available": ollama_available,
                "base_url": settings.ollama_base_url,
                "model": settings.ollama_model,
                "installed_models": ollama_models,
            },
        }
