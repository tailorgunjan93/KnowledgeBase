from typing import Protocol

class LLMPort(Protocol):
    """Abstraction over any LLM provider."""

    def chat(self, messages: list[dict], max_tokens: int = 1000) -> str:
        """Send a list of {role, content} messages; return assistant reply."""
        ...

    def embed(self, text: str) -> list[float]:
        """Return an embedding vector for the given text."""
        ...
