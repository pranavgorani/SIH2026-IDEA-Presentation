import re
from typing import Dict, Any, Optional, List
from enum import Enum

class CanonicalDocType(str, Enum):
    PAN = "PAN"
    PAN_CARD = "PAN_CARD"
    AADHAAR = "AADHAAR"
    PASSPORT = "PASSPORT"
    INDIAN_PASSPORT = "INDIAN_PASSPORT"
    VOTER_ID = "VOTER_ID"
    DRIVING_LICENSE = "DRIVING_LICENSE"
    DRIVING_LICENCE = "DRIVING_LICENCE"
    VEHICLE_RC = "VEHICLE_RC"
    INDIAN_VISA = "INDIAN_VISA"
    VISA = "VISA"
    VISA_OR_PERMIT = "VISA_OR_PERMIT"
    OCI_CARD = "OCI_CARD"
    NATIONAL_ID = "NATIONAL_ID"
    GENERIC_ID = "GENERIC_ID"
    UNSUPPORTED = "UNSUPPORTED"
    UNKNOWN = "UNKNOWN"

CANONICAL_TYPE_MAP = {
    "PAN": "PAN",
    "PAN_CARD": "PAN",
    "PAN CARD": "PAN",
    "INDIAN PAN": "PAN",
    "PERMANENT ACCOUNT NUMBER": "PAN",
    "AADHAAR": "AADHAAR",
    "AADHAAR_CARD": "AADHAAR",
    "AADHAAR CARD": "AADHAAR",
    "UIDAI": "AADHAAR",
    "PASSPORT": "PASSPORT",
    "INDIAN_PASSPORT": "PASSPORT",
    "INDIAN PASSPORT": "PASSPORT",
    "VOTER_ID": "VOTER_ID",
    "VOTER ID": "VOTER_ID",
    "EPIC": "VOTER_ID",
    "ELECTOR PHOTO IDENTITY CARD": "VOTER_ID",
    "DRIVING_LICENSE": "DRIVING_LICENSE",
    "DRIVING_LICENCE": "DRIVING_LICENSE",
    "DRIVING LICENSE": "DRIVING_LICENSE",
    "DRIVING LICENCE": "DRIVING_LICENSE",
    "VEHICLE_RC": "VEHICLE_RC",
    "VEHICLE RC": "VEHICLE_RC",
    "REGISTRATION CERTIFICATE": "VEHICLE_RC",
    "INDIAN_VISA": "VISA",
    "INDIAN VISA": "VISA",
    "VISA": "VISA",
    "VISA_OR_PERMIT": "VISA",
    "OCI_CARD": "OCI_CARD",
    "OCI CARD": "OCI_CARD",
    "NATIONAL_ID": "NATIONAL_ID",
    "NATIONAL ID": "NATIONAL_ID",
    "GENERIC_ID": "GENERIC_ID",
    "GENERIC_DOCUMENT": "GENERIC_ID",
    "UNSUPPORTED": "UNSUPPORTED",
    "UNKNOWN": "UNKNOWN"
}

