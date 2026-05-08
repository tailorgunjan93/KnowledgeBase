"""Ollama local LLM service — free alternative when no cloud API subscription."""

from typing import Optional, List
from dataclasses import dataclass
import logging
import httpx

from ..shared.config import get_settings
from ..shared.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    role: str
    content: str


class OllamaService:
    """Local LLM service via Ollama — zero cost, no API key needed."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        settings = get_settings()
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model = model or settings.ollama_model
        self._available: Optional[bool] = None

    def chat_completion(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> str:
        """Generate a chat completion using local Ollama."""
        if not self.is_available():
            raise ExternalServiceError(
                "Ollama is not running. Install from https://ollama.com "
                "and run 'ollama pull llama3.1:8b'"
            )

        payload = {
            "model": model or self.model,
            "messages": [
                {"role": m.role, "content": m.content} for m in messages
            ],
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        try:
            with httpx.Client(timeout=120.0) as client:
                resp = client.post(f"{self.base_url}/api/chat", json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data.get("message", {}).get("content", "")
        except httpx.TimeoutException:
            logger.error("Ollama request timed out")
            raise ExternalServiceError("Local LLM request timed out")
        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama HTTP error: {e}")
            raise ExternalServiceError(f"Local LLM error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            raise ExternalServiceError(f"Local LLM unavailable: {e}")

    def is_available(self) -> bool:
        """Check if Ollama is running locally."""
        if self._available is not None:
            return self._available
        self._available = OllamaService.check_available(self.base_url)
        return self._available

    def is_configured(self) -> bool:
        """Ollama doesn't need configuration — just needs to be running."""
        return self.is_available()

    def list_models(self) -> List[str]:
        """List locally available Ollama models."""
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(f"{self.base_url}/api/tags")
                resp.raise_for_status()
                data = resp.json()
                return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []

    @staticmethod
    def check_available(base_url: str = "http://localhost:11434") -> bool:
        """Check if Ollama server is reachable."""
        try:
            with httpx.Client(timeout=3.0) as client:
                resp = client.get(f"{base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False

    @property
    def provider_name(self) -> str:
        return "ollama"
