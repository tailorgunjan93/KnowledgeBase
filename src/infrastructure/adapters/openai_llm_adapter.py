class OpenAILLMAdapter:
    """LLMPort implementation using the OpenAI SDK."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        try:
            from openai import OpenAI
            self._client = OpenAI(api_key=api_key)
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
            raise ValueError(f"OpenAI returned no choices (model={self._model})")
        content = choices[0].message.content
        if content is None:
            raise ValueError("OpenAI returned empty content")
        return content

    def embed(self, text: str) -> list[float]:
        raise NotImplementedError("Use SentenceTransformerEmbedder for embeddings.")
