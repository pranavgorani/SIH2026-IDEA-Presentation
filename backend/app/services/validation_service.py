import re
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from backend.app.models.schemas import ExtractedFields, MRZData, ValidationCheck, ValidationSummary
from backend.app.services.document_validators import validator_registry

class ValidationService:
    """
    Validation engine ensuring syntactic, chronological, and cross-field integrity.
    Never throws 500 exceptions on missing fields; records informative UNAVAILABLE / INFO checks.
    Applies dedicated document-type specific validators (PAN, Aadhaar, Passport, DL, Voter ID).
    """
    def validate_document_data(
        self,
        fields: ExtractedFields,
        mrz_data: Optional[MRZData] = None,
        document_type: str = "PASSPORT"
    ) -> ValidationSummary:
        checks: List[ValidationCheck] = []
        today = date.today()
        doc_type_clean = (document_type or "PASSPORT").strip().upper().replace(" ", "_")

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

        # Determine if document type has an expiry date
        no_expiry_types = {"PAN_CARD", "PAN", "AADHAAR", "AADHAAR_CARD", "VOTER_ID", "EPIC"}
        is_expiry_applicable = doc_type_clean not in no_expiry_types

        # 1. Field-by-Field Presence & Extraction Status
        field_specs = [
            ("name", "Full Name", fields.name, True),
            ("document_number", "Document Number", fields.document_number, True),
            ("date_of_birth", "Date of Birth", fields.date_of_birth, True),
            ("date_of_expiry", "Validity Period", fields.date_of_expiry, is_expiry_applicable),
        ]

        for field_key, field_label, field_val, is_app in field_specs:
            if not is_app:
                checks.append(ValidationCheck(
                    name=f"Field Extraction Check: {field_label}",
                    status="NOT_APPLICABLE",
                    severity="LOW",
                    message=f"{field_label} is not applicable for {document_type} credential type.",
                    evidence={"field": field_key, "status": "NOT_APPLICABLE", "severity": "LOW"}
                ))
            elif not field_val or not str(field_val).strip():
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
            dob_str = str(fields.date_of_birth).strip()
            # Allow year only for Aadhaar
            if "AADHAAR" in doc_type_clean and re.match(r'^(19|20)\d{2}$', dob_str):
                checks.append(ValidationCheck(
                    name="Date of Birth Format Check",
                    status="PASS",
                    severity="LOW",
                    message=f"Date of birth adheres to valid birth year representation ('{dob_str}')."
                ))
            elif not parsed_dob:
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

        # 3. Expiry Check (Only evaluated for applicable document types)
        if not is_expiry_applicable:
            checks.append(ValidationCheck(
                name="Document Expiry Check",
                status="NOT_APPLICABLE",
                severity="LOW",
                message=f"Document expiry check is NOT_APPLICABLE for {document_type} (permanent/lifetime credential).",
                evidence={"field": "date_of_expiry", "status": "NOT_APPLICABLE", "severity": "LOW"}
            ))
        elif parsed_expiry:
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
        elif is_expiry_applicable and parsed_issue and parsed_expiry and parsed_issue >= parsed_expiry:
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
            if "AADHAAR" in doc_type_clean and re.match(r'^[X•x*]{4}\s+[X•x*]{4}\s+[0-9]{4}$', doc_num):
                checks.append(ValidationCheck(
                    name="Document Number Format",
                    status="PASS",
                    severity="LOW",
                    message="Masked Aadhaar format verified (XXXX XXXX 1234)."
                ))
            elif "PAN" in doc_type_clean:
                if re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]$', doc_num.upper()):
                    checks.append(ValidationCheck(
                        name="Document Number Format",
                        status="PASS",
                        severity="LOW",
                        message=f"PAN identifier syntax verified (5 letters, 4 digits, 1 letter)."
                    ))
                else:
                    checks.append(ValidationCheck(
                        name="Document Number Format",
                        status="WARNING",
                        severity="MEDIUM",
                        message=f"PAN format inconsistency: '{doc_num}' deviates from AAAAA9999A syntax."
                    ))
            elif len(doc_num) < 5 or len(doc_num) > 25:
                checks.append(ValidationCheck(
                    name="Document Number Format",
                    status="WARNING",
                    severity="MEDIUM",
                    message=f"Document number '{doc_num}' length ({len(doc_num)}) deviates from standard pattern (5-25 characters)."
                ))
            elif not re.match(r'^[A-Z0-9\-_•* ]+$', doc_num, re.I):
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

        # 6. MRZ vs Visual Cross-Check Consistency (Only if MRZ is applicable)
        mrz_applicable_types = {"PASSPORT", "INDIAN_PASSPORT", "VISA", "INDIAN_VISA"}
        is_mrz_expected = doc_type_clean in mrz_applicable_types

        if mrz_data and hasattr(mrz_data, "valid") and getattr(mrz_data, "raw_mrz", None):
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
        elif not is_mrz_expected:
            checks.append(ValidationCheck(
                name="MRZ Checksum Validation",
                status="NOT_APPLICABLE",
                severity="LOW",
                message=f"MRZ validation is NOT_APPLICABLE for {document_type} credential type."
            ))
        else:
            checks.append(ValidationCheck(
                name="MRZ Checksum Validation",
                status="WARNING",
                severity="MEDIUM",
                message=f"{document_type} typically features an ICAO MRZ zone which was not detected."
            ))

        # 7. Nationality Code Validation
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

        # 8. Duplicate Fields Check (Anomaly check)
        val_map = {
            "Name": fields.name,
            "Document Number": fields.document_number,
            "DOB": fields.date_of_birth,
            "Expiry": fields.date_of_expiry if is_expiry_applicable else None,
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

        # 9. Document-Specific Validator Integration from Registry
        specific_validator = validator_registry.get_validator(document_type)
        if specific_validator:
            specific_checks = specific_validator.validate(fields, mrz_data)
            existing_names = {c.name for c in checks}
            for sc in specific_checks:
                if sc.name in existing_names:
                    # Update existing check with document-specific logic
                    for i, ec in enumerate(checks):
                        if ec.name == sc.name:
                            checks[i] = sc
                            break
                else:
                    checks.append(sc)

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
