"""Wrapper around the Groq SDK. All Groq imports live here."""
from groq import Groq


class GroqLLMAdapter:
    """Implements LLMPort using the Groq SDK.

    Accepts either a legacy AppSettings object or explicit api_key/model kwargs
    so it can be used both at startup and from the per-request provider factory.
    """

    def __init__(self, settings=None, *, api_key: str = None, model: str = None) -> None:
        resolved_key = api_key or (settings.groq_api_key if settings else None) or ""
        resolved_model = model or (settings.groq_model if settings else "llama-3.1-8b-instant")
        self._client = Groq(api_key=resolved_key)
        self._model = resolved_model

    def chat(self, messages: list[dict], max_tokens: int = 1000) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            max_tokens=max_tokens,
        )
        choices = response.choices if response.choices else []
        if not choices:
            raise ValueError(f"LLM returned no response choices (model={self._model})")
        content = choices[0].message.content
        if content is None:
            raise ValueError("LLM returned empty content")
        return content

    def embed(self, text: str) -> list[float]:
        # Groq doesn't embed — delegate to a local sentence-transformer.
        # Keep this here so the rest of the app never knows.
        raise NotImplementedError("Use SentenceTransformerEmbedder for embeddings.")
