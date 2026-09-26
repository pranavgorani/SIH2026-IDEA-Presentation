from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, Any, Optional

class BaseVerificationProvider(ABC):
    @abstractmethod
    def verify(self, document_number: str, doc_type: str, candidate_name: Optional[str] = None) -> Dict[str, Any]:
        pass

class MockVerificationProvider(BaseVerificationProvider):
    """
    Simulated Verification Provider for Hackathon Demonstration.
    Pre-configured with synthetic test records.
    CLEARLY LABELED AS SIMULATED DATA.
    """
    DISCLAIMER = "SIMULATED / DEMONSTRATION DATA — NOT A REAL GOVERNMENT DATABASE"

    # Known synthetic mock database
    SYNTHETIC_REGISTRY = {
        "K81927361": {
            "status": "VALID",
            "name": "SHARMA ARJUN VIKRAM",
            "doc_type": "PASSPORT",
            "country": "DEMO",
            "expiry": "2028-06-09",
            "flagged": False
        },
        "A12345678": {
            "status": "VALID",
            "name": "SMITH JOHN EDWARD",
            "doc_type": "PASSPORT",
            "country": "USA",
            "expiry": "2029-11-20",
            "flagged": False
        },
        "EXP998877": {
            "status": "EXPIRED",
            "name": "PATEL PRIYA",
            "doc_type": "VISA",
            "country": "IND",
            "expiry": "2022-01-15",
            "flagged": False
        },
        "TAMPER007": {
            "status": "REVOKED",
            "name": "ALTERED RECORD",
            "doc_type": "NATIONAL_ID",
            "country": "DEMO",
            "expiry": "2027-04-12",
            "flagged": True
        }
    }

    def verify(self, document_number: str, doc_type: str, candidate_name: Optional[str] = None) -> Dict[str, Any]:
        clean_num = (document_number or "").strip().upper()
        now = datetime.now(timezone.utc).isoformat()

        if clean_num in self.SYNTHETIC_REGISTRY:
            reg = self.SYNTHETIC_REGISTRY[clean_num]
            name_match = True
            if candidate_name and reg.get("name"):
                name_match = any(part in reg["name"].upper() for part in candidate_name.upper().split() if len(part) > 2)

            return {
                "record_found": True,
                "status": reg["status"],
                "document_number": clean_num,
                "source": "MOCK_CENTRAL_REGISTRY (SIMULATED)",
                "match_details": {
                    "registered_name": reg["name"],
                    "name_match": name_match,
                    "registered_expiry": reg["expiry"],
                    "flagged_status": reg.get("flagged", False)
                },
                "checked_at": now,
                "disclaimer": self.DISCLAIMER
            }

        # If document number is not in static seed, provide a realistic simulated response
        # Default: if document number looks like test fake or has 'FAKE' or '999' -> NOT_FOUND / SUSPENDED
        if any(bad in clean_num for bad in ["FAKE", "FORGE", "99999", "TAMPER"]):
            return {
                "record_found": False,
                "status": "NOT_FOUND",
                "document_number": clean_num,
                "source": "MOCK_CENTRAL_REGISTRY (SIMULATED)",
                "match_details": {"error": "Record not found in simulated issuer database"},
                "checked_at": now,
                "disclaimer": self.DISCLAIMER
            }

        # Otherwise standard valid simulated record
        return {
            "record_found": True,
            "status": "VALID",
            "document_number": clean_num,
            "source": "MOCK_CENTRAL_REGISTRY (SIMULATED)",
            "match_details": {
                "registered_name": candidate_name or "SIMULATED CITIZEN",
                "name_match": True,
                "registered_expiry": "2028-12-31",
                "flagged_status": False
            },
            "checked_at": now,
            "disclaimer": self.DISCLAIMER
        }

# Provider instances
mock_verification_provider = MockVerificationProvider()
