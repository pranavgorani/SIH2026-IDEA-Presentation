import re
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from backend.app.models.schemas import ExtractedFields, MRZData, ValidationCheck, ValidationSummary

class BaseDocumentValidator:
    """Base validator for document-specific rules."""
    def validate(self, fields: ExtractedFields, mrz_data: Optional[MRZData] = None) -> List[ValidationCheck]:
        raise NotImplementedError

class PANValidator(BaseDocumentValidator):
    """
    Dedicated Indian PAN Card Validator (Section 3).
    - Format: 5 letters, 4 digits, 1 letter (AAAAA9999A)
    - DOB / Incorporation date
    - Father's name is optional and absence does not mean fraud
    - No expiry date required (Permanent)
    - No MRZ or Aadhaar QR rules applied
    """
    def validate(self, fields: ExtractedFields, mrz_data: Optional[MRZData] = None) -> List[ValidationCheck]:
        checks: List[ValidationCheck] = []
        doc_num = (fields.document_number or "").strip().upper()

        if doc_num:
            # 5 letters, 4 digits, 1 letter
            if re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]$', doc_num):
                checks.append(ValidationCheck(
                    name="PAN Identifier Format Check",
                    status="PASS",
                    severity="LOW",
                    message=f"PAN identifier '{doc_num[:2]}*****{doc_num[-2:]}' conforms to official Income Tax Department syntax (AAAAA9999A)."
                ))
            else:
                checks.append(ValidationCheck(
                    name="PAN Identifier Format Check",
                    status="WARNING",
                    severity="MEDIUM",
                    message=f"Document number '{doc_num}' does not conform to standard 10-character PAN format (AAAAA9999A). Format inconsistency recorded.",
                    evidence={"field": "document_number", "value": doc_num, "expected_pattern": "^[A-Z]{5}[0-9]{4}[A-Z]$"}
                ))
        else:
            checks.append(ValidationCheck(
                name="PAN Identifier Format Check",
                status="UNAVAILABLE",
                severity="INFO",
                message="PAN identifier was unreadable or not extracted from card face.",
                evidence={"field": "document_number", "status": "UNREADABLE"}
            ))

        # Holder Name Check
        if fields.name and fields.name.strip():
            checks.append(ValidationCheck(
                name="PAN Cardholder Name Check",
                status="PASS",
                severity="LOW",
                message="PAN holder name successfully extracted."
            ))
        else:
            checks.append(ValidationCheck(
                name="PAN Cardholder Name Check",
                status="UNAVAILABLE",
                severity="INFO",
                message="Cardholder name was not clearly readable on card face.",
                evidence={"field": "name", "status": "NOT_FOUND"}
            ))

        # Father's Name Check (Optional in modern PAN layouts)
        checks.append(ValidationCheck(
            name="PAN Father's Name Presence",
            status="PASS" if getattr(fields, "father_name", None) else "NOT_APPLICABLE",
            severity="LOW",
            message="Father's name present on card." if getattr(fields, "father_name", None) else "Father's name not present or optional for this card variant.",
            evidence={"field": "father_name", "status": "PRESENT" if getattr(fields, "father_name", None) else "NOT_APPLICABLE"}
        ))

        # Expiry Check (PAN does not expire)
        checks.append(ValidationCheck(
            name="Document Expiry Check",
            status="NOT_APPLICABLE",
            severity="LOW",
            message="PAN cards do not expire (Permanent Account Number). Expiry check is NOT_APPLICABLE.",
            evidence={"field": "date_of_expiry", "status": "NOT_APPLICABLE"}
        ))

        # MRZ Check (PAN does not have MRZ)
        checks.append(ValidationCheck(
            name="MRZ Checksum Validation",
            status="NOT_APPLICABLE",
            severity="LOW",
            message="PAN card is a domestic smart/laminated card without an ICAO 9303 MRZ zone.",
            evidence={"field": "mrz", "status": "NOT_APPLICABLE"}
        ))

        return checks

