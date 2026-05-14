class OllamaLLMAdapter:
    """LLMPort implementation for local Ollama server."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.1:8b") -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model

    def chat(self, messages: list[dict], max_tokens: int = 4096) -> str:
        import httpx
        payload = {
            "model": self._model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.3, "num_predict": max_tokens},
        }
        try:
            with httpx.Client(timeout=120.0) as client:
                resp = client.post(f"{self._base_url}/api/chat", json=payload)
                if resp.status_code == 404:
                    raise ValueError(
                        f"Ollama model '{self._model}' is not installed. "
                        f"Run: ollama pull {self._model}"
                    )
                if resp.status_code == 503 or resp.status_code == 500:
                    raise ValueError(
                        "Ollama server returned an error. Make sure Ollama is running: ollama serve"
                    )
                resp.raise_for_status()
        except httpx.ConnectError:
            raise ValueError(
                f"Cannot connect to Ollama at {self._base_url}. "
                "Make sure Ollama is running: ollama serve"
            )
        except httpx.TimeoutException:
            raise ValueError(
                f"Ollama request timed out for model '{self._model}'. "
                "The model may be loading — please try again in a moment."
            )
        except ValueError:
            raise
        except Exception as err:
            raise ValueError(f"Ollama error: {err}") from err

        content = resp.json().get("message", {}).get("content", "")
        if not content:
            raise ValueError("Ollama returned empty content")
        return content

    def chat_stream(self, messages: list[dict], max_tokens: int = 4096):
        import httpx
        import json
        payload = {
            "model": self._model,
            "messages": messages,
            "stream": True,
            "options": {"temperature": 0.3, "num_predict": max_tokens},
        }
        try:
            with httpx.stream("POST", f"{self._base_url}/api/chat", json=payload, timeout=120.0) as resp:
                if resp.status_code != 200:
                    raise ValueError(f"Ollama error (status {resp.status_code})")
                for line in resp.iter_lines():
                    if line:
                        chunk = json.loads(line)
                        content = chunk.get("message", {}).get("content", "")
                        if content:
                            yield content
        except Exception as err:
            raise ValueError(f"Ollama streaming error: {err}") from err

    def embed(self, text: str) -> list[float]:
        raise NotImplementedError("Use SentenceTransformerEmbedder for embeddings.")
