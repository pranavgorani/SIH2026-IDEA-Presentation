import re
from typing import Dict, Any, Optional
from PIL import Image

class BaseDocumentClassifier:
    def classify(self, text: str, width: int, height: int, has_mrz: bool = False) -> Dict[str, Any]:
        raise NotImplementedError

class RuleAndHeuristicClassifier(BaseDocumentClassifier):
    """
    Production-grade rule and heuristic classifier using OCR keywords,
    MRZ presence, and ISO document aspect ratio standards.
    """
    PASSPORT_KEYWORDS = ["PASSPORT", "PASSEPORT", "REPUBLIC", "UNITED STATES OF AMERICA", "INDIA", "BRITISH", "DEUTSCHLAND", "P<"]
    VISA_KEYWORDS = ["VISA", "ENTRY PERMIT", "SCHENGEN", "VALID FOR", "MULTIPLE ENTRIES", "SINGLE ENTRY", "NUMBER OF ENTRIES"]
    ID_KEYWORDS = ["IDENTITY CARD", "NATIONAL ID", "IDENTIFICATION", "AADHAAR", "ELECTOR", "RESIDENCE PERMIT", "CITIZEN ID", "CIVIL ID"]
    LICENSE_KEYWORDS = ["DRIVING LICENCE", "DRIVER LICENSE", "DRIVING LICENSE", "PERMIT TO DRIVE", "MOTOR VEHICLE", "CLASS", "DL NO"]
    PERMIT_KEYWORDS = ["WORK PERMIT", "RESIDENCE PERMIT", "EMPLOYMENT AUTHORIZATION", "STAY PERMIT", "BORDER PASS"]
    TRAVEL_AUTH_KEYWORDS = ["TRAVEL AUTHORIZATION", "ESTA", "ELECTRONIC TRAVEL", "BOARDING PASS", "EVUS", "ETA"]

    def classify(self, text: str, width: int, height: int, has_mrz: bool = False) -> Dict[str, Any]:
        text_upper = text.upper()
        scores = {
            "PASSPORT": 0.0,
            "VISA": 0.0,
            "NATIONAL_ID": 0.0,
            "DRIVING_LICENSE": 0.0,
            "PERMIT": 0.0,
            "TRAVEL_AUTHORIZATION": 0.0
        }

        # 1. Keyword Frequency Scoring
        for kw in self.PASSPORT_KEYWORDS:
            if kw in text_upper:
                scores["PASSPORT"] += 2.0
        for kw in self.VISA_KEYWORDS:
            if kw in text_upper:
                scores["VISA"] += 2.0
        for kw in self.ID_KEYWORDS:
            if kw in text_upper:
                scores["NATIONAL_ID"] += 2.0
        for kw in self.LICENSE_KEYWORDS:
            if kw in text_upper:
                scores["DRIVING_LICENSE"] += 2.5
        for kw in self.PERMIT_KEYWORDS:
            if kw in text_upper:
                scores["PERMIT"] += 2.0
        for kw in self.TRAVEL_AUTH_KEYWORDS:
            if kw in text_upper:
                scores["TRAVEL_AUTHORIZATION"] += 2.0

        # 2. MRZ Structural Signal
        if has_mrz:
            if scores["NATIONAL_ID"] > scores["PASSPORT"]:
                scores["NATIONAL_ID"] += 3.0
            else:
                scores["PASSPORT"] += 4.0

        # 3. Aspect Ratio Heuristics (ISO 7810 ID-1 = 1.58, ID-3 = 1.42)
        if height > 0:
            aspect = width / float(height)
            if 1.35 <= aspect <= 1.50: # Typical passport layout
                scores["PASSPORT"] += 0.5
            elif 1.50 <= aspect <= 1.70: # ID card or Driver License
                scores["NATIONAL_ID"] += 0.5
                scores["DRIVING_LICENSE"] += 0.5

        # Best match
        best_doc, best_score = max(scores.items(), key=lambda item: item[1])

        if best_score < 1.0:
            return {
                "document_type": "UNKNOWN",
                "confidence": 0.35,
                "scores": scores,
                "explanation": "No distinct document header or pattern identified. Defaulting to standard scrutiny."
            }

        confidence = min(0.98, max(0.65, round(best_score / (best_score + 1.5), 2)))
        return {
            "document_type": best_doc,
            "confidence": confidence,
            "scores": scores,
            "explanation": f"Document classified as {best_doc} based on key textual markers, layout, and structural features."
        }

class DocumentClassifier:
    """Pluggable facade allowing hot-swapping with future Deep Learning models."""
    def __init__(self, backend: Optional[BaseDocumentClassifier] = None):
        self.backend = backend or RuleAndHeuristicClassifier()

    def classify_document(self, text: str, width: int = 0, height: int = 0, has_mrz: bool = False) -> Dict[str, Any]:
        return self.backend.classify(text=text, width=width, height=height, has_mrz=has_mrz)

document_classifier = DocumentClassifier()