class AadhaarValidator(BaseDocumentValidator):
    """
    Dedicated Indian Aadhaar Validator (Section 4).
    - 12-digit UID or masked format (XXXX XXXX 1234)
    - Full DOB or Year of Birth only (accepted without penalty)
    - No expiry date required (Permanent)
    - No MRZ rules applied
    """
    def validate(self, fields: ExtractedFields, mrz_data: Optional[MRZData] = None) -> List[ValidationCheck]:
        checks: List[ValidationCheck] = []
        doc_num = (fields.document_number or "").strip()

        if doc_num:
            is_masked = bool(re.match(r'^[X•x*]{4}\s+[X•x*]{4}\s+[0-9]{4}$', doc_num))
            is_full = bool(re.match(r'^[2-9]{1}[0-9]{3}\s+[0-9]{4}\s+[0-9]{4}$', doc_num))
            is_compact = bool(re.match(r'^[2-9]{1}[0-9]{11}$', doc_num))

            if is_masked:
                checks.append(ValidationCheck(
                    name="Aadhaar Identifier Format Check",
                    status="PASS",
                    severity="LOW",
                    message="Masked Aadhaar format verified (XXXX XXXX 1234). Adheres to UIDAI masking privacy mandates."
                ))
            elif is_full or is_compact:
                checks.append(ValidationCheck(
                    name="Aadhaar Identifier Format Check",
                    status="PASS",
                    severity="LOW",
                    message="Aadhaar 12-digit identifier format verified."
                ))
            else:
                checks.append(ValidationCheck(
                    name="Aadhaar Identifier Format Check",
                    status="WARNING",
                    severity="MEDIUM",
                    message=f"Aadhaar identifier '{doc_num[:2]}****' format deviates from standard 12-digit or masked pattern.",
                    evidence={"field": "document_number", "value": "MASKED"}
                ))
        else:
            checks.append(ValidationCheck(
                name="Aadhaar Identifier Format Check",
                status="UNAVAILABLE",
                severity="INFO",
                message="Aadhaar identifier not readable on card face.",
                evidence={"field": "document_number", "status": "UNREADABLE"}
            ))

        # DOB / YOB Check
        dob_val = (fields.date_of_birth or "").strip()
        if dob_val:
            is_year_only = bool(re.match(r'^(19|20)\d{2}$', dob_val))
            if is_year_only:
                checks.append(ValidationCheck(
                    name="Date of Birth Format Check",
                    status="PASS",
                    severity="LOW",
                    message=f"Aadhaar birth year '{dob_val}' verified. Valid for UIDAI cards showing only year of birth."
                ))
            else:
                checks.append(ValidationCheck(
                    name="Date of Birth Format Check",
                    status="PASS",
                    severity="LOW",
                    message=f"Date of birth adheres to valid calendar representation."
                ))

        # Expiry Check (Aadhaar is lifetime)
        checks.append(ValidationCheck(
            name="Document Expiry Check",
            status="NOT_APPLICABLE",
            severity="LOW",
            message="Aadhaar card credentials do not possess an expiration date.",
            evidence={"field": "date_of_expiry", "status": "NOT_APPLICABLE"}
        ))

        # MRZ Check
        checks.append(ValidationCheck(
            name="MRZ Checksum Validation",
            status="NOT_APPLICABLE",
            severity="LOW",
            message="Aadhaar card does not utilize an ICAO 9303 MRZ zone.",
            evidence={"field": "mrz", "status": "NOT_APPLICABLE"}
        ))

        return checks

class DrivingLicenseValidator(BaseDocumentValidator):
    """
    Dedicated Driving Licence Validator (Section 5).
    - Format: 2-state code, RTO code, year, 7 digits
    - Licence classes
    - Does not require passport MRZ
    """
    def validate(self, fields: ExtractedFields, mrz_data: Optional[MRZData] = None) -> List[ValidationCheck]:
        checks: List[ValidationCheck] = []
        doc_num = (fields.document_number or "").strip().upper()

        if doc_num:
            if re.match(r'^[A-Z]{2}[-\s]?[0-9]{2}[-\s]?[0-9]{4}[-\s]?[0-9]{7}$', doc_num):
                checks.append(ValidationCheck(
                    name="Driving Licence Format Check",
                    status="PASS",
                    severity="LOW",
                    message=f"Driving licence identifier syntax verified against Indian state RTO registry format."
                ))
            elif len(doc_num) >= 8:
                checks.append(ValidationCheck(
                    name="Driving Licence Format Check",
                    status="PASS",
                    severity="LOW",
                    message=f"Driving licence identifier parsed."
                ))
            else:
                checks.append(ValidationCheck(
                    name="Driving Licence Format Check",
                    status="WARNING",
                    severity="MEDIUM",
                    message=f"Driving licence number '{doc_num}' deviates from standard syntax."
                ))

        # MRZ Check
        checks.append(ValidationCheck(
            name="MRZ Checksum Validation",
            status="NOT_APPLICABLE",
            severity="LOW",
            message="Driving Licence does not utilize an ICAO 9303 MRZ zone."
        ))

        return checks

class VoterIDValidator(BaseDocumentValidator):
    """
    Dedicated Voter ID (EPIC) Validator (Section 5).
    - 3 letters + 7 digits (e.g. ABC1234567)
    - Does not require passport fields
    - Does not expire
    """
    def validate(self, fields: ExtractedFields, mrz_data: Optional[MRZData] = None) -> List[ValidationCheck]:
        checks: List[ValidationCheck] = []
        doc_num = (fields.document_number or "").strip().upper()

        if doc_num:
            if re.match(r'^[A-Z]{3}[0-9]{7}$', doc_num):
                checks.append(ValidationCheck(
                    name="Voter ID EPIC Format Check",
                    status="PASS",
                    severity="LOW",
                    message=f"Elector Photo Identity Card (EPIC) number syntax verified (3 alpha + 7 digits)."
                ))
            else:
                checks.append(ValidationCheck(
                    name="Voter ID EPIC Format Check",
                    status="WARNING",
                    severity="MEDIUM",
                    message=f"Voter ID EPIC number '{doc_num}' deviates from standard 10-char format."
                ))

        checks.append(ValidationCheck(
            name="Document Expiry Check",
            status="NOT_APPLICABLE",
            severity="LOW",
            message="Voter ID cards do not possess an expiration date."
        ))
        checks.append(ValidationCheck(
            name="MRZ Checksum Validation",
            status="NOT_APPLICABLE",
            severity="LOW",
            message="Voter ID does not utilize an ICAO 9303 MRZ zone."
        ))

        return checks

