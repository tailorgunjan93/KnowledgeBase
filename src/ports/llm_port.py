from collections.abc import Iterator
from typing import Protocol


class LLMPort(Protocol):
    """Abstraction over any LLM provider."""

    def chat(self, messages: list[dict], max_tokens: int = 4096) -> str:
        """Send a list of {role, content} messages; return assistant reply."""
        ...

    def chat_stream(self, messages: list[dict], max_tokens: int = 4096) -> Iterator[str]:
        """Send messages and yield chunks of the assistant's reply."""
        ...

    def embed(self, text: str) -> list[float]:
        """Return an embedding vector for the given text."""
        ...
