class OllamaLLMAdapter:
    """LLMPort implementation for local Ollama server."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.1:8b") -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model

    def chat(self, messages: list[dict], max_tokens: int = 1000) -> str:
        import httpx
        payload = {
            "model": self._model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.3, "num_predict": max_tokens},
        }
        with httpx.Client(timeout=120.0) as client:
            resp = client.post(f"{self._base_url}/api/chat", json=payload)
            resp.raise_for_status()
            content = resp.json().get("message", {}).get("content", "")
        if not content:
            raise ValueError("Ollama returned empty content")
        return content

    def embed(self, text: str) -> list[float]:
        raise NotImplementedError("Use SentenceTransformerEmbedder for embeddings.")
