import re
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from backend.app.models.schemas import ExtractedFields, MRZData, ValidationCheck, ValidationSummary

class ValidationService:
    def validate_document_data(
        self,
        fields: ExtractedFields,
        mrz_data: Optional[MRZData] = None,
        document_type: str = "PASSPORT"
    ) -> ValidationSummary:
        checks: List[ValidationCheck] = []
        today = date.today()

        # 1. Required Fields Check
        missing_fields = []
        if not fields.name: missing_fields.append("Full Name")
        if not fields.document_number: missing_fields.append("Document Number")
        if not fields.date_of_birth: missing_fields.append("Date of Birth")
        if not fields.date_of_expiry: missing_fields.append("Date of Expiry")

        if missing_fields:
            checks.append(ValidationCheck(
                name="Required Fields Check",
                status="FAIL",
                severity="HIGH",
                message=f"Missing mandatory document field(s): {', '.join(missing_fields)}",
                evidence={"missing": missing_fields}
            ))
        else:
            checks.append(ValidationCheck(
                name="Required Fields Check",
                status="PASS",
                severity="LOW",
                message="All mandatory credential fields successfully extracted."
            ))

        # Helper to parse dates
        def parse_date(date_str: Optional[str]) -> Optional[date]:
            if not date_str:
                return None
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d %b %Y", "%Y/%m/%d"):
                try:
                    return datetime.strptime(date_str.strip(), fmt).date()
                except ValueError:
                    continue
            return None

        parsed_dob = parse_date(fields.date_of_birth)
        parsed_expiry = parse_date(fields.date_of_expiry)
        parsed_issue = parse_date(fields.date_of_issue)

        # 2. Date Format & Calendar Validity Check
        if fields.date_of_birth and not parsed_dob:
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
        elif fields.date_of_expiry:
            checks.append(ValidationCheck(
                name="Document Expiry Check",
                status="WARNING",
                severity="MEDIUM",
                message=f"Expiry date '{fields.date_of_expiry}' could not be parsed into a verifiable date."
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
        else:
            checks.append(ValidationCheck(
                name="Chronological Sanity Check",
                status="PASS",
                severity="LOW",
                message="Temporal chronology (Birth -> Issue -> Expiration) is internally consistent."
            ))

        # 5. Document Number Format Validation
        doc_num = (fields.document_number or "").strip()
        if doc_num:
            if len(doc_num) < 6 or len(doc_num) > 16:
                checks.append(ValidationCheck(
                    name="Document Number Format",
                    status="WARNING",
                    severity="MEDIUM",
                    message=f"Document number '{doc_num}' length ({len(doc_num)}) deviates from standard standard pattern (6-16 characters)."
                ))
            elif not re.match(r'^[A-Z0-9]+$', doc_num, re.I):
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

        # 6. MRZ vs Visual Cross-Check Consistency
        if mrz_data:
            mrz_mismatches = []
            if mrz_data.passport_number and doc_num:
                # Compare without spaces/fillers
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

            # MRZ Checksum check
            if not mrz_data.checksum_overall:
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
        else:
            if document_type in ("PASSPORT", "NATIONAL_ID"):
                checks.append(ValidationCheck(
                    name="MRZ Verification",
                    status="WARNING",
                    severity="LOW",
                    message="MRZ not detected or not applicable for this credential side."
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
