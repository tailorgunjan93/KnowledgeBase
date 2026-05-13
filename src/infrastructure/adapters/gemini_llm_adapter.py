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

    def chat(self, messages: list[dict], max_tokens: int = 1000) -> str:
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

        response = self._client.models.generate_content(
            model=self._model_name,
            contents=contents,
            config=config,
        )
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

    def embed(self, text: str) -> list[float]:
        raise NotImplementedError("Use SentenceTransformerEmbedder for embeddings.")
