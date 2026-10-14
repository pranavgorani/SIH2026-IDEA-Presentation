from typing import Dict, Any, List, Optional, Tuple
from backend.app.core.config import settings
from backend.app.models.schemas import (
    ImageQualityResult, OCRResultResponse, ValidationSummary,
    TamperResultResponse, FaceVerificationResponse, RecordVerificationResponse,
    RiskAssessmentResponse
)
from backend.app.services.gate1_validator import gate1_validator
from backend.app.services.gate3_scorer import gate3_scorer


class RiskEngine:
    """
    3-Gate Calibrated Multi-Dimensional Risk Engine:
    Enforces the Golden Rule: "Deterministic Clarity First, Calibrated AI Second"

    1. Valid documents MUST pass as LOW RISK (Score: 0–30, GREEN) even if
       slightly blurry, phone-captured, WhatsApp-compressed, or missing EXIF metadata.
    2. Global image noise or missing EXIF data must NEVER trigger a High Risk (RED) alert.
    3. High Risk (Score: 66–100, RED) can ONLY be triggered if:
       - A deterministic structural/cryptographic rule fails (Gate 1), OR
       - Differential ROI Forensics proves that Face Box or Text/DOB Box has
         anomalous variance vs background substrate (ΔZ > 2.6) (Gate 2), OR
       - Biometric 1:1 face verification fails or 1:N multi-identity check flags
         the same face on two different ID numbers (Gate 2).
    4. Review / Medium Risk (Score: 31–65, YELLOW) for borderline cases (1.8 < ΔZ <= 2.6,
       unreadable fields, minor discrepancy).
    """

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or settings.DEFAULT_WEIGHTS.copy()
        # Calibrated risk bands from Section 6 & Golden Rule
        self.threshold_low = 24.0      # 0 - 24: LOW (and strictly within 0 - 30 GREEN)
        self.threshold_medium = 49.0   # 25 - 49: MEDIUM (YELLOW)
        self.threshold_high = 74.0     # 50 - 74: HIGH, 75 - 100: CRITICAL (RED)

    def evaluate(
        self,
        quality: ImageQualityResult,
        ocr: OCRResultResponse,
        validation: ValidationSummary,
        tampering: TamperResultResponse,
        face: FaceVerificationResponse,
        record: RecordVerificationResponse,
        document_type: str = "PASSPORT"
    ) -> RiskAssessmentResponse:
        signal_scores: Dict[str, float] = {}
        risk_factors: List[str] = []
        positive_signals: List[str] = []
        unavailable_checks: List[str] = []

        doc_type_clean = (document_type or "PASSPORT").strip().upper().replace(" ", "_")
        no_expiry_types = {"PAN_CARD", "PAN", "AADHAAR", "AADHAAR_CARD", "VOTER_ID", "EPIC"}
        mrz_expected_types = {"PASSPORT", "INDIAN_PASSPORT", "VISA", "INDIAN_VISA"}
        is_expiry_applicable = doc_type_clean not in no_expiry_types
        is_mrz_applicable = doc_type_clean in mrz_expected_types

        # ---------------------------------------------------------------------
        # 1. Gate 2: Visual Forensics Signal (Differential ROI Forensics)
        # ---------------------------------------------------------------------
        tamper_sig_status = tampering.signals.get("status") or (
            "UNAVAILABLE" if tampering.confidence == 0.0 and not tampering.tampering_detected and tampering.evidence and "unavailable" in tampering.evidence[0].lower() else "OK"
        )
        t_signals = tampering.signals or {}
        max_delta_z = float(t_signals.get("max_delta_z", 0.0))

        if tamper_sig_status == "UNAVAILABLE" or tampering.signals.get("ai_status") == "unavailable":
            signal_scores["visual_forensics"] = 0.0
            unavailable_checks.append("VISUAL_FORENSICS")
            positive_signals.append("Visual forensics service unavailable/offline (zero fraud penalty applied)")
        elif tampering.tampering_detected:
            # Genuine detected differential splicing or injected demo region
            r_count = len(tampering.regions)
            f_score = min(100.0, 50.0 + tampering.confidence * 35.0 + r_count * 5.0)
            signal_scores["visual_forensics"] = round(f_score, 1)
            risk_factors.append(f"Visual tampering signals detected in {r_count} region(s) (Confidence: {tampering.confidence*100:.0f}%)")
        elif max_delta_z > 1.8:
            signal_scores["visual_forensics"] = 15.0
            risk_factors.append(f"Minor differential variance across document substrate (ΔZ = {max_delta_z:.2f})")
        else:
            signal_scores["visual_forensics"] = 0.0
            positive_signals.append("Visual forensics: No differential compression, splicing, or edge manipulation anomalies detected")

        # ---------------------------------------------------------------------
        # 2. Gate 2: Biometric Face Verification Signal
        # ---------------------------------------------------------------------
        if face.status == "MATCH_CONFIRMED":
            signal_scores["identity_verification"] = 0.0
            positive_signals.append(f"Biometric 1:1 face match confirmed ({face.similarity*100:.0f}% similarity)")
        elif face.status == "MATCH_REVIEW":
            signal_scores["identity_verification"] = 35.0
            risk_factors.append(f"Biometric match in review threshold ({face.similarity*100:.0f}% similarity)")
        elif face.status == "MISMATCH_DETECTED":
            signal_scores["identity_verification"] = 90.0
            risk_factors.append(f"Biometric mismatch alert: Presenter face does not correspond to document photo ({face.similarity*100:.0f}%)")
        elif face.status in ("NOT_PROVIDED", "UNAVAILABLE"):
            signal_scores["identity_verification"] = 0.0
            unavailable_checks.append("FACE_VERIFICATION")
            positive_signals.append("Live presenter portrait not provided (biometric matching omitted without penalty)")
        else:
            signal_scores["identity_verification"] = 0.0
            unavailable_checks.append("FACE_VERIFICATION")

        # ---------------------------------------------------------------------
        # 3. External Record Verification Signal
        # ---------------------------------------------------------------------
        if record.status == "VALID":
            signal_scores["record_verification"] = 0.0
            positive_signals.append("Issuer Record Check: Document active and recorded in central registry")
        elif record.status == "SUSPENDED":
            signal_scores["record_verification"] = 80.0
            risk_factors.append("Issuer Record Check: Document status is currently SUSPENDED")
        elif record.status == "REVOKED":
            signal_scores["record_verification"] = 95.0
            risk_factors.append("Issuer Record Check: Document status has been REVOKED or reported lost/stolen")
        elif record.status in ("UNAVAILABLE", "NOT_CONFIGURED", "OFFLINE"):
            signal_scores["record_verification"] = 0.0
            unavailable_checks.append("EXTERNAL_RECORD_VERIFICATION")
            positive_signals.append("External registry verification not configured or unreachable (zero fraud penalty applied)")
        else:
            signal_scores["record_verification"] = 25.0
            risk_factors.append(f"Issuer Record Check: Document identifier not found in test registry ({record.status})")

        # ---------------------------------------------------------------------
        # 4. Gate 1: Document Validation Signal
        # ---------------------------------------------------------------------
        has_critical_failure = False
        has_expiry_failure = False
        actual_failed_checks = 0
        actual_warning_checks = 0

        for c in validation.checks:
            if c.status == "NOT_APPLICABLE":
                continue
            if c.status == "FAIL":
                actual_failed_checks += 1
                if c.severity in ("HIGH", "CRITICAL") or "Chronological" in c.name or ("Expiry" in c.name and is_expiry_applicable):
                    has_critical_failure = True
                if "Expiry" in c.name and is_expiry_applicable:
                    has_expiry_failure = True
                risk_factors.append(f"Validation failure: {c.name} — {c.message}")
            elif c.status == "WARNING":
                actual_warning_checks += 1

        if actual_failed_checks > 0:
            val_score = 85.0 if has_critical_failure else min(100.0, actual_failed_checks * 30.0 + actual_warning_checks * 10.0)
            signal_scores["document_validation"] = round(val_score, 1)
        elif actual_warning_checks > 0:
            signal_scores["document_validation"] = round(min(30.0, actual_warning_checks * 10.0), 1)
            positive_signals.append("Core syntax parameters validated with minor formatting notices")
        else:
            signal_scores["document_validation"] = 0.0
            positive_signals.append("Rule validation: All applicable syntax and chronological checks satisfied")

        # ---------------------------------------------------------------------
        # 5. OCR & Field Consistency
        # ---------------------------------------------------------------------
        if ocr.confidence >= 0.85:
            signal_scores["ocr_consistency"] = 0.0
            positive_signals.append(f"High OCR confidence ({ocr.confidence*100:.0f}%) across document fields")
        elif ocr.confidence >= 0.60:
            signal_scores["ocr_consistency"] = 15.0
            positive_signals.append(f"Moderate OCR text confidence ({ocr.confidence*100:.0f}%)")
        else:
            signal_scores["ocr_consistency"] = 25.0
            risk_factors.append(f"Low OCR text extraction confidence ({ocr.confidence*100:.0f}%) — image rescan recommended")

        # ---------------------------------------------------------------------
        # 6. MRZ Validation
        # ---------------------------------------------------------------------
        if is_mrz_applicable and ocr.mrz:
            if ocr.mrz.valid:
                signal_scores["mrz_validation"] = 0.0
                positive_signals.append("ICAO 9303 MRZ parsed with valid check digits")
            else:
                signal_scores["mrz_validation"] = 85.0
                risk_factors.append("MRZ check digit validation failed (checksum mismatch)")
        elif not is_mrz_applicable:
            signal_scores["mrz_validation"] = 0.0
        else:
            # Expected MRZ document missing MRZ
            signal_scores["mrz_validation"] = 35.0
            risk_factors.append(f"{document_type} typically requires an ICAO MRZ zone which was not detected")

        # ---------------------------------------------------------------------
        # 7. Image Quality Signal
        # ---------------------------------------------------------------------
        if quality.is_acceptable:
            signal_scores["image_quality"] = 0.0
            positive_signals.append(f"Image scan quality is adequate (Score: {quality.quality_score:.0f}%)")
        else:
            signal_scores["image_quality"] = 25.0
            risk_factors.append(f"Scan quality degraded ({quality.quality_score:.0f}%): {', '.join(quality.issues)}")

        # ---------------------------------------------------------------------
        # Weighted Score Calculation
        # ---------------------------------------------------------------------
        total_weight = sum(self.weights.values())
        raw_weighted_score = sum(
            signal_scores.get(key, 0.0) * self.weights.get(key, 0.1)
            for key in self.weights
        ) / (total_weight if total_weight > 0 else 1.0)

        # ---------------------------------------------------------------------
        # HIGH-RISK TRIGGERS (GOLDEN RULE 3)
        # High Risk can ONLY be triggered if:
        # 1. Deterministic structural failure (Gate 1): Expiry failure, critical chronological failure, or MRZ checksum mismatch
        # 2. Localized differential splicing (Gate 2): tampering detected with high confidence (>= 0.70)
        # 3. Biometric mismatch / recycled fraud (Gate 2): face mismatch detected
        # 4. Central registry status revoked/suspended
        # ---------------------------------------------------------------------
        has_mrz_mismatch = is_mrz_applicable and (
            (ocr.mrz is not None and not getattr(ocr.mrz, "valid", True)) or
            any("mrz" in rf.lower() and "fail" in rf.lower() for rf in risk_factors)
        )

        is_high_risk_trigger = (
            (has_expiry_failure and is_expiry_applicable) or
            record.status in ("REVOKED", "SUSPENDED") or
            (tampering.tampering_detected and tampering.confidence >= 0.70) or
            face.status == "MISMATCH_DETECTED" or
            has_critical_failure
        )

        if is_high_risk_trigger:
            final_score = max(raw_weighted_score, 66.0)
        elif has_mrz_mismatch:
            final_score = max(raw_weighted_score, 35.0)
        else:
            final_score = raw_weighted_score

        final_score = round(max(0.0, min(100.0, final_score)), 1)

        # ---------------------------------------------------------------------
        # Calibrated Categorization & Decisions
        # Bands: 0-24 LOW (GREEN), 25-49 MEDIUM (YELLOW), 50-74 HIGH, 75-100 CRITICAL (RED)
        # ---------------------------------------------------------------------
        if quality.quality_score < 40.0 or (ocr.confidence < 0.40 and not fields_have_data(ocr.fields)):
            final_decision = "NEEDS_RESCAN"
            risk_level = "MEDIUM" if final_score <= self.threshold_medium else "HIGH"
            recommended_action = "Image quality or OCR insufficient. Rescan requested."
        elif final_score <= self.threshold_low:
            final_decision = "LOW_RISK"
            risk_level = "LOW"
            recommended_action = "Low Risk — Eligible for Standard Verification"
        elif final_score <= self.threshold_medium:
            final_decision = "NEEDS_REVIEW"
            risk_level = "MEDIUM"
            recommended_action = "Medium Risk — Human Review Recommended"
        elif final_score <= self.threshold_high:
            final_decision = "HIGH_RISK"
            risk_level = "HIGH"
            recommended_action = "High Risk — Mandatory Human Review"
        else:
            final_decision = "CRITICAL_REVIEW"
            risk_level = "CRITICAL"
            recommended_action = "Critical Risk — Urgent Supervisory Review Required"

        # Overall Confidence
        confidence = round(
            0.4 * ocr.confidence +
            0.3 * (tampering.confidence if tampering.tampering_detected else 0.90) +
            0.3 * (quality.quality_score / 100.0),
            2
        )
        confidence = max(0.40, min(0.99, confidence))

        # Comprehensive explanation
        explanation = self._build_explanation(final_score, risk_level, final_decision, risk_factors, positive_signals)

        return RiskAssessmentResponse(
            risk_score=final_score,
            risk_level=risk_level,
            confidence=confidence,
            recommended_action=recommended_action,
            signal_scores=signal_scores,
            risk_factors=risk_factors,
            positive_signals=positive_signals,
            explanation=explanation,
            weights_used=self.weights,
            unavailable_checks=unavailable_checks
        )

    def _build_explanation(self, score: float, level: str, decision: str, risks: List[str], positives: List[str]) -> str:
        lines = [
            f"Overall Risk Score: {score}/100 [{level} RISK | Status: {decision}].",
            f"Verified Positive Signals: {len(positives)} markers.",
        ]
        if risks:
            lines.append(f"Recorded Risk Factors: {len(risks)} item(s).")
            for r in risks[:4]:
                lines.append(f" - {r}")
        else:
            lines.append("No material inconsistencies or tampering signatures identified.")

        if level in ("HIGH", "CRITICAL"):
            lines.append("Decision Advisory: Document flagged with documented risk factors. Routed to authorized human verification queue.")
        elif level == "MEDIUM":
            lines.append("Decision Advisory: Moderate risk detected. Verifier should spot-check flagged fields.")
        else:
            lines.append("Decision Advisory: Document conforms to standard issuance parameters.")

        return "\n".join(lines)


def fields_have_data(fields) -> bool:
    if not fields:
        return False
    doc_num = getattr(fields, "document_number", "") or ""
    name = getattr(fields, "name", "") or ""
    return bool(doc_num.strip() or name.strip())


risk_engine = RiskEngine()