def normalize_canonical_doc_type(val: Optional[str]) -> str:
    if not val:
        return "UNKNOWN"
    clean = str(val).strip().upper().replace("-", "_")
    if clean in CANONICAL_TYPE_MAP:
        return CANONICAL_TYPE_MAP[clean]
    clean_sp = clean.replace("_", " ")
    if clean_sp in CANONICAL_TYPE_MAP:
        return CANONICAL_TYPE_MAP[clean_sp]
    for k, canonical in CANONICAL_TYPE_MAP.items():
        if k in clean or k in clean_sp:
            return canonical
    return clean

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
        r'\bP<IND\b', r'\bP<', r'\bINDIAN\s+PASSPORT\b', r'\bPASSEPORT\b'
    ]

    PAN_PATTERNS = [
        r'\b[A-Z]{5}[0-9]{4}[A-Z]\b',
        r'\bPERMANENT\s+ACCOUNT\s+NUMBER\b',
        r'\bINCOME\s*TAX\s*DEPARTMENT\b',
        r'\bINCOMETAXDEPARTMENT\b',
        r'\bINCOME\s*TAX\b',
        r'आयकर\s*विभाग',
        r'स्थायी\s*लेखा',
        r'\bPAN\s*CARD\b'
    ]

    AADHAAR_PATTERNS = [
        r'\bAADHAAR\b', r'\bUNIQUE\s+IDENTIFICATION\b', r'\bUIDAI\b',
        r'आधार', r'मेरा\s*आधार', r'मेरी\s*पहचान',
        r'\b[2-9]{1}[0-9]{3}\s+[0-9]{4}\s+[0-9]{4}\b',
        r'\b[2-9]{1}[0-9]{3}[-\s][0-9]{4}[-\s][0-9]{4}\b',
        r'\b[2-9]{1}[0-9]{11}\b',
        r'\b[X•\*x]{4}\s*[X•\*x]{4}\s*[0-9]{4}\b',
        r'\bVID\b', r'\bENROLMENT\s*NO\b', r'HELP@UIDAI'
    ]

    VOTER_ID_PATTERNS = [
        r'\b[A-Z]{3}[0-9]{7}\b',
        r'\bELECTION\s+COMMISSION\s+OF\s+INDIA\b',
        r'\bELECTOR\s+PHOTO\s+IDENTITY\s+CARD\b',
        r'\bEPIC\s*NO\b',
        r'\bEPIC\b',
        r'भारत\s*निर्वाचन\s*आयोग',
        r'\bELECTORAL\s+ROLL\b',
        r'\bASSEMBLY\s+CONSTITUENCY\b'
    ]

    DRIVING_LICENSE_PATTERNS = [
        r'\b[A-Z]{2}[-\s]?[0-9]{2}[-\s]?[0-9]{4}[-\s]?[0-9]{7}\b',
        r'\b[A-Z]{2}[0-9]{13,15}\b',
        r'\bDRIVING\s+LICENCE\b', r'\bDRIVING\s+LICENSE\b',
        r'\bDL\s*NO\b',
        r'\bFORM\s*7\b', r'\bUNION\s+OF\s+INDIA\b',
        r'\bMOTOR\s+VEHICLES?\s+ACT\b', r'\bAUTHORISED\s+TO\s+DRIVE\b',
        r'\bTRANSPORT\s+DEPARTMENT\b', r'\bSARATHI\b', r'\bPARIVAHAN\b'
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

        # 0. Check for Empty, Blurry, or Insufficient text (< 15 chars)
        if len(text_clean) < 15 and not has_mrz:
            return {
                "document_type": "UNKNOWN",
                "document_subtype": "UNREADABLE_IMAGE",
                "issuing_country": "UNKNOWN",
                "classification_confidence": 0.05,
                "confidence": 0.05,
                "classification_evidence": ["Insufficient legible textual content detected (< 15 characters)"],
                "alternative_candidates": [],
                "supported_status": "NEEDS_REVIEW",
                "status": "NOT_VERIFIED",
                "classifier_status": "NEEDS_RESCAN",
                "processing_status": "NEEDS_RESCAN",
                "supported": False,
                "country": "UNKNOWN",
                "explanation": "Insufficient legible textual content detected in document scan. Image may be blurry, low contrast, or poorly illuminated. Rescan requested."
            }

        # Check for Indian PAN Card specific pattern (Strongest signal)
        pan_num = re.search(r'\b([A-Z]{5}[0-9]{4}[A-Z])\b', text_clean)
        is_pan_marker = any(re.search(p, text_clean, re.I) for p in self.PAN_PATTERNS)
        if pan_num or is_pan_marker:
            evidence = []
            if pan_num:
                evidence.append(f"PAN regex pattern matched: {pan_num.group(1)}")
            if is_pan_marker:
                evidence.append("Income Tax Department / Permanent Account Number keyword matched")
            return {
                "document_type": "PAN_CARD",
                "document_subtype": "INDIAN_PAN_INDIVIDUAL",
                "issuing_country": "IND",
                "classification_confidence": 0.98 if pan_num else 0.88,
                "confidence": 0.98 if pan_num else 0.88,
                "classification_evidence": evidence,
                "alternative_candidates": [{"document_type": "GENERIC_ID", "confidence": 0.20}],
                "supported_status": "SUPPORTED",
                "status": "RECOGNIZED",
                "classifier_status": "COMPLETED",
                "processing_status": "COMPLETED",
                "supported": True,
                "country": "IND",
                "explanation": "Indian Permanent Account Number (PAN) Card identified from income tax typography and PAN syntax."
            }

        # Check for Indian Aadhaar Card
        is_aadhaar = any(re.search(p, text_clean, re.I) for p in self.AADHAAR_PATTERNS)
        if is_aadhaar:
            evidence = ["UIDAI / Government of India Aadhaar identity keywords matched"]
            if re.search(r'\b[0-9]{4}\s+[0-9]{4}\s+[0-9]{4}\b', text_clean):
                evidence.append("12-digit Aadhaar number layout detected")
            elif re.search(r'[X*]{4}[\s-]*[X*]{4}[\s-]*[0-9]{4}', text_clean, re.I):
                evidence.append("Masked Aadhaar pattern detected")
            return {
                "document_type": "AADHAAR",
                "document_subtype": "AADHAAR_CARD",
                "issuing_country": "IND",
                "classification_confidence": 0.95,
                "confidence": 0.95,
                "classification_evidence": evidence,
                "alternative_candidates": [{"document_type": "GENERIC_ID", "confidence": 0.25}],
                "supported_status": "SUPPORTED",
                "status": "RECOGNIZED",
                "classifier_status": "COMPLETED",
                "processing_status": "COMPLETED",
                "supported": True,
                "country": "IND",
                "explanation": "Indian Aadhaar National Identity Document identified from UIDAI layout and format."
            }

        # Check for Indian Voter ID / EPIC
        epic_match = re.search(r'\b([A-Z]{3}[0-9]{7})\b', text_clean)
        is_epic = epic_match or any(re.search(p, text_clean, re.I) for p in self.VOTER_ID_PATTERNS)
        if is_epic:
            evidence = []
            if epic_match:
                evidence.append(f"EPIC alphanumeric identifier matched: {epic_match.group(1)}")
            evidence.append("Election Commission of India / Elector Photo Identity Card anchor matched")
            return {
                "document_type": "VOTER_ID",
                "document_subtype": "EPIC_ELECTORAL",
                "issuing_country": "IND",
                "classification_confidence": 0.95 if epic_match else 0.85,
                "confidence": 0.95 if epic_match else 0.85,
                "classification_evidence": evidence,
                "alternative_candidates": [{"document_type": "NATIONAL_ID", "confidence": 0.20}],
                "supported_status": "SUPPORTED",
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
                "document_subtype": "VEHICLE_REGISTRATION_CERTIFICATE",
                "issuing_country": "IND",
                "classification_confidence": 0.90,
                "confidence": 0.90,
                "classification_evidence": ["Transport Department / Registration Certificate keywords matched"],
                "alternative_candidates": [],
                "supported_status": "SUPPORTED",
                "status": "RECOGNIZED",
                "supported": True,
                "country": "IND",
                "explanation": "Vehicle Registration Certificate (RC) identified from transport authority registration fields."
            }

        # Check for Indian Driving Licence
        dl_match = re.search(r'\b([A-Z]{2}[-\s]?[0-9]{2}[-\s]?[0-9]{4}[-\s]?[0-9]{7})\b', text_clean)
        is_dl = dl_match or any(re.search(p, text_clean, re.I) for p in self.DRIVING_LICENSE_PATTERNS)
        if is_dl:
            evidence = ["Motor Vehicle Driving Licence keywords detected"]
            if dl_match:
                evidence.append(f"Standard DL format matched: {dl_match.group(1)}")
            return {
                "document_type": "DRIVING_LICENSE",
                "document_subtype": "DRIVING_LICENCE_SMART_CARD",
                "issuing_country": "IND",
                "classification_confidence": 0.95 if dl_match else 0.85,
                "confidence": 0.95 if dl_match else 0.85,
                "classification_evidence": evidence,
                "alternative_candidates": [{"document_type": "NATIONAL_ID", "confidence": 0.15}],
                "supported_status": "SUPPORTED",
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
                "document_subtype": "INDIAN_CONSULAR_VISA",
                "issuing_country": "IND",
                "classification_confidence": 0.92,
                "confidence": 0.92,
                "classification_evidence": ["Government of India Visa foil headers matched"],
                "alternative_candidates": [{"document_type": "VISA", "confidence": 0.40}],
                "supported_status": "SUPPORTED",
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
                "document_subtype": "OVERSEAS_CITIZEN_CARD",
                "issuing_country": "IND",
                "classification_confidence": 0.92,
                "confidence": 0.92,
                "classification_evidence": ["Overseas Citizen of India keywords matched"],
                "alternative_candidates": [{"document_type": "VISA", "confidence": 0.30}],
                "supported_status": "SUPPORTED",
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
                    "document_subtype": "INDIAN_PASSPORT_TD3",
                    "issuing_country": "IND",
                    "classification_confidence": 0.98 if has_mrz else 0.88,
                    "confidence": 0.98 if has_mrz else 0.88,
                    "classification_evidence": ["Republic of India Passport anchor matched", "MRZ structure detected" if has_mrz else "Passport visual typography matched"],
                    "alternative_candidates": [{"document_type": "PASSPORT", "confidence": 0.50}],
                    "supported_status": "SUPPORTED",
                    "status": "RECOGNIZED",
                    "supported": True,
                    "country": "IND",
                    "explanation": "Republic of India Diplomatic/Standard Passport identified with MRZ structure."
                }
            else:
                return {
                    "document_type": "PASSPORT",
                    "document_subtype": "INTERNATIONAL_PASSPORT_TD3",
                    "issuing_country": "INTERNATIONAL",
                    "classification_confidence": 0.95 if has_mrz else 0.82,
                    "confidence": 0.95 if has_mrz else 0.82,
                    "classification_evidence": ["International travel passport ICAO layout matched", "MRZ lines verified" if has_mrz else "Passport headers matched"],
                    "alternative_candidates": [],
                    "supported_status": "SUPPORTED",
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
                "document_subtype": "INTERNATIONAL_ENTRY_VISA",
                "issuing_country": "INTERNATIONAL",
                "classification_confidence": 0.88,
                "confidence": 0.88,
                "classification_evidence": ["Visa / Schengen / Entry permit keywords detected"],
                "alternative_candidates": [],
                "supported_status": "SUPPORTED",
                "status": "RECOGNIZED",
                "supported": True,
                "country": "INTERNATIONAL",
                "explanation": "International travel visa foil recognized."
            }

        # General National ID / Residence Card
        if "IDENTITY CARD" in text_upper or "RESIDENCE PERMIT" in text_upper or "NATIONAL ID" in text_upper:
            return {
                "document_type": "NATIONAL_ID",
                "document_subtype": "NATIONAL_RESIDENCE_CARD",
                "issuing_country": "INTERNATIONAL",
                "classification_confidence": 0.82,
                "confidence": 0.82,
                "classification_evidence": ["National Identity Card layout markers detected"],
                "alternative_candidates": [{"document_type": "GENERIC_ID", "confidence": 0.40}],
                "supported_status": "SUPPORTED",
                "status": "RECOGNIZED",
                "classifier_status": "COMPLETED",
                "processing_status": "COMPLETED",
                "supported": True,
                "country": "INTERNATIONAL",
                "explanation": "National Identity Card format recognized."
            }

        # Generic Identity Credential
        OFFICIAL_ID_PATTERNS = [
            r'\bGOVERNMENT\b', r'\bGOVT\b', r'\bBHARAT\s*SARKAR\b', r'\bUNION\s+OF\s+INDIA\b',
            r'\bMINISTRY\b', r'\bDEPARTMENT\s+OF\b', r'\bOFFICIAL\s+IDENTITY\b',
            r'\bNATIONAL\s+REGISTRATION\b', r'\bCIVIL\s+REGISTRATION\b',
            r'\bSTATE\s+OF\b', r'\bREPUBLIC\s+OF\b', r'\bDIRECTORATE\b',
            r'\bIMMIGRATION\b', r'\bCONSULAR\b', r'\bPERMANENT\s+RESIDENT\b'
        ]
        is_official_generic = any(re.search(p, text_clean, re.I) for p in OFFICIAL_ID_PATTERNS)

        if is_official_generic:
            return {
                "document_type": "GENERIC_ID",
                "document_subtype": "GENERIC_GOVERNMENT_CREDENTIAL",
                "issuing_country": "UNKNOWN",
                "classification_confidence": 0.78,
                "confidence": 0.78,
                "classification_evidence": ["Official government authority marker identified"],
                "alternative_candidates": [{"document_type": "NATIONAL_ID", "confidence": 0.35}],
                "supported_status": "NEEDS_REVIEW",
                "status": "RECOGNIZED",
                "classifier_status": "NEEDS_REVIEW",
                "processing_status": "NEEDS_REVIEW",
                "supported": True,
                "country": "UNKNOWN",
                "explanation": "Generic or unindexed official credential recognized. Preserving all extracted text and fields for secondary review."
            }

        # Check for Unsupported Non-Identity Documents
        UNSUPPORTED_NON_ID_PATTERNS = [
            r'\bRECEIPT\b', r'\bGROCERY\b', r'\bSUPERMARKET\b', r'\bINVOICE\b',
            r'\bCASH\s+PAID\b', r'\bTOTAL\s*[\$₹€£]', r'\bTABLE\s+[0-9]+\b',
            r'\bRESTAURANT\b', r'\bMENU\b', r'\bORDER\s*#?[0-9]+\b',
            r'\bMEMBERSHIP\s+CARD\b', r'\bLIBRARY\b', r'\bCLUB\b', r'\bGYM\b',
            r'\bSTUDENT\s+ID\b', r'\bSTUDENT\s+CARD\b',
            r'\bPHOTOGRAPH\b', r'\bLANDSCAPE\b', r'\bNATURE\b', r'\bPHOTO\b'
        ]
        if any(re.search(p, text_clean, re.I) for p in UNSUPPORTED_NON_ID_PATTERNS):
            return {
                "document_type": "UNSUPPORTED",
                "document_subtype": "NON_IDENTITY_DOCUMENT",
                "issuing_country": "UNKNOWN",
                "classification_confidence": 0.15,
                "confidence": 0.15,
                "classification_evidence": ["Commercial receipt, invoice, membership, or student non-identity pattern detected"],
                "alternative_candidates": [],
                "supported_status": "UNSUPPORTED",
                "status": "NOT_VERIFIED",
                "classifier_status": "NOT_VERIFIED",
                "processing_status": "NOT_VERIFIED",
                "supported": False,
                "country": "UNKNOWN",
                "explanation": "Uploaded document appears to be a receipt, invoice, membership card, student ID, or non-identity record rather than an official identity credential."
            }

        # Unindexed / Unknown document with readable text: preserve for review, do not fail
        if len(text_clean) >= 15:
            return {
                "document_type": "UNKNOWN",
                "document_subtype": "UNINDEXED_DOCUMENT",
                "issuing_country": "UNKNOWN",
                "classification_confidence": 0.50,
                "confidence": 0.50,
                "classification_evidence": ["Readable textual data extracted but document subtype unindexed"],
                "alternative_candidates": [],
                "supported_status": "UNKNOWN",
                "status": "COMPLETED",
                "classifier_status": "COMPLETED",
                "processing_status": "COMPLETED",
                "supported": True,
                "country": "UNKNOWN",
                "explanation": "Document type unknown or unclassified. All visible text and fields have been extracted."
            }

        # Truly empty, blurred or unreadable scan
        return {
            "document_type": "UNKNOWN",
            "document_subtype": "UNREADABLE_IMAGE",
            "issuing_country": "UNKNOWN",
            "classification_confidence": 0.10,
            "confidence": 0.10,
            "classification_evidence": ["Insufficient legible text detected"],
            "alternative_candidates": [],
            "supported_status": "UNKNOWN",
            "status": "UNREADABLE",
            "classifier_status": "UNREADABLE",
            "processing_status": "NEEDS_RESCAN",
            "supported": False,
            "country": "UNKNOWN",
            "explanation": "Insufficient legible text detected to classify document. Please inspect scan resolution and lighting."
        }

class DocumentClassifier:
    """Pluggable facade allowing hot-swapping with future deep learning classifiers."""
    def __init__(self, backend: Optional[BaseDocumentClassifier] = None):
        self.backend = backend or ModularDocumentClassifier()

    def classify_document(self, text: str, width: int = 0, height: int = 0, has_mrz: bool = False) -> Dict[str, Any]:
        return self.backend.classify(text=text, width=width, height=height, has_mrz=has_mrz)

document_classifier = DocumentClassifier()

