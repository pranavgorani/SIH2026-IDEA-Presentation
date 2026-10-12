import re
from typing import Dict, Any, Optional, List

class BaseDocumentClassifier:
    def classify(self, text: str, width: int = 0, height: int = 0, has_mrz: bool = False) -> Dict[str, Any]:
        raise NotImplementedError

class ModularDocumentClassifier(BaseDocumentClassifier):
    """
    High-accuracy, multi-tier document classifier supporting:
    - Indian Documents: Passport, Aadhaar, PAN Card, Voter ID (EPIC), Driving Licence,
      Vehicle Registration (RC), Indian Visa, OCI Card.
    - International Documents: Foreign Passport, Foreign Visa, Foreign ID.
    - Unsupported / Non-Document detection with explicit NOT_VERIFIED status.
    """

    INDIAN_PASSPORT_PATTERNS = [
        r'\bREPUBLIC\s+OF\s+INDIA\b', r'\bPASSPORT\b', r'\bBHARAT\s+SARKAR\b',
        r'\bP<IND\b', r'\bP<', r'\bINDIAN\s+PASSPORT\b'
    ]

    PAN_PATTERNS = [
        r'\b[A-Z]{5}[0-9]{4}[A-Z]\b',
        r'\bPERMANENT\s+ACCOUNT\s+NUMBER\b',
        r'\bINCOME\s*TAX\s*DEPARTMENT\b',
        r'\bINCOMETAXDEPARTMENT\b',
        r'आयकर\s*विभाग',
        r'स्थायी\s*लेखा'
    ]

    AADHAAR_PATTERNS = [
        r'\bAADHAAR\b', r'\bUNIQUE\s+IDENTIFICATION\b', r'\bUIDAI\b',
        r'आधार', r'मेरा\s*आधार', r'\b[2-9]{1}[0-9]{3}\s+[0-9]{4}\s+[0-9]{4}\b',
        r'\b[X•]{4}\s+[X•]{4}\s+[0-9]{4}\b', r'\bVID\b'
    ]

    VOTER_ID_PATTERNS = [
        r'\b[A-Z]{3}[0-9]{7}\b',
        r'\bELECTION\s+COMMISSION\s+OF\s+INDIA\b',
        r'\bELECTOR\s+PHOTO\s+IDENTITY\s+CARD\b',
        r'\bEPIC\b',
        r'भारत\s*निर्वाचन\s*आयोग'
    ]

    DRIVING_LICENSE_PATTERNS = [
        r'\b[A-Z]{2}[-\s]?[0-9]{2}[-\s]?[0-9]{4}[-\s]?[0-9]{7}\b',
        r'\bDRIVING\s+LICENCE\b', r'\bDRIVING\s+LICENSE\b',
        r'\bFORM\s*7\b', r'\bUNION\s+OF\s+INDIA\b',
        r'\bMOTOR\s+VEHICLES?\s+ACT\b', r'\bAUTHORISED\s+TO\s+DRIVE\b'
    ]

    VEHICLE_RC_PATTERNS = [
        r'\bREGISTRATION\s+CERTIFICATE\b',
        r'\bCERTIFICATE\s+OF\s+REGISTRATION\b',
        r'\bCHASSIS\s+NO\b', r'\bENGINE\s+NO\b',
        r'\bVEHICLE\s+CLASS\b', r'\bREGN\s*NO\b',
        r'\bFORM\s*23\b'
    ]

    INDIAN_VISA_PATTERNS = [
        r'\bINDIAN\s+VISA\b',
        r'\bGOVERNMENT\s+OF\s+INDIA\s+VISA\b',
        r'\bVISA\s+NO\b', r'\bNUMBER\s+OF\s+ENTRIES\b'
    ]

    OCI_PATTERNS = [
        r'\bOVERSEAS\s+CITIZEN\s+OF\s+INDIA\b',
        r'\bOCI\s+CARD\b', r'\bLIFE\s+LONG\s+VISA\b'
    ]

    FOREIGN_PASSPORT_PATTERNS = [
        r'\bPASSPORT\b', r'\bPASSEPORT\b', r'\bREISEPASS\b', r'\bPASAPORTE\b'
    ]

    FOREIGN_VISA_PATTERNS = [
        r'\bVISA\b', r'\bSCHENGEN\b', r'\bENTRY\s+PERMIT\b', r'\bESTA\b'
    ]

    def classify(self, text: str, width: int = 0, height: int = 0, has_mrz: bool = False) -> Dict[str, Any]:
        text_clean = text.strip()
        text_upper = text_clean.upper()

        # 0. Check for Empty, Blurry, or Non-Document text
        if len(text_clean) < 15 and not has_mrz:
            return {
                "document_type": "UNSUPPORTED",
                "confidence": 0.10,
                "status": "NOT_VERIFIED",
                "supported": False,
                "explanation": "Insufficient textual content or features detected. Document type could not be confidently recognized."
            }

        # Check for Indian PAN Card specific pattern (Strongest signal)
        pan_num = re.search(r'\b([A-Z]{5}[0-9]{4}[A-Z])\b', text_clean)
        is_pan_marker = any(re.search(p, text_clean, re.I) for p in self.PAN_PATTERNS)
        if pan_num or is_pan_marker:
            return {
                "document_type": "PAN_CARD",
                "confidence": 0.98 if pan_num else 0.88,
                "status": "RECOGNIZED",
                "supported": True,
                "country": "IND",
                "explanation": "Indian Permanent Account Number (PAN) Card identified from income tax typography and PAN syntax."
            }

        # Check for Indian Aadhaar Card
        is_aadhaar = any(re.search(p, text_clean, re.I) for p in self.AADHAAR_PATTERNS)
        if is_aadhaar:
            return {
                "document_type": "AADHAAR",
                "confidence": 0.95,
                "status": "RECOGNIZED",
                "supported": True,
                "country": "IND",
                "explanation": "Indian Aadhaar National Identity Document identified from UIDAI layout and format."
            }

        # Check for Indian Voter ID / EPIC
        epic_match = re.search(r'\b([A-Z]{3}[0-9]{7})\b', text_clean)
        is_epic = epic_match or any(re.search(p, text_clean, re.I) for p in self.VOTER_ID_PATTERNS)
        if is_epic:
            return {
                "document_type": "VOTER_ID",
                "confidence": 0.95 if epic_match else 0.85,
                "status": "RECOGNIZED",
                "supported": True,
                "country": "IND",
                "explanation": "Indian Voter ID / Electors Photo Identity Card (EPIC) identified from Election Commission markers."
            }

        # Check for Vehicle RC
        is_rc = any(re.search(p, text_clean, re.I) for p in self.VEHICLE_RC_PATTERNS)
        if is_rc:
            return {
                "document_type": "VEHICLE_RC",
                "confidence": 0.90,
                "status": "RECOGNIZED",
                "supported": True,
                "country": "IND",
                "explanation": "Vehicle Registration Certificate (RC) identified from transport authority registration fields."
            }

        # Check for Indian Driving Licence
        dl_match = re.search(r'\b([A-Z]{2}[-\s]?[0-9]{2}[-\s]?[0-9]{4}[-\s]?[0-9]{7})\b', text_clean)
        is_dl = dl_match or any(re.search(p, text_clean, re.I) for p in self.DRIVING_LICENSE_PATTERNS)
        if is_dl:
            return {
                "document_type": "DRIVING_LICENSE",
                "confidence": 0.95 if dl_match else 0.85,
                "status": "RECOGNIZED",
                "supported": True,
                "country": "IND",
                "explanation": "Indian Driving Licence identified from motor vehicle authority layout."
            }

        # Check for Indian Visa
        is_in_visa = any(re.search(p, text_clean, re.I) for p in self.INDIAN_VISA_PATTERNS)
        if is_in_visa:
            return {
                "document_type": "INDIAN_VISA",
                "confidence": 0.92,
                "status": "RECOGNIZED",
                "supported": True,
                "country": "IND",
                "explanation": "Government of India Visa foil recognized from consular entry permit layout."
            }

        # Check for OCI Card
        is_oci = any(re.search(p, text_clean, re.I) for p in self.OCI_PATTERNS)
        if is_oci:
            return {
                "document_type": "OCI_CARD",
                "confidence": 0.92,
                "status": "RECOGNIZED",
                "supported": True,
                "country": "IND",
                "explanation": "Overseas Citizen of India (OCI) document identified."
            }

        # Check for Indian Passport vs Foreign Passport
        has_india_kw = "INDIA" in text_upper or "REPUBLIC OF INDIA" in text_upper or "P<IND" in text_upper or "BHARAT" in text_upper
        if has_mrz or any(re.search(p, text_clean, re.I) for p in self.FOREIGN_PASSPORT_PATTERNS):
            if has_india_kw:
                return {
                    "document_type": "INDIAN_PASSPORT",
                    "confidence": 0.98 if has_mrz else 0.88,
                    "status": "RECOGNIZED",
                    "supported": True,
                    "country": "IND",
                    "explanation": "Republic of India Diplomatic/Standard Passport identified with MRZ structure."
                }
            else:
                return {
                    "document_type": "PASSPORT",
                    "confidence": 0.95 if has_mrz else 0.82,
                    "status": "RECOGNIZED",
                    "supported": True,
                    "country": "INTERNATIONAL",
                    "explanation": "International travel passport recognized from ICAO Doc 9303 layout and structure."
                }

        # Check for Foreign Visa
        is_visa = any(re.search(p, text_clean, re.I) for p in self.FOREIGN_VISA_PATTERNS)
        if is_visa:
            return {
                "document_type": "VISA",
                "confidence": 0.88,
                "status": "RECOGNIZED",
                "supported": True,
                "country": "INTERNATIONAL",
                "explanation": "International travel visa foil recognized."
            }

        # General National ID / Residence Card
        if "IDENTITY CARD" in text_upper or "RESIDENCE PERMIT" in text_upper or "NATIONAL ID" in text_upper:
            return {
                "document_type": "NATIONAL_ID",
                "confidence": 0.82,
                "status": "RECOGNIZED",
                "supported": True,
                "country": "INTERNATIONAL",
                "explanation": "National Identity Card format recognized."
            }

        # If none of the recognized document patterns match:
        return {
            "document_type": "UNSUPPORTED",
            "confidence": 0.30,
            "status": "NOT_VERIFIED",
            "supported": False,
            "explanation": "Document type could not be confidently recognized or supported by TRUST-ID."
        }

class DocumentClassifier:
    """Pluggable facade allowing hot-swapping with future deep learning classifiers."""
    def __init__(self, backend: Optional[BaseDocumentClassifier] = None):
        self.backend = backend or ModularDocumentClassifier()

    def classify_document(self, text: str, width: int = 0, height: int = 0, has_mrz: bool = False) -> Dict[str, Any]:
        return self.backend.classify(text=text, width=width, height=height, has_mrz=has_mrz)

document_classifier = DocumentClassifier()

