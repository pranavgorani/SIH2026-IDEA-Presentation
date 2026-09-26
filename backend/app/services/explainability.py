from typing import Dict, Any, List
from backend.app.models.schemas import RiskAssessmentResponse

class ExplainabilityService:
    @staticmethod
    def generate_narrative_report(risk: RiskAssessmentResponse) -> Dict[str, Any]:
        """
        Formats an easily digestible Explainable AI (XAI) breakdown
        highlighting WHY the document received its specific score.
        """
        primary_driver = "No significant risk drivers."
        if risk.risk_factors:
            primary_driver = risk.risk_factors[0]

        summary_tone = "conforming" if risk.risk_level == "LOW" else ("concerning" if risk.risk_level == "HIGH" else "indeterminate")

        recommendations = []
        if risk.risk_level == "HIGH":
            recommendations.append("Mandatory Human-in-the-Loop review required prior to taking any administrative action.")
            recommendations.append("Examine visual forensics heatmap in highlighted high-residual areas.")
            recommendations.append("Manually cross-examine database record discrepancies with issuer authority.")
        elif risk.risk_level == "MEDIUM":
            recommendations.append("Secondary review recommended to resolve moderate ambiguities.")
            recommendations.append("Confirm expiry dates and check for physical wear or optical artifacting.")
        else:
            recommendations.append("Eligible for standard operational verification.")

        return {
            "risk_score": risk.risk_score,
            "risk_level": risk.risk_level,
            "confidence_percentage": round(risk.confidence * 100, 1),
            "primary_driver": primary_driver,
            "summary_tone": summary_tone,
            "reasons": risk.risk_factors,
            "positive_signals": risk.positive_signals,
            "recommended_actions": recommendations,
            "signal_radar": risk.signal_scores,
            "human_in_the_loop_mandatory": risk.risk_level == "HIGH"
        }

explainability_service = ExplainabilityService()
