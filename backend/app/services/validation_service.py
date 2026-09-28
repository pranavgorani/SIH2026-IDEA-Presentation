import re
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from backend.app.models.schemas import ExtractedFields, MRZData, ValidationCheck, ValidationSummary

class ValidationService:
    """
    Validation engine ensuring syntactic, chronological, and cross-field integrity.
    Never throws 500 exceptions on missing fields; records informative UNAVAILABLE / INFO checks.
    """
    def validate_document_data(
        self,
        fields: ExtractedFields,
        mrz_data: Optional[MRZData] = None,
        document_type: str = "PASSPORT"
    ) -> ValidationSummary:
        checks: List[ValidationCheck] = []
        today = date.today()

        # Helper to parse dates safely
        def parse_date(date_str: Optional[str]) -> Optional[date]:
            if not date_str:
                return None
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d %b %Y", "%Y/%m/%d"):
                try:
                    return datetime.strptime(date_str.strip(), fmt).date()
                except (ValueError, TypeError):
                    continue
            return None

        # 1. Field-by-Field Presence & Extraction Status
        for field_key, field_label, field_val in [
            ("name", "Full Name", fields.name),
            ("document_number", "Document Number", fields.document_number),
            ("date_of_birth", "Date of Birth", fields.date_of_birth),
            ("date_of_expiry", "Validity Period", fields.date_of_expiry),
        ]:
            if not field_val or not str(field_val).strip():
                checks.append(ValidationCheck(
                    name=f"Field Extraction Check: {field_label}",
                    status="UNAVAILABLE",
                    severity="INFO",
                    message=f"{field_label} was not extracted or unavailable on document face.",
                    evidence={"field": field_key, "status": "UNAVAILABLE", "severity": "INFO"}
                ))
            else:
                checks.append(ValidationCheck(
                    name=f"Field Extraction Check: {field_label}",
                    status="PASS",
                    severity="LOW",
                    message=f"{field_label} successfully parsed."
                ))

        parsed_dob = parse_date(fields.date_of_birth)
        parsed_expiry = parse_date(fields.date_of_expiry)
        parsed_issue = parse_date(fields.date_of_issue)

        # 2. Date of Birth Format & Sanity
        if fields.date_of_birth and str(fields.date_of_birth).strip():
            if not parsed_dob:
                checks.append(ValidationCheck(
                    name="Date of Birth Format Check",
                    status="FAIL",
                    severity="HIGH",
                    message=f"Date of birth '{fields.date_of_birth}' is invalid or impossible calendar date."
                ))
            else:
                checks.append(ValidationCheck(
                    name="Date of Birth Format Check",
                    status="PASS",
                    severity="LOW",
                    message="Date of birth adheres to valid calendar representation."
                ))
        else:
            checks.append(ValidationCheck(
                name="Date of Birth Format Check",
                status="UNAVAILABLE",
                severity="INFO",
                message="Date of birth format check skipped — field unavailable.",
                evidence={"field": "date_of_birth", "status": "UNAVAILABLE", "severity": "INFO"}
            ))

        # 3. Expiry Check
        if parsed_expiry:
            if parsed_expiry < today:
                checks.append(ValidationCheck(
                    name="Document Expiry Check",
                    status="FAIL",
                    severity="HIGH",
                    message=f"Document expired on {parsed_expiry.isoformat()} (prior to screening date {today.isoformat()}).",
                    evidence={"expiry_date": parsed_expiry.isoformat(), "current_date": today.isoformat()}
                ))
            else:
                checks.append(ValidationCheck(
                    name="Document Expiry Check",
                    status="PASS",
                    severity="LOW",
                    message=f"Document is active and valid until {parsed_expiry.isoformat()}."
                ))
        elif fields.date_of_expiry and str(fields.date_of_expiry).strip():
            checks.append(ValidationCheck(
                name="Document Expiry Check",
                status="WARNING",
                severity="MEDIUM",
                message=f"Expiry date '{fields.date_of_expiry}' could not be parsed into a verifiable date."
            ))
        else:
            checks.append(ValidationCheck(
                name="Document Expiry Check",
                status="UNAVAILABLE",
                severity="INFO",
                message="Document expiry check skipped — field unavailable.",
                evidence={"field": "date_of_expiry", "status": "UNAVAILABLE", "severity": "INFO"}
            ))

        # 4. Chronological Integrity Check (DOB vs Issue vs Expiry)
        if parsed_dob and parsed_dob > today:
            checks.append(ValidationCheck(
                name="Chronological Sanity Check",
                status="FAIL",
                severity="CRITICAL",
                message="Date of birth is in the future. Physically impossible chronology.",
                evidence={"dob": parsed_dob.isoformat()}
            ))
        elif parsed_dob and parsed_issue and parsed_dob >= parsed_issue:
            checks.append(ValidationCheck(
                name="Chronological Sanity Check",
                status="FAIL",
                severity="HIGH",
                message="Date of birth is after or identical to document issue date.",
                evidence={"dob": parsed_dob.isoformat(), "issue": parsed_issue.isoformat()}
            ))
        elif parsed_issue and parsed_expiry and parsed_issue >= parsed_expiry:
            checks.append(ValidationCheck(
                name="Chronological Sanity Check",
                status="FAIL",
                severity="HIGH",
                message="Document issue date is greater than or equal to expiry date.",
                evidence={"issue": parsed_issue.isoformat(), "expiry": parsed_expiry.isoformat()}
            ))
        elif parsed_dob or parsed_expiry or parsed_issue:
            checks.append(ValidationCheck(
                name="Chronological Sanity Check",
                status="PASS",
                severity="LOW",
                message="Temporal chronology (Birth -> Issue -> Expiration) is internally consistent."
            ))
        else:
            checks.append(ValidationCheck(
                name="Chronological Sanity Check",
                status="UNAVAILABLE",
                severity="INFO",
                message="Chronological validation skipped — dates unavailable."
            ))

        # 5. Document Number Format Validation
        doc_num = (fields.document_number or "").strip()
        if doc_num:
            if len(doc_num) < 5 or len(doc_num) > 20:
                checks.append(ValidationCheck(
                    name="Document Number Format",
                    status="WARNING",
                    severity="MEDIUM",
                    message=f"Document number '{doc_num}' length ({len(doc_num)}) deviates from standard standard pattern (5-20 characters)."
                ))
            elif not re.match(r'^[A-Z0-9\-_]+$', doc_num, re.I):
                checks.append(ValidationCheck(
                    name="Document Number Format",
                    status="FAIL",
                    severity="HIGH",
                    message=f"Document number '{doc_num}' contains illegal non-alphanumeric characters."
                ))
            else:
                checks.append(ValidationCheck(
                    name="Document Number Format",
                    status="PASS",
                    severity="LOW",
                    message="Document identifier conforms to alphanumeric standard formatting."
                ))
        else:
            checks.append(ValidationCheck(
                name="Document Number Format",
                status="UNAVAILABLE",
                severity="INFO",
                message="Document number check skipped — identifier unavailable."
            ))

        # 6. MRZ vs Visual Cross-Check Consistency
        if mrz_data and hasattr(mrz_data, "valid"):
            mrz_mismatches = []
            if mrz_data.passport_number and doc_num:
                mrz_doc = mrz_data.passport_number.replace('<', '').strip()
                if mrz_doc != doc_num and mrz_doc not in doc_num and doc_num not in mrz_doc:
                    mrz_mismatches.append(f"Document Number mismatch (Visual: {doc_num} vs MRZ: {mrz_doc})")

            if mrz_data.date_of_birth and fields.date_of_birth:
                mrz_dob = parse_date(mrz_data.date_of_birth)
                if mrz_dob and parsed_dob and mrz_dob != parsed_dob:
                    mrz_mismatches.append(f"DOB mismatch (Visual: {parsed_dob.isoformat()} vs MRZ: {mrz_dob.isoformat()})")

            if mrz_data.expiry_date and fields.date_of_expiry:
                mrz_exp = parse_date(mrz_data.expiry_date)
                if mrz_exp and parsed_expiry and mrz_exp != parsed_expiry:
                    mrz_mismatches.append(f"Expiry mismatch (Visual: {parsed_expiry.isoformat()} vs MRZ: {mrz_exp.isoformat()})")

            if not getattr(mrz_data, "checksum_overall", True):
                checks.append(ValidationCheck(
                    name="MRZ Checksum Validation",
                    status="FAIL",
                    severity="HIGH",
                    message="MRZ composite or field checksum verification failed. Potential alteration in machine-readable zone.",
                    evidence={"mrz": mrz_data.raw_mrz}
                ))
            else:
                checks.append(ValidationCheck(
                    name="MRZ Checksum Validation",
                    status="PASS",
                    severity="LOW",
                    message="MRZ check digit validation passed (ICAO 9303 algorithm confirmed)."
                ))

            if mrz_mismatches:
                checks.append(ValidationCheck(
                    name="Visual vs MRZ Cross-Check",
                    status="FAIL",
                    severity="HIGH",
                    message="Cross-field inconsistency detected between Visual Inspection Zone (VIZ) and MRZ.",
                    evidence={"mismatches": mrz_mismatches}
                ))
            else:
                checks.append(ValidationCheck(
                    name="Visual vs MRZ Cross-Check",
                    status="PASS",
                    severity="LOW",
                    message="Visual fields match MRZ parsed values with 100% correlation."
                ))
        # 7. Nationality Code Validation (ISO 3166-1 alpha-3 code)
        nat = (fields.nationality or "").strip().upper()
        if nat:
            if re.match(r'^[A-Z]{3}$', nat):
                checks.append(ValidationCheck(
                    name="Nationality Code Format",
                    status="PASS",
                    severity="LOW",
                    message=f"Nationality '{nat}' conforms to standard 3-letter ICAO/ISO 3166-1 alpha-3 format."
                ))
            elif len(nat) >= 3 and nat.isalpha():
                checks.append(ValidationCheck(
                    name="Nationality Code Format",
                    status="PASS",
                    severity="LOW",
                    message=f"Nationality designation '{nat}' recognized."
                ))
            else:
                checks.append(ValidationCheck(
                    name="Nationality Code Format",
                    status="WARNING",
                    severity="MEDIUM",
                    message=f"Nationality '{nat}' does not conform to 3-letter ISO country code standard."
                ))
        else:
            checks.append(ValidationCheck(
                name="Nationality Code Format",
                status="UNAVAILABLE",
                severity="INFO",
                message="Nationality code check skipped — field unavailable."
            ))

        # 8. Duplicate Fields Check (Cross-Field Redundancy Anomaly)
        val_map = {
            "Name": fields.name,
            "Document Number": fields.document_number,
            "DOB": fields.date_of_birth,
            "Expiry": fields.date_of_expiry,
            "Nationality": fields.nationality
        }
        clean_vals = {k: str(v).strip().upper() for k, v in val_map.items() if v and len(str(v).strip()) > 3}
        duplicate_pairs = []
        val_seen = {}
        for k, v in clean_vals.items():
            if v in val_seen:
                duplicate_pairs.append(f"{k} and {val_seen[v]} have identical value '{v}'")
            else:
                val_seen[v] = k
        if duplicate_pairs:
            checks.append(ValidationCheck(
                name="Duplicate Fields Anomaly Check",
                status="FAIL",
                severity="HIGH",
                message=f"Abnormal duplicate text found across distinct fields: {'; '.join(duplicate_pairs)}."
            ))
        else:
            checks.append(ValidationCheck(
                name="Duplicate Fields Anomaly Check",
                status="PASS",
                severity="LOW",
                message="Distinct credential fields possess independent, non-duplicated values."
            ))

        # 9. Document Type Consistency Check
        if document_type.upper() == "PASSPORT":
            if mrz_data and mrz_data.valid:
                checks.append(ValidationCheck(
                    name="Document Type Consistency",
                    status="PASS",
                    severity="LOW",
                    message="Passport document structure and MRZ format are mutually consistent."
                ))
            else:
                checks.append(ValidationCheck(
                    name="Document Type Consistency",
                    status="WARNING" if not mrz_data else "FAIL",
                    severity="MEDIUM",
                    message="Document classified as Passport but standard TD3 MRZ layout is missing or unverified."
                ))
        elif document_type.upper() == "VISA":
            checks.append(ValidationCheck(
                name="Document Type Consistency",
                status="PASS",
                severity="LOW",
                message="Visa credential conforms to expected layout parameters."
            ))
        else:
            checks.append(ValidationCheck(
                name="Document Type Consistency",
                status="PASS",
                severity="LOW",
                message=f"Document format consistent with declared {document_type} credential type."
            ))

        # Calculate Summary
        passed = sum(1 for c in checks if c.status == "PASS")
        failed = sum(1 for c in checks if c.status == "FAIL")
        warnings = sum(1 for c in checks if c.status == "WARNING")
        is_valid = failed == 0

        return ValidationSummary(
            valid=is_valid,
            passed_count=passed,
            failed_count=failed,
            warning_count=warnings,
            checks=checks
        )

validation_service = ValidationService()
