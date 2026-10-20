"""
TRUST-ID Gate 3: Calibrated Multi-Gate Risk Scorer
Enforces the Golden Architectural Rule: "Deterministic Clarity First, Calibrated AI Second"

1. Valid documents MUST pass as LOW RISK (Score: 0–30, GREEN) even if slightly blurry,
   phone-captured, WhatsApp-compressed, or missing EXIF metadata.
2. Global image noise or missing EXIF data must NEVER trigger a High Risk (RED) alert.
3. High Risk (Score: 66–100, RED) can ONLY be triggered if:
   - A deterministic structural/cryptographic rule fails (Gate 1), OR
   - Differential ROI Forensics proves Face Box or Text/DOB Box has ΔZ > 2.6 (Gate 2), OR
   - Biometric 1:1 face verification fails (< 0.45) or 1:N multi-identity check flags
     the same face on two different ID numbers (Gate 2).
4. Review / Medium Risk (Score: 31–65, YELLOW) for borderline cases (1.8 < ΔZ <= 2.6,
   unreadable fields, minor discrepancy).
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone


class CalibratedGate3Scorer:
    """
    Gate 3: Multi-Gate Decision & Calibrated Risk Scoring Engine.
    Fuses Gate 1 (Deterministic Clarity), Gate 2 (Differential Forensics & Biometrics),
    and Document Quality while strictly preserving the Golden Rule.
    """

    # Calibrated Operational Bands conforming to Golden Rule
    SCORE_LOW_MAX = 24.0       # 0 - 24: LOW RISK (GREEN, strictly <= 30)
    SCORE_MEDIUM_MAX = 49.0    # 25 - 49: MEDIUM RISK / NEEDS REVIEW (YELLOW)
    SCORE_HIGH_MIN = 66.0      # 66 - 100: HIGH RISK / FRAUD SUSPECT (RED)

    def evaluate_multi_gate(
        self,
        gate1_result: Dict[str, Any],
        gate2_result: Dict[str, Any],
        image_quality_data: Optional[Dict[str, Any]] = None,
        record_verification_data: Optional[Dict[str, Any]] = None,
        ocr_confidence: float = 0.90
    ) -> Dict[str, Any]:
        """
        Fuses Gate 1, Gate 2, Quality, and External Records under Golden Rule invariants.
        """
        gate1_passed = bool(gate1_result.get("gate1_passed", False))
        structural_valid = bool(gate1_result.get("structural_valid", False))
        trust_bonus = int(gate1_result.get("trust_bonus", 0))
        failed_gate1_rules = list(gate1_result.get("failed_rules", []))
        passed_gate1_rules = list(gate1_result.get("passed_rules", []))

        gate2_passed = bool(gate2_result.get("gate2_passed", True))
        splicing_detected = bool(gate2_result.get("splicing_detected", False))
        max_delta_z = float(gate2_result.get("max_delta_z", 0.0))
        delta_z_face = float(gate2_result.get("delta_z_face", 0.0))
        delta_z_text = float(gate2_result.get("delta_z_text", 0.0))

        bio_1to1 = gate2_result.get("biometrics_1to1", {})
        bio_1toN = gate2_result.get("biometrics_1toN", {})

        bio_mismatch = bio_1to1.get("status") == "MISMATCH_DETECTED"
        recycled_fraud = bool(bio_1toN.get("recycled_fraud_detected", False))

        rec_data = record_verification_data or {}
        rec_status = rec_data.get("status", "NOT_VERIFIED")
        record_revoked = rec_status in ("REVOKED", "SUSPENDED")

        q_data = image_quality_data or {}
        q_score = float(q_data.get("quality_score", 90.0))

        risk_factors: List[str] = []
        positive_signals: List[str] = []

        # =====================================================================
        # EVALUATE HIGH-RISK TRIGGERS (ONLY GATES 1 & 2 CAN TRIGGER HIGH RISK)
        # =====================================================================
        high_risk_triggered = False
        trigger_reasons: List[str] = []

        # 1. Deterministic Structural Failure (Gate 1)
        doc_type_clean = str(gate1_result.get("doc_type") or gate1_result.get("document_type") or "").upper()
        is_unknown_or_unsupported = doc_type_clean in ("UNKNOWN", "UNSUPPORTED", "GENERIC_ID")
        if not structural_valid and len(failed_gate1_rules) > 0 and not is_unknown_or_unsupported:
            high_risk_triggered = True
            trigger_reasons.append("Gate 1 Deterministic Structural Failure")
            for fr in failed_gate1_rules:
                risk_factors.append(f"Gate 1 Rule Failed: {fr}")

        # 2. Localized Splicing (Gate 2: ΔZ > 2.6)
        if splicing_detected or max_delta_z > 2.6:
            high_risk_triggered = True
            trigger_reasons.append(f"Gate 2 Localized Splicing Detected (ΔZ = {max_delta_z:.2f} > 2.6)")
            risk_factors.append(f"Differential Forensics: Statistically anomalous ROI variance (ΔZ = {max_delta_z:.2f})")

        # 3. Biometric Verification Mismatch / Recycled Identity
        if bio_mismatch:
            high_risk_triggered = True
            trigger_reasons.append(f"Gate 2 Biometric Mismatch ({bio_1to1.get('similarity', 0.0)*100:.1f}%)")
            risk_factors.append("Biometric 1:1 face mismatch between document portrait and presenter selfie")

        if recycled_fraud:
            high_risk_triggered = True
            trigger_reasons.append("Gate 2 1:N Recycled Biometric Identity Fraud")
            for ev in bio_1toN.get("evidence", []):
                risk_factors.append(ev)

        # 4. Official Issuer Revocation
        if record_revoked:
            high_risk_triggered = True
            trigger_reasons.append(f"Official Registry Status: {rec_status}")
            risk_factors.append(f"Credential status is {rec_status} in official registry")

        # =====================================================================
        # SCORE CALIBRATION ACCORDING TO GOLDEN RULE
        # =====================================================================
        if high_risk_triggered:
            # High Risk Band: 66 - 100 (RED)
            base_high = 68.0
            if not structural_valid:
                base_high += 12.0
            if splicing_detected:
                base_high += 10.0
            if bio_mismatch or recycled_fraud:
                base_high += 10.0
            final_score = min(100.0, max(self.SCORE_HIGH_MIN, base_high))
            risk_level = "HIGH"
            badge_color = "RED"
            decision = "HIGH_RISK"
            action = "Mandatory Human Review / Forensic Audit"

        elif gate1_passed and max_delta_z <= 1.8:
            # GOLDEN RULE 1:
            # Valid documents MUST pass as LOW RISK (Score: 0 - 30, GREEN)
            # even if slightly blurry, phone-captured, WhatsApp-compressed, or missing EXIF metadata.
            forensic_penalty = min(10.0, max_delta_z * 5.0)

            # Quality blur penalty: max 10 pts, only if severely blurred
            quality_penalty = 0.0
            if q_score < 60.0:
                quality_penalty = min(10.0, (60.0 - q_score) * 0.25)
                risk_factors.append(f"Minor phone capture blur (Score: {q_score:.0f}%), verified genuine")

            # Trust bonus credit reduces risk points
            bonus_credit = trust_bonus * 0.3

            raw_score = max(0.0, forensic_penalty + quality_penalty - bonus_credit)
            # Strictly bounded within [0, 24] (GREEN, LOW RISK)
            final_score = max(0.0, min(self.SCORE_LOW_MAX, raw_score))
            risk_level = "LOW"
            badge_color = "GREEN"
            decision = "LOW_RISK"
            action = "Eligible for Instant Automated Clearance"

            positive_signals.append("Gate 1 Structural Baseline Passed: Mathematical integrity confirmed")
            positive_signals.append(f"Gate 2 Differential Forensics Clean (ΔZ = {max_delta_z:.2f} <= 1.8)")
            for pr in passed_gate1_rules[:3]:
                positive_signals.append(pr)

        else:
            # Borderline / Needs Review Band: 25 - 49 (YELLOW)
            # 1.8 < ΔZ <= 2.6, or unreadable fields without fraudulent intent
            base_medium = 25.0
            if max_delta_z > 1.8:
                base_medium += (max_delta_z - 1.8) * 15.0
                risk_factors.append(f"Differential Forensics: Minor variance across regions (ΔZ = {max_delta_z:.2f})")
            if not structural_valid and len(failed_gate1_rules) == 0:
                base_medium += 8.0
                risk_factors.append("Field unreadable or absent from document face")
            if ocr_confidence < 0.65:
                base_medium += 6.0
                risk_factors.append("Low OCR confidence; manual field spot-check required")

            final_score = min(self.SCORE_MEDIUM_MAX, max(25.0, base_medium))
            risk_level = "MEDIUM"
            badge_color = "YELLOW"
            decision = "NEEDS_REVIEW"
            action = "Secondary Review Required — Inspect Flagged Fields"

        final_score = round(final_score, 1)

        # Audit Breakdown adhering to Section 4
        gate_summary = {
            "gate1": {
                "name": "Deterministic Clarity Engine",
                "status": "PASSED" if gate1_passed else ("FAILED" if not structural_valid else "INCOMPLETE"),
                "structural_valid": structural_valid,
                "trust_bonus": trust_bonus,
                "passed_rules": passed_gate1_rules,
                "failed_rules": failed_gate1_rules
            },
            "gate2": {
                "name": "Differential ROI Forensics & Biometrics",
                "status": "CLEAN" if max_delta_z <= 1.8 else ("ANOMALY" if max_delta_z <= 2.6 else "SPLICING_DETECTED"),
                "delta_z_face": delta_z_face,
                "delta_z_text": delta_z_text,
                "max_delta_z": max_delta_z,
                "splicing_detected": splicing_detected,
                "biometrics_1to1_status": bio_1to1.get("status", "NOT_PROVIDED"),
                "recycled_fraud_detected": recycled_fraud,
                "flagged_regions": gate2_result.get("flagged_rois", [])
            },
            "gate3": {
                "name": "Calibrated Multi-Gate Decision Scorer",
                "risk_score": final_score,
                "risk_level": risk_level,
                "badge_color": badge_color,
                "decision": decision,
                "action": action,
                "high_risk_triggered": high_risk_triggered,
                "trigger_reasons": trigger_reasons
            }
        }

        explanation = self._build_verdict_explanation(
            final_score=final_score,
            risk_level=risk_level,
            badge_color=badge_color,
            decision=decision,
            trigger_reasons=trigger_reasons,
            positive_signals=positive_signals,
            risk_factors=risk_factors
        )

        return {
            "risk_score": final_score,
            "risk_level": risk_level,
            "badge_color": badge_color,
            "decision": decision,
            "recommended_action": action,
            "gate1_passed": gate1_passed,
            "gate2_passed": gate2_passed and not high_risk_triggered,
            "gate_summary": gate_summary,
            "risk_factors": risk_factors,
            "positive_signals": positive_signals,
            "explanation": explanation
        }

    def _build_verdict_explanation(
        self,
        final_score: float,
        risk_level: str,
        badge_color: str,
        decision: str,
        trigger_reasons: List[str],
        positive_signals: List[str],
        risk_factors: List[str]
    ) -> str:
        lines = [
            f"3-Gate Security Assessment: Score {final_score}/100 [{risk_level} RISK | {badge_color}].",
            f"Verdict: {decision}."
        ]
        if trigger_reasons:
            lines.append("High Risk Triggers:")
            for tr in trigger_reasons:
                lines.append(f" - {tr}")
        elif positive_signals:
            lines.append(f"Deterministic & Forensic Trust Signals ({len(positive_signals)} verified):")
            for ps in positive_signals[:3]:
                lines.append(f" + {ps}")

        if risk_factors and not trigger_reasons:
            lines.append("Observation Notes:")
            for rf in risk_factors[:3]:
                lines.append(f" * {rf}")

        return "\n".join(lines)


gate3_scorer = CalibratedGate3Scorer()
