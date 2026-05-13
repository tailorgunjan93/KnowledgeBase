def _openai_error(err: Exception, model: str) -> ValueError:
    s = str(err)
    t = type(err).__name__
    if "429" in s or "RateLimitError" in t:
        return ValueError(
            "OpenAI rate limit exceeded. Please wait and try again, "
            "or check your usage limits at platform.openai.com."
        )
    if "401" in s or "403" in s or "AuthenticationError" in t:
        return ValueError(
            "OpenAI API key is invalid or expired. Go to Settings → OpenAI and check your API key."
        )
    if "404" in s or "NotFoundError" in t:
        return ValueError(
            f"OpenAI model '{model}' was not found. Go to Settings → OpenAI and select a different model."
        )
    if "503" in s or "ServiceUnavailableError" in t:
        return ValueError("OpenAI service is temporarily unavailable. Please try again in a moment.")
    return ValueError(f"OpenAI API error: {s}")


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
        try:
            response = self._client.chat.completions.create(  # type: ignore[call-overload]
                model=self._model,
                messages=messages,
                max_tokens=max_tokens,
            )
        except Exception as err:
            raise _openai_error(err, self._model) from err

        choices = response.choices if response.choices else []
        if not choices:
            raise ValueError(f"OpenAI returned no choices (model={self._model})")
        content = choices[0].message.content
        if content is None:
            raise ValueError("OpenAI returned empty content")
        return content

    def embed(self, text: str) -> list[float]:
        raise NotImplementedError("Use SentenceTransformerEmbedder for embeddings.")
