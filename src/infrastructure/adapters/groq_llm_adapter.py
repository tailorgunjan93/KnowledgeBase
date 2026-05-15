"""Wrapper around the Groq SDK. All Groq imports live here."""
from groq import Groq


def _groq_error(err: Exception, model: str) -> ValueError:
    s = str(err)
    if "429" in s or "rate_limit" in s.lower() or "RateLimitError" in type(err).__name__:
        return ValueError(
            "Groq rate limit exceeded. Please wait a moment and try again, "
            "or switch to a less busy model in Settings."
        )
    if "401" in s or "403" in s or "AuthenticationError" in type(err).__name__ or "api_key" in s.lower():
        return ValueError(
            "Groq API key is invalid or expired. Go to Settings → Groq and check your API key."
        )
    if "404" in s or "model_not_found" in s.lower():
        return ValueError(
            f"Groq model '{model}' was not found. Go to Settings → Groq and select a different model."
        )
    if "503" in s or "ServiceUnavailable" in type(err).__name__:
        return ValueError("Groq service is temporarily unavailable. Please try again in a moment.")
    return ValueError(f"Groq API error: {s}")


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

    def chat(self, messages: list[dict], max_tokens: int = 4096) -> str:
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                max_tokens=max_tokens,
            )
        except Exception as err:
            raise _groq_error(err, self._model) from err

        choices = response.choices if response.choices else []
        if not choices:
            raise ValueError(f"Groq returned no response choices (model={self._model})")
        content = choices[0].message.content
        if content is None:
            raise ValueError("Groq returned empty content")
        return content

    def chat_stream(self, messages: list[dict], max_tokens: int = 4096):
        text_so_far = ""
        try:
            stream = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                max_tokens=max_tokens,
                stream=True,
            )
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    delta = chunk.choices[0].delta.content
                    text_so_far += delta
                    yield delta
        except Exception as err:
            # Llama models sometimes try to call tools spontaneously (e.g. when
            # the prompt contains web URLs).  Groq raises an error when no tools
            # are registered.  Fall back to a plain non-streaming call so the
            # user still gets an answer.
            if "called a tool" in str(err).lower():
                if not text_so_far:
                    try:
                        yield self.chat(messages, max_tokens)
                        return
                    except Exception as fallback_err:
                        raise _groq_error(fallback_err, self._model) from fallback_err
                # Already streamed some text — stop gracefully rather than crashing.
                return
            raise _groq_error(err, self._model) from err

    def embed(self, text: str) -> list[float]:
        raise NotImplementedError("Use SentenceTransformerEmbedder for embeddings.")
