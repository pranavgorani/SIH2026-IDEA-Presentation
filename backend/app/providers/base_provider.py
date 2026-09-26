from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

class AIProvider(ABC):
    """
    Common abstraction for TRUST-ID AI and Computer Vision Providers.
    Supports pluggable local heuristics or multimodal cloud foundation models
    with seamless fallback guarantees.
    """
    provider_name: str
    provider_status: str

    @abstractmethod
    def analyze_document(self, image_path: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Comprehensive document assessment combining visual classification,
        structural integrity, and anomaly cues.
        """
        pass

    @abstractmethod
    def analyze_visual_anomalies(self, image_path: str) -> Dict[str, Any]:
        """
        Specialized forensic scan for image tampering, photo substitution,
        typography alterations, and compression inconsistencies.
        """
        pass

    @abstractmethod
    def generate_explanation(self, risk_score: float, risk_factors: List[str], positive_signals: List[str]) -> str:
        """
        Generates explainable human-readable verification rationale
        grounded in detected signals.
        """
        pass
