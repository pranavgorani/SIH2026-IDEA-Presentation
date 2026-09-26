from datetime import datetime, timezone
from typing import Optional, Dict, Any
from backend.app.models.schemas import RecordVerificationResponse
from backend.app.providers.mock_verification import mock_verification_provider, BaseVerificationProvider

class RecordVerificationService:
    def __init__(self, provider: Optional[BaseVerificationProvider] = None):
        self.provider = provider or mock_verification_provider

    def set_provider(self, provider: BaseVerificationProvider):
        self.provider = provider

    def verify_record(
        self,
        document_number: str,
        document_type: str = "PASSPORT",
        candidate_name: Optional[str] = None
    ) -> RecordVerificationResponse:
        res = self.provider.verify(document_number, document_type, candidate_name)
        return RecordVerificationResponse(
            record_found=res.get("record_found", False),
            status=res.get("status", "NOT_FOUND"),
            document_number=res.get("document_number", document_number),
            source=res.get("source", "MOCK_CENTRAL_REGISTRY (SIMULATED)"),
            match_details=res.get("match_details"),
            checked_at=datetime.now(timezone.utc),
            disclaimer=res.get("disclaimer", "SIMULATED / DEMONSTRATION DATA")
        )

record_verification_service = RecordVerificationService()
