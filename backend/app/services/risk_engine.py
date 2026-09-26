from typing import Dict, Any, List, Optional, Tuple
from backend.app.core.config import settings
from backend.app.models.schemas import (
    ImageQualityResult, OCRResultResponse, ValidationSummary,
    TamperResultResponse, FaceVerificationResponse, RecordVerificationResponse,
    RiskAssessmentResponse
)

class RiskEngine:
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or settings.DEFAULT_WEIGHTS.copy()
        self.threshold_low = settings.RISK_THRESHOLD_LOW
        self.threshold_medium = settings.RISK_THRESHOLD_MEDIUM

    def evaluate(
        self,
        quality: ImageQualityResult,
        ocr: OCRResultResponse,
        validation: ValidationSummary,
        tampering: TamperResultResponse,
        face: FaceVerificationResponse,
        record: RecordVerificationResponse
    ) -> RiskAssessmentResponse:
        """
        Synthesizes multiple orthogonal screening signals into an explainable 0-100 risk score.
        """
        signal_scores: Dict[str, float] = {}
        risk_factors: List[str] = []
        positive_signals: List[str] = []

        # 1. Visual Forensics Signal (0 = clean, 100 = high suspicion)
        if tampering.tampering_detected:
            # Score proportional to confidence and region count
            r_count = len(tampering.regions)
            f_score = min(100.0, 50.0 + tampering.confidence * 40.0 + r_count * 5.0)
            signal_scores["visual_forensics"] = round(f_score, 1)
            risk_factors.append(f"Visual tampering signals detected in {r_count} region(s) (Confidence: {tampering.confidence*100:.0f}%)")
        else:
            signal_scores["visual_forensics"] = 8.0
            positive_signals.append("Visual forensics: No compression or edge manipulation anomalies detected")

        # 2. Identity / Biometric Face Verification Signal
        if face.status == "MATCH_CONFIRMED":
            signal_scores["identity_verification"] = 10.0
            positive_signals.append(f"Biometric 1:1 face match confirmed ({face.similarity*100:.0f}% similarity)")
        elif face.status == "MATCH_REVIEW":
            signal_scores["identity_verification"] = 45.0
            risk_factors.append(f"Biometric match in review threshold ({face.similarity*100:.0f}% similarity)")
        elif face.status == "MISMATCH_DETECTED":
            signal_scores["identity_verification"] = 88.0
            risk_factors.append(f"Biometric mismatch alert: Presenter face does not correspond to document photo ({face.similarity*100:.0f}%)")
        else: # UNAVAILABLE
            # If no live face provided, default to moderate baseline risk factor
            signal_scores["identity_verification"] = 25.0
            risk_factors.append("Biometric face verification unavailable (no live selfie submitted)")

        # 3. Record Verification Signal
        if record.status == "VALID":
            signal_scores["record_verification"] = 5.0
            positive_signals.append("Issuer Record Check: Document active and recorded in simulated central database")
        elif record.status == "SUSPENDED":
            signal_scores["record_verification"] = 75.0
            risk_factors.append("Issuer Record Check: Document status is currently SUSPENDED")
        elif record.status == "REVOKED":
            signal_scores["record_verification"] = 95.0
            risk_factors.append("Issuer Record Check: Document status has been REVOKED or reported lost/stolen")
        else:
            signal_scores["record_verification"] = 40.0
            risk_factors.append(f"Issuer Record Check: Document number not found in simulated database ({record.status})")

        # 4. Document Validation Signal
        has_critical_failure = False
        has_expiry_failure = False
        if validation.failed_count > 0:
            for c in validation.checks:
                if c.status == "FAIL":
                    if c.severity in ("HIGH", "CRITICAL") or "Expiry" in c.name or "Chronological" in c.name:
                        has_critical_failure = True
                    if "Expiry" in c.name:
                        has_expiry_failure = True
                    risk_factors.append(f"Validation failure: {c.name} — {c.message}")

            val_score = 92.0 if has_critical_failure else min(100.0, validation.failed_count * 45.0 + validation.warning_count * 15.0)
            signal_scores["document_validation"] = round(val_score, 1)
        else:
            signal_scores["document_validation"] = 5.0
            positive_signals.append(f"Rule validation: All {validation.passed_count} syntax and chronological checks passed")

        # 5. OCR & Field Consistency
        if ocr.confidence >= 0.85:
            signal_scores["ocr_consistency"] = 8.0
            positive_signals.append(f"High OCR confidence ({ocr.confidence*100:.0f}%) across document fields")
        elif ocr.confidence >= 0.60:
            signal_scores["ocr_consistency"] = 35.0
            risk_factors.append(f"Moderate OCR text confidence ({ocr.confidence*100:.0f}%)")
        else:
            signal_scores["ocr_consistency"] = 70.0
            risk_factors.append(f"Low OCR text extraction confidence ({ocr.confidence*100:.0f}%)")

        # 6. MRZ Validation
        if ocr.mrz:
            if ocr.mrz.valid:
                signal_scores["mrz_validation"] = 5.0
                positive_signals.append("ICAO 9303 MRZ parsed with valid check digits")
            else:
                signal_scores["mrz_validation"] = 85.0
                risk_factors.append("MRZ check digit validation failed (checksum mismatch)")
        else:
            signal_scores["mrz_validation"] = 20.0

        # 7. Image Quality Signal
        if quality.is_acceptable:
            q_risk = max(5.0, 100.0 - quality.quality_score)
            signal_scores["image_quality"] = round(q_risk, 1)
            positive_signals.append(f"Image scan quality is adequate (Score: {quality.quality_score:.0f}%)")
        else:
            signal_scores["image_quality"] = 65.0
            risk_factors.append(f"Low scan quality ({quality.quality_score:.0f}%): {', '.join(quality.issues)}")

        # Weighted Score Calculation
        total_weight = sum(self.weights.values())
        raw_weighted_score = sum(
            signal_scores.get(key, 20.0) * self.weights.get(key, 0.1)
            for key in self.weights
        ) / (total_weight if total_weight > 0 else 1.0)

        # Domain Safety Overrides:
        # High-risk triggers: Expired document, Revoked record, High-confidence tampering, or Biometric Mismatch
        if has_expiry_failure or record.status in ("REVOKED", "SUSPENDED") or (tampering.tampering_detected and tampering.confidence >= 0.85) or face.status == "MISMATCH_DETECTED":
            final_score = max(raw_weighted_score, 68.0)
        elif not tampering.tampering_detected and validation.valid and record.status == "VALID" and not has_critical_failure and ocr.confidence >= 0.80:
            final_score = min(raw_weighted_score, 24.0)
        else:
            final_score = raw_weighted_score

        final_score = round(max(0.0, min(100.0, final_score)), 1)

        # Categorization based on prompt's exact safety guidelines
        if final_score <= self.threshold_low:
            risk_level = "LOW"
            recommended_action = "Low Risk — Eligible for Standard Verification"
        elif final_score <= self.threshold_medium:
            risk_level = "MEDIUM"
            recommended_action = "Medium Risk — Human Review Recommended"
        else:
            risk_level = "HIGH"
            recommended_action = "High Risk — Mandatory Human Review"

        # Overall Confidence
        confidence = round(
            0.4 * ocr.confidence +
            0.3 * tampering.confidence +
            0.3 * (quality.quality_score / 100.0),
            2
        )
        confidence = max(0.50, min(0.98, confidence))

        # Comprehensive explanation
        explanation = self._build_explanation(final_score, risk_level, risk_factors, positive_signals)

        return RiskAssessmentResponse(
            risk_score=final_score,
            risk_level=risk_level,
            confidence=confidence,
            recommended_action=recommended_action,
            signal_scores=signal_scores,
            risk_factors=risk_factors,
            positive_signals=positive_signals,
            explanation=explanation,
            weights_used=self.weights
        )

    def _build_explanation(self, score: float, level: str, risks: List[str], positives: List[str]) -> str:
        lines = [
            f"Overall Risk Score: {score}/100 [{level} RISK].",
            f"Key Positive Signals: {len(positives)} verified markers.",
        ]
        if risks:
            lines.append(f"Key Risk Factors Detected: {len(risks)} anomalies requiring attention.")
            for r in risks[:3]:
                lines.append(f" - {r}")
        else:
            lines.append("No critical inconsistencies or tampering signatures identified.")

        if level == "HIGH":
            lines.append("Decision Advisory: In accordance with MHA AI-Assisted Screening Protocols, AI cannot make punitive rejections. Case routed to human verifier queue for manual forensic confirmation.")
        elif level == "MEDIUM":
            lines.append("Decision Advisory: Moderate risk detected. Verifier should spot-check flagged fields.")
        else:
            lines.append("Decision Advisory: Document conforms to standard issuance parameters.")

        return "\n".join(lines)

risk_engine = RiskEngine()
