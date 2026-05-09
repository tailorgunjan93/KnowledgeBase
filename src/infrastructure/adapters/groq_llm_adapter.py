"""Wrapper around the Groq SDK. All Groq imports live here."""
from groq import Groq
from src.ports.llm_port import LLMPort
from src.core.settings import AppSettings


class GroqLLMAdapter:
    """Implements LLMPort using the Groq SDK."""

    def __init__(self, settings: AppSettings) -> None:
        self._client = Groq(api_key=settings.groq_api_key)
        self._model = settings.groq_model  # e.g. "mixtral-8x7b-32768"

    def chat(self, messages: list[dict], max_tokens: int = 1000) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

    def embed(self, text: str) -> list[float]:
        # Groq doesn't embed — delegate to a local sentence-transformer.
        # Keep this here so the rest of the app never knows.
        raise NotImplementedError("Use SentenceTransformerEmbedder for embeddings.")
