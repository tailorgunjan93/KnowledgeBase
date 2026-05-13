class NvidiaLLMAdapter:
    """LLMPort implementation using NVIDIA NIM (OpenAI-compatible API)."""

    BASE_URL = "https://integrate.api.nvidia.com/v1"

    def __init__(self, api_key: str, model: str = "meta/llama-3.1-8b-instruct") -> None:
        try:
            from openai import OpenAI
            self._client = OpenAI(api_key=api_key, base_url=self.BASE_URL)
        except ImportError:
            raise RuntimeError("openai not installed: pip install openai>=1.0.0")
        self._model = model

    def chat(self, messages: list[dict], max_tokens: int = 1000) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            max_tokens=max_tokens,
        )
        choices = response.choices if response.choices else []
        if not choices:
            raise ValueError(f"NVIDIA NIM returned no choices (model={self._model})")
        content = choices[0].message.content
        if content is None:
            raise ValueError("NVIDIA NIM returned empty content")
        return content

    def embed(self, text: str) -> list[float]:
        raise NotImplementedError("Use SentenceTransformerEmbedder for embeddings.")
