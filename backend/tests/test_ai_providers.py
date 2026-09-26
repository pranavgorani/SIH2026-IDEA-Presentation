"""
TRUST-ID SIH 2026 - AI Provider Tests
Validates LocalCVProvider, GeminiVisionHybridProvider fallback behavior,
and zero-crash resilience when GEMINI_API_KEY is unconfigured or unavailable.
"""

import pytest
from backend.app.providers.base_provider import AIProvider
from backend.app.providers.local_cv_provider import LocalCVProvider, local_cv_provider
from backend.app.providers.gemini_provider import GeminiVisionHybridProvider
from backend.app.providers import get_ai_provider


def test_local_cv_provider_interface():
    provider = LocalCVProvider()
    assert isinstance(provider, AIProvider)
    assert provider.provider_name == "LOCAL_CV_FALLBACK"

    # Test explanation generation without LLM
    explanation = provider.generate_explanation(
        risk_score=75.0,
        risk_factors=["MRZ check digit mismatch", "Font inconsistency"],
        positive_signals=["Valid document format"]
    )
    assert isinstance(explanation, str)
    assert "Risk Score: 75/100" in explanation
    assert "LOCAL_CV_FALLBACK" in explanation


def test_gemini_provider_fallback_when_unconfigured(monkeypatch):
    # Ensure GEMINI_API_KEY is absent
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    provider = GeminiVisionHybridProvider()

    assert provider.is_configured is False
    assert provider.provider_name == "GEMINI_VISION_HYBRID"

    # Should gracefully return local fallback status without crashing
    result = provider.analyze_document("nonexistent_path.jpg")
    assert result["provider_status"] == "LOCAL_FALLBACK"
    assert result["explanation"] == "Gemini provider unavailable; local computer-vision analysis used."
    assert "quality_score" in result

    # Visual anomalies should also indicate local fallback
    anomalies = provider.analyze_visual_anomalies("nonexistent_path.jpg")
    assert anomalies["provider_status"] == "LOCAL_FALLBACK"
    assert anomalies["explanation"] == "Gemini provider unavailable; local computer-vision analysis used."

    # Should generate fallback explanation safely
    explanation = provider.generate_explanation(
        risk_score=85.0,
        risk_factors=["Critical expiry mismatch"],
        positive_signals=[]
    )
    assert "Risk Score: 85/100" in explanation


def test_gemini_provider_with_dummy_key_handles_api_failure(monkeypatch):
    # Dummy key (not a real key) to test network/API failure fallback
    monkeypatch.setenv("GEMINI_API_KEY", "dummy_test_key_for_unit_tests")
    provider = GeminiVisionHybridProvider()
    assert provider.is_configured is True

    # Calling analyze_document with missing/failing file should not crash; falls back gracefully
    result = provider.analyze_document("nonexistent_test_doc.jpg")
    assert result["provider_status"] == "LOCAL_FALLBACK"
    assert result["explanation"] == "Gemini provider unavailable; local computer-vision analysis used."


def test_get_ai_provider_factory(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER_MODE", "LOCAL_CV_FALLBACK")
    p1 = get_ai_provider("LOCAL_CV_FALLBACK")
    assert isinstance(p1, LocalCVProvider)

    p2 = get_ai_provider("GEMINI_VISION_HYBRID")
    assert isinstance(p2, GeminiVisionHybridProvider)
