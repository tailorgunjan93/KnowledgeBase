import logging
from dataclasses import dataclass

from groq import Groq
from groq import RateLimitError as GroqRateLimitError

from ..shared.config import get_settings
from ..shared.exceptions import ExternalServiceError, RateLimitError

logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    role: str
    content: str


class GroqService:
    def __init__(self, api_key: str | None = None):
        settings = get_settings()
        self.api_key = api_key or settings.groq_api_key
        self.model = settings.groq_model
        self.client = Groq(api_key=self.api_key) if self.api_key else None

    def chat_completion(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 1024
    ) -> str:
        if not self.client:
            raise ExternalServiceError("GROQ_API_KEY not configured")

        try:
            response = self.client.chat.completions.create(
                model=model or self.model,
                messages=[{"role": m.role, "content": m.content} for m in messages],
                temperature=temperature,
                max_tokens=max_tokens
            )
            if not response.choices:
                raise ExternalServiceError("LLM returned no response choices")
            return response.choices[0].message.content
        except GroqRateLimitError:
            logger.warning("Groq rate limit hit")
            raise RateLimitError("Rate limit exceeded, please try again later")
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise ExternalServiceError("LLM service unavailable")

    def is_configured(self) -> bool:
        return bool(self.api_key)
