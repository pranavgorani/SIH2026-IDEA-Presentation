from datetime import datetime, timezone
from typing import Optional, Dict, Any
from backend.app.models.schemas import RecordVerificationResponse
from backend.app.providers.mock_verification import (
    mock_verification_provider, BaseVerificationProvider,
    passport_verification_provider, visa_verification_provider,
    identity_verification_provider, permit_verification_provider
)

class RecordVerificationService:
    def __init__(self, provider: Optional[BaseVerificationProvider] = None):
        self.provider = provider or mock_verification_provider
        self.providers_by_type = {
            "PASSPORT": passport_verification_provider,
            "VISA": visa_verification_provider,
            "NATIONAL_ID": identity_verification_provider,
            "DRIVING_LICENSE": identity_verification_provider,
            "PERMIT": permit_verification_provider,
            "TRAVEL_AUTHORIZATION": permit_verification_provider
        }

    def set_provider(self, provider: BaseVerificationProvider):
        self.provider = provider

    def register_provider_for_type(self, doc_type: str, provider: BaseVerificationProvider):
        self.providers_by_type[doc_type.upper()] = provider

    def verify_record(
        self,
        document_number: str,
        document_type: str = "PASSPORT",
        candidate_name: Optional[str] = None
    ) -> RecordVerificationResponse:
        try:
            active_provider = self.providers_by_type.get(document_type.upper(), self.provider)
            res = active_provider.verify(document_number, document_type, candidate_name)
            return RecordVerificationResponse(
                record_found=res.get("record_found", False),
                status=res.get("status", "NOT_FOUND"),
                document_number=res.get("document_number", document_number),
                source=res.get("source", "DEMO_VERIFICATION_DATABASE (SIMULATED)"),
                match_details=res.get("match_details"),
                checked_at=datetime.now(timezone.utc),
                disclaimer=res.get("disclaimer", "SIMULATED / DEMONSTRATION DATA")
            )
        except Exception:
            return RecordVerificationResponse(
                record_found=False,
                status="UNAVAILABLE",
                document_number=document_number,
                source="MOCK_REGISTRY_FALLBACK",
                match_details={"status": "UNAVAILABLE", "reason": "External verification unavailable"},
                checked_at=datetime.now(timezone.utc),
                disclaimer="SIMULATED / DEMONSTRATION DATA"
            )

record_verification_service = RecordVerificationService()
