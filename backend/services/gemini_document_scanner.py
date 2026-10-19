"""
Gemini Document Scanner module entrypoint.
Proxies to backend.app.services.gemini_document_scanner for consistent modularity.
"""
from backend.app.services.gemini_document_scanner import (
    GeminiDocumentScanner,
    gemini_document_scanner,
    GeminiDocumentScanResult,
    FieldResult,
    VisualObservation,
    LocalizedRegion,
    GeminiMRZInfo,
    QRAnalysisInfo,
    ImageQualityInfo,
    OFFICIAL_GEMINI_MODEL,
    OFFICIAL_THINKING_LEVEL
)

__all__ = [
    "GeminiDocumentScanner",
    "gemini_document_scanner",
    "GeminiDocumentScanResult",
    "FieldResult",
    "VisualObservation",
    "LocalizedRegion",
    "GeminiMRZInfo",
    "QRAnalysisInfo",
    "ImageQualityInfo",
    "OFFICIAL_GEMINI_MODEL",
    "OFFICIAL_THINKING_LEVEL"
]
