"""Builds the correct LLM adapter for a user based on their stored settings."""
import logging
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def get_llm_for_user(user_id: int, db: AsyncSession):
    """Return an LLMPort adapter configured with the user's active provider + key."""
    from src.domain.models import UserSetting
    from src.infrastructure.database.repositories import UserSettingRepository
    from src.core.settings import get_settings

    repo = UserSettingRepository(UserSetting, db)
    settings = get_settings()

    async def _get(key: str, default=None):
        s = await repo.get_by_user_and_key(user_id, key)  # type: ignore[arg-type]
        v = str(s.value).strip() if s and s.value else None
        return v or default

    provider = await _get("active_provider", settings.active_provider or "groq")

    if provider == "openai":
        api_key = await _get("openai_api_key") or settings.openai_api_key
        model = await _get("openai_model") or settings.openai_model
        if not api_key:
            raise ValueError("OpenAI API key not configured. Go to Settings to add one.")
        from .openai_llm_adapter import OpenAILLMAdapter
        return OpenAILLMAdapter(api_key=api_key, model=model)

    if provider == "gemini":
        api_key = await _get("gemini_api_key") or settings.gemini_api_key
        model = await _get("gemini_model") or settings.gemini_model
        if not api_key:
            raise ValueError("Gemini API key not configured. Go to Settings to add one.")
        from .gemini_llm_adapter import GeminiLLMAdapter
        return GeminiLLMAdapter(api_key=api_key, model=model)

    if provider == "nvidia":
        api_key = await _get("nvidia_api_key") or settings.nvidia_api_key
        model = await _get("nvidia_model") or settings.nvidia_model
        if not api_key:
            raise ValueError("NVIDIA API key not configured. Go to Settings to add one.")
        from .nvidia_llm_adapter import NvidiaLLMAdapter
        return NvidiaLLMAdapter(api_key=api_key, model=model)

    if provider == "aws":
        access_key = await _get("aws_access_key_id") or settings.aws_access_key_id
        secret_key = await _get("aws_secret_access_key") or settings.aws_secret_access_key
        region = await _get("aws_region") or settings.aws_region
        model = await _get("aws_model") or settings.aws_model
        if not access_key or not secret_key:
            raise ValueError("AWS credentials not configured. Go to Settings to add them.")
        from .aws_llm_adapter import AWSBedrockLLMAdapter
        return AWSBedrockLLMAdapter(
            access_key_id=access_key,
            secret_access_key=secret_key,
            region=region,
            model=model,
        )

    if provider == "ollama":
        model = await _get("ollama_model") or settings.ollama_model
        from .ollama_llm_adapter import OllamaLLMAdapter
        return OllamaLLMAdapter(base_url=settings.ollama_base_url, model=model)

    # Default: groq
    api_key = await _get("groq_api_key") or settings.groq_api_key
    model = await _get("groq_model") or settings.groq_model
    if not api_key:
        raise ValueError("No LLM provider configured. Go to Settings to add an API key.")
    from .groq_llm_adapter import GroqLLMAdapter
    return GroqLLMAdapter(api_key=api_key, model=model)
