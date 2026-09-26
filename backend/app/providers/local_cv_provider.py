from pathlib import Path
from typing import Dict, Any, Optional, List
from backend.app.providers.base_provider import AIProvider
from backend.app.services.image_quality import image_quality_service
from backend.app.services.tamper_detection import tamper_detection_service
from backend.app.services.explainability import explainability_service

class LocalCVProvider(AIProvider):
    """
    Deterministic Local Computer Vision & Document Forensics Engine.
    Uses OpenCV, Error Level Analysis (ELA 95%), 64x64 Noise Grid Variance,
    and rule-based heuristic anomaly detection with zero external dependencies.
    """
    provider_name: str = "LOCAL_CV_FALLBACK"
    provider_status: str = "ACTIVE"

    def analyze_document(self, image_path: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        quality = image_quality_service.analyze(image_path)
        forensics = tamper_detection_service.analyze_document(image_path)

        return {
            "provider": self.provider_name,
            "status": self.provider_status,
            "ai_status": "fallback",
            "provider_status": "LOCAL_FALLBACK",
            "provider_reason": "Processed with Local CV Fallback (AI unavailable)",
            "user_notice": "Processed with Local CV Fallback (AI unavailable)",
            "quality_score": quality.quality_score,
            "quality_issues": quality.issues,
            "tampering_detected": forensics.tampering_detected,
            "forensic_confidence": forensics.confidence,
            "suspicious_regions_count": len(forensics.regions),
            "forensics_signals": forensics.signals,
            "explanation": "Evaluated using deterministic OpenCV Error Level Analysis & local noise variance grids."
        }

    def analyze_visual_anomalies(self, image_path: str) -> Dict[str, Any]:
        path = Path(image_path)
        if not path.exists():
            return {
                "provider": self.provider_name,
                "status": self.provider_status,
                "tampering_detected": False,
                "confidence": 0.0,
                "regions": [],
                "signals": {},
                "heatmap_url": None,
                "note": f"Document scan file not found on disk: {image_path}"
            }
        forensics = tamper_detection_service.analyze_document(image_path)
        return {
            "provider": self.provider_name,
            "status": self.provider_status,
            "tampering_detected": forensics.tampering_detected,
            "confidence": forensics.confidence,
            "regions": [r.dict() for r in forensics.regions],
            "signals": forensics.signals,
            "heatmap_url": forensics.heatmap_url
        }

    def generate_explanation(self, risk_score: float, risk_factors: List[str], positive_signals: List[str]) -> str:
        reasons_text = "; ".join(risk_factors) if risk_factors else "No anomalous risk factors identified"
        signals_text = "; ".join(positive_signals) if positive_signals else "Standard verification baseline"
        return f"Risk Score: {risk_score:.0f}/100. Key Risk Drivers: {reasons_text}. Positive Signals: {signals_text}. (Engine: {self.provider_name})"

local_cv_provider = LocalCVProvider()
