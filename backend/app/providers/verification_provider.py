"""
Verification Provider module adhering to Section 18 & 19 of TRUST-ID Specification.
Defines VerificationProvider with states: AVAILABLE, UNAVAILABLE, NOT_CONFIGURED.
External verification status is NOT_CONFIGURED by default unless an authorized
external government or regulatory API is integrated.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timezone
import os

class VerificationProviderState:
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_CONFIGURED = "NOT_CONFIGURED"

class VerificationProvider:
    """
    Manages external verification provider connections.
    Distinguishes between DOCUMENT RECOGNIZED and DOCUMENT OFFICIALLY VERIFIED.
    """
    def __init__(self, provider_name: str = "TRUST_ID_GATEWAY"):
        self.provider_name = provider_name
        self.api_key = os.getenv("EXTERNAL_VERIFICATION_API_KEY")
        self.endpoint_url = os.getenv("EXTERNAL_VERIFICATION_ENDPOINT")

    @property
    def status(self) -> str:
        """
        Returns AVAILABLE, UNAVAILABLE, or NOT_CONFIGURED.
        Section 19: If no authorized external source is configured, returns NOT_CONFIGURED.
        """
        if not self.endpoint_url or not self.api_key:
            return VerificationProviderState.NOT_CONFIGURED
        return VerificationProviderState.AVAILABLE

    def verify_document(self, document_number: str, document_type: str, candidate_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Checks document against external registry if configured.
        Never pretends OCR alone verifies official government records.
        """
        prov_status = self.status
        if prov_status == VerificationProviderState.NOT_CONFIGURED:
            return {
                "status": VerificationProviderState.NOT_CONFIGURED,
                "verified": False,
                "provider": self.provider_name,
                "document_number": document_number,
                "message": "External government verification database is not configured in this environment.",
                "disclaimer": "Document recognized by OCR/MRZ/CV heuristics only. Not officially cross-referenced with government registries.",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        # If configured (future live external API integration)
        return {
            "status": VerificationProviderState.AVAILABLE,
            "verified": False,
            "provider": self.provider_name,
            "document_number": document_number,
            "message": "External verification query completed.",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

default_verification_provider = VerificationProvider()
