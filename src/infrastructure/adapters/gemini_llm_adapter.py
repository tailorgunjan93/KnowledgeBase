class GeminiLLMAdapter:
    """LLMPort implementation using the Google GenAI SDK (google-genai)."""

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash") -> None:
        try:
            from google import genai
            from google.genai import types as _types
            self._client = genai.Client(api_key=api_key)
            self._types = _types
        except ImportError:
            raise RuntimeError(
                "google-genai not installed: pip install google-genai>=1.0.0"
            )
        self._model_name = model

    def chat(self, messages: list[dict], max_tokens: int = 4096) -> str:
        system_parts = [m["content"] for m in messages if m["role"] == "system"]
        conversation = [m for m in messages if m["role"] != "system"]

        contents = [
            self._types.Content(
                role="user" if m["role"] == "user" else "model",
                parts=[self._types.Part(text=m["content"])],
            )
            for m in conversation
        ]

        config = self._types.GenerateContentConfig(
            max_output_tokens=max_tokens,
            system_instruction="\n".join(system_parts) if system_parts else None,
        )

        try:
            response = self._client.models.generate_content(
                model=self._model_name,
                contents=contents,  # type: ignore[arg-type]
                config=config,
            )
        except Exception as api_err:
            s = str(api_err)
            if "429" in s or "RESOURCE_EXHAUSTED" in s:
                raise ValueError(
                    "Gemini API rate limit exceeded. You have hit your free-tier quota. "
                    "Please wait and try again, or upgrade your Google AI plan at ai.google.dev."
                ) from api_err
            if "401" in s or "403" in s or "API_KEY_INVALID" in s or "UNAUTHENTICATED" in s:
                raise ValueError(
                    "Gemini API key is invalid or expired. "
                    "Go to Settings → Gemini and check your API key."
                ) from api_err
            if "404" in s or "NOT_FOUND" in s:
                raise ValueError(
                    f"Gemini model '{self._model_name}' is not available or has been deprecated. "
                    "Go to Settings → Gemini and select a different model (e.g. gemini-2.0-flash)."
                ) from api_err
            if "503" in s or "UNAVAILABLE" in s:
                raise ValueError(
                    "Gemini service is temporarily unavailable. Please try again in a moment."
                ) from api_err
            raise

        try:
            text = response.text
            if text is not None:
                return text
        except (ValueError, AttributeError):
            pass
        # response.text is None or raised — try extracting from candidates directly
        candidates = response.candidates or []
        if candidates and candidates[0].content and candidates[0].content.parts:
            return candidates[0].content.parts[0].text or ""
        finish = getattr(candidates[0] if candidates else None, "finish_reason", "UNKNOWN")
        raise RuntimeError(
            f"Gemini returned no text content (finish_reason={finish}). "
            "The request may have been blocked by safety filters."
        )

    def chat_stream(self, messages: list[dict], max_tokens: int = 4096):
        system_parts = [m["content"] for m in messages if m["role"] == "system"]
        conversation = [m for m in messages if m["role"] != "system"]

        contents = [
            self._types.Content(
                role="user" if m["role"] == "user" else "model",
                parts=[self._types.Part(text=m["content"])],
            )
            for m in conversation
        ]

        config = self._types.GenerateContentConfig(
            max_output_tokens=max_tokens,
            system_instruction="\n".join(system_parts) if system_parts else None,
        )

        try:
            stream = self._client.models.generate_content_stream(
                model=self._model_name,
                contents=contents,  # type: ignore[arg-type]
                config=config,
            )
            for chunk in stream:
                if chunk.text:
                    yield chunk.text
        except Exception as api_err:
            s = str(api_err)
            if "429" in s or "RESOURCE_EXHAUSTED" in s:
                raise ValueError("Gemini API rate limit exceeded.") from api_err
            if "401" in s or "403" in s or "API_KEY_INVALID" in s or "UNAUTHENTICATED" in s:
                raise ValueError("Gemini API key is invalid or expired.") from api_err
            raise

    def embed(self, text: str) -> list[float]:
        raise NotImplementedError("Use SentenceTransformerEmbedder for embeddings.")
