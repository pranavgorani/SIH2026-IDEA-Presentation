from typing import Optional
from backend.app.core.config import settings
from backend.app.providers.base_provider import AIProvider
from backend.app.providers.local_cv_provider import LocalCVProvider, local_cv_provider
from backend.app.providers.gemini_provider import GeminiVisionHybridProvider, gemini_provider

def get_ai_provider(provider_type: Optional[str] = None) -> AIProvider:
    """
    Returns the configured AI Provider instance.
    Defaults to LocalCVProvider unless GEMINI_VISION_HYBRID is explicitly enabled.
    """
    selected = provider_type or settings.AI_PROVIDER
    if selected == "GEMINI_VISION_HYBRID":
        return gemini_provider
    return local_cv_provider

__all__ = [
    "AIProvider",
    "LocalCVProvider",
    "local_cv_provider",
    "GeminiVisionHybridProvider",
    "gemini_provider",
    "get_ai_provider"
]
