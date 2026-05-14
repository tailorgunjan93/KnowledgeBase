def _nvidia_error(err: Exception, model: str) -> ValueError:
    s = str(err)
    t = type(err).__name__
    if "429" in s or "RateLimitError" in t:
        return ValueError(
            "NVIDIA NIM rate limit exceeded. Please wait and try again."
        )
    if "401" in s or "403" in s or "AuthenticationError" in t:
        return ValueError(
            "NVIDIA API key is invalid or expired. Go to Settings → NVIDIA NIM and check your API key."
        )
    if "404" in s or "NotFoundError" in t:
        return ValueError(
            f"NVIDIA model '{model}' was not found. Go to Settings → NVIDIA NIM and select a different model."
        )
    if "503" in s or "ServiceUnavailableError" in t:
        return ValueError("NVIDIA NIM service is temporarily unavailable. Please try again in a moment.")
    return ValueError(f"NVIDIA NIM API error: {s}")


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

    def chat(self, messages: list[dict], max_tokens: int = 4096) -> str:
        try:
            response = self._client.chat.completions.create(  # type: ignore[call-overload]
                model=self._model,
                messages=messages,
                max_tokens=max_tokens,
            )
        except Exception as err:
            raise _nvidia_error(err, self._model) from err

        choices = response.choices if response.choices else []
        if not choices:
            raise ValueError(f"NVIDIA NIM returned no choices (model={self._model})")
        content = choices[0].message.content
        if content is None:
            raise ValueError("NVIDIA NIM returned empty content")
        return content

    def chat_stream(self, messages: list[dict], max_tokens: int = 4096):
        try:
            stream = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                max_tokens=max_tokens,
                stream=True,
            )
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as err:
            raise _nvidia_error(err, self._model) from err

    def embed(self, text: str) -> list[float]:
        raise NotImplementedError("Use SentenceTransformerEmbedder for embeddings.")