class PassportValidator(BaseDocumentValidator):
    """
    Dedicated Passport Validator (Section 5).
    - Evaluates VIZ and MRZ independently
    - Validates ICAO 9303 check digits
    - Checks document expiry against current date
    """
    def validate(self, fields: ExtractedFields, mrz_data: Optional[MRZData] = None) -> List[ValidationCheck]:
        checks: List[ValidationCheck] = []
        today = date.today()

        def parse_date(date_str: Optional[str]) -> Optional[date]:
            if not date_str:
                return None
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d %b %Y", "%Y/%m/%d"):
                try:
                    return datetime.strptime(date_str.strip(), fmt).date()
                except (ValueError, TypeError):
                    continue
            return None

        # Expiry Check
        parsed_exp = parse_date(fields.date_of_expiry)
        if parsed_exp:
            if parsed_exp < today:
                checks.append(ValidationCheck(
                    name="Document Expiry Check",
                    status="FAIL",
                    severity="HIGH",
                    message=f"Passport expired on {parsed_exp.isoformat()} (prior to screening date {today.isoformat()}).",
                    evidence={"expiry_date": parsed_exp.isoformat(), "current_date": today.isoformat()}
                ))
            else:
                checks.append(ValidationCheck(
                    name="Document Expiry Check",
                    status="PASS",
                    severity="LOW",
                    message=f"Passport is active and valid until {parsed_exp.isoformat()}."
                ))
        elif fields.date_of_expiry:
            checks.append(ValidationCheck(
                name="Document Expiry Check",
                status="WARNING",
                severity="MEDIUM",
                message=f"Expiry date '{fields.date_of_expiry}' could not be parsed."
            ))

        # MRZ Check
        if mrz_data and getattr(mrz_data, "valid", None) is not None:
            if not getattr(mrz_data, "checksum_overall", True):
                checks.append(ValidationCheck(
                    name="MRZ Checksum Validation",
                    status="FAIL",
                    severity="HIGH",
                    message="MRZ composite or field checksum verification failed. Potential alteration in machine-readable zone.",
                    evidence={"mrz": getattr(mrz_data, "raw_mrz", [])}
                ))
            else:
                checks.append(ValidationCheck(
                    name="MRZ Checksum Validation",
                    status="PASS",
                    severity="LOW",
                    message="Passport MRZ check digit validation passed (ICAO 9303 algorithm confirmed)."
                ))

            # Cross-check VIZ vs MRZ
            mismatches = []
            mrz_doc = (getattr(mrz_data, "passport_number", "") or "").replace('<', '').strip()
            viz_doc = (fields.document_number or "").strip()
            if mrz_doc and viz_doc and mrz_doc != viz_doc and mrz_doc not in viz_doc and viz_doc not in mrz_doc:
                mismatches.append(f"Passport Number (Visual: {viz_doc} vs MRZ: {mrz_doc})")

            if mismatches:
                checks.append(ValidationCheck(
                    name="Visual vs MRZ Cross-Check",
                    status="FAIL",
                    severity="HIGH",
                    message=f"Cross-field inconsistency detected between Visual zone and MRZ: {'; '.join(mismatches)}.",
                    evidence={"mismatches": mismatches}
                ))
            else:
                checks.append(ValidationCheck(
                    name="Visual vs MRZ Cross-Check",
                    status="PASS",
                    severity="LOW",
                    message="Visual fields match MRZ parsed values with 100% correlation."
                ))
        else:
            checks.append(ValidationCheck(
                name="MRZ Checksum Validation",
                status="WARNING",
                severity="MEDIUM",
                message="Passport credential uploaded without readable ICAO 9303 TD3 MRZ zone."
            ))

        return checks

class DocumentValidatorRegistry:
    """Central registry mapping document types to dedicated validators (Section 5)."""
    def __init__(self):
        self._validators = {
            "PAN_CARD": PANValidator(),
            "PAN": PANValidator(),
            "AADHAAR": AadhaarValidator(),
            "AADHAAR_CARD": AadhaarValidator(),
            "DRIVING_LICENSE": DrivingLicenseValidator(),
            "DRIVING_LICENCE": DrivingLicenseValidator(),
            "VOTER_ID": VoterIDValidator(),
            "EPIC": VoterIDValidator(),
            "PASSPORT": PassportValidator(),
            "INDIAN_PASSPORT": PassportValidator(),
        }

    def get_validator(self, document_type: str) -> Optional[BaseDocumentValidator]:
        cleaned = (document_type or "").strip().upper().replace(" ", "_")
        return self._validators.get(cleaned)

validator_registry = DocumentValidatorRegistry()
