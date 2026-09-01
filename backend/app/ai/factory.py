from typing import Optional
from app.ai.base import AIProvider
from app.ai.mock_provider import MockProvider
from app.ai.openai_provider import OpenAIProvider
from app.ai.gemini_provider import GeminiProvider
from app.core.config import settings
from app.core.logging import logger


class AIProviderFactory:
    """Factory to instantiate AI Provider based on configuration or runtime selection."""

    @staticmethod
    def get_provider(provider_type: Optional[str] = None) -> AIProvider:
        p_type = (provider_type or settings.AI_PROVIDER).lower()

        if p_type == "openai":
            if settings.OPENAI_API_KEY:
                return OpenAIProvider()
            logger.warning("OpenAI provider requested but OPENAI_API_KEY is empty. Falling back to MockProvider.")
            return MockProvider()

        elif p_type == "gemini":
            if settings.GEMINI_API_KEY:
                return GeminiProvider()
            logger.warning("Gemini provider requested but GEMINI_API_KEY is empty. Falling back to MockProvider.")
            return MockProvider()

        else:
            return MockProvider()
