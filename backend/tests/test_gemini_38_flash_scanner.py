import pytest
import io
import json
from unittest.mock import MagicMock, patch, PropertyMock
from PIL import Image
from pathlib import Path

from backend.app.services.gemini_document_scanner import (
    GeminiDocumentScanner,
    gemini_document_scanner,
    GeminiDocumentScanResult,
    FieldResult,
    VisualObservation,
    LocalizedRegion,
    GeminiMRZInfo,
    OFFICIAL_GEMINI_MODEL,
    OFFICIAL_THINKING_LEVEL
)
from backend.app.services.gate1_validator import gate1_validator
from backend.app.services.gate2_forensics import gate2_forensics
from backend.app.services.gate3_scorer import gate3_scorer


# Helper to generate in-memory dummy image bytes
def create_test_image_bytes(w=600, h=400, color="white"):
    img = Image.new("RGB", (w, h), color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


# -----------------------------------------------------------------------------
# 1. Clear PAN image test
# -----------------------------------------------------------------------------
def test_clear_pan_image_scan():
    scanner = GeminiDocumentScanner()
    mock_payload = {
        "document_type": "PAN",
        "classification_status": "RECOGNIZED",
        "classification_cues": ["INCOME TAX DEPARTMENT", "Permanent Account Number"],
        "image_quality": {"status": "ACCEPTABLE", "issues": []},
        "fields": {
            "document_number": {"value": "ABCDE1234F", "confidence": 0.98, "status": "PRESENT"},
            "holder_full_name": {"value": "RAHUL SHARMA", "confidence": 0.95, "status": "PRESENT"},
            "father_name": {"value": "VIKRAM SHARMA", "confidence": 0.95, "status": "PRESENT"},
            "date_of_birth": {"value": "1990-05-15", "confidence": 0.96, "status": "PRESENT"}
        },
        "visual_observations": [],
        "localized_regions": [
            {"region_type": "ROI_FACE", "bbox": {"x": 50, "y": 100, "width": 150, "height": 180}, "confidence": 0.96}
        ],
        "processing_status": "COMPLETED"
    }

    with patch.object(GeminiDocumentScanner, "api_key", new_callable=PropertyMock, return_value="AIzaSyTestValidKey123"), \
         patch.object(scanner, "_call_gemini_with_sdk", return_value=json.dumps(mock_payload)):
        res = scanner.scan_document(create_test_image_bytes())
        assert res.document_type == "PAN"
        assert res.classification_status == "RECOGNIZED"
        assert res.fields["document_number"].value == "ABCDE1234F"
        assert res.model_used == OFFICIAL_GEMINI_MODEL
        assert res.thinking_level == "HIGH"


# -----------------------------------------------------------------------------
# 2. Compressed PAN image test (WhatsApp/JPEG compression not penalised)
# -----------------------------------------------------------------------------
def test_compressed_pan_image_no_high_risk():
    scanner = GeminiDocumentScanner()
    mock_payload = {
        "document_type": "PAN",
        "classification_status": "RECOGNIZED",
        "image_quality": {"status": "DEGRADED", "issues": ["jpeg_recompression", "minor_compression_artifacts"]},
        "fields": {
            "document_number": {"value": "ABCDE1234F", "confidence": 0.91, "status": "PRESENT"},
            "holder_full_name": {"value": "RAHUL SHARMA", "confidence": 0.88, "status": "PRESENT"}
        },
        "visual_observations": [
            {"finding_type": "GLARE_OR_BLUR", "description": "Global WhatsApp compression noise detected", "severity": "INFO"}
        ],
        "processing_status": "COMPLETED"
    }

    with patch.object(GeminiDocumentScanner, "api_key", new_callable=PropertyMock, return_value="AIzaSyTestValidKey123"), \
         patch.object(scanner, "_call_gemini_with_sdk", return_value=json.dumps(mock_payload)):
        res = scanner.scan_document(create_test_image_bytes())
        assert res.document_type == "PAN"
        
        # Feed into Gate 1 & Gate 3
        g1 = gate1_validator.validate_gate1("PAN", {k: v.value for k, v in res.fields.items()})
        assert g1["gate1_passed"] is True
        
        g3 = gate3_scorer.evaluate_multi_gate(
            gate1_result=g1,
            gate2_result={"gate2_passed": True, "localized_findings": []},
            image_quality_data={"quality_score": 70.0},
            record_verification_data={"status": "NOT_VERIFIED"}
        )
        # MUST NOT be high risk
        assert g3["risk_level"] == "LOW"
        assert g3["risk_score"] < 25.0


# -----------------------------------------------------------------------------
# 3. Masked Aadhaar image test
# -----------------------------------------------------------------------------
def test_masked_aadhaar_image_scan():
    scanner = GeminiDocumentScanner()
    mock_payload = {
        "document_type": "AADHAAR",
        "classification_status": "RECOGNIZED",
        "fields": {
            "document_number": {"value": "XXXX XXXX 9821", "confidence": 0.97, "status": "PRESENT"},
            "holder_full_name": {"value": "ANITA DESHMUKH", "confidence": 0.95, "status": "PRESENT"},
            "date_of_birth": {"value": "1985-11-20", "confidence": 0.94, "status": "PRESENT"}
        },
        "processing_status": "COMPLETED"
    }

    with patch.object(GeminiDocumentScanner, "api_key", new_callable=PropertyMock, return_value="AIzaSyTestValidKey123"), \
         patch.object(scanner, "_call_gemini_with_sdk", return_value=json.dumps(mock_payload)):
        res = scanner.scan_document(create_test_image_bytes())
        assert res.document_type == "AADHAAR"
        assert "XXXX" in res.fields["document_number"].value
        
        # Gate 1 verification of masked Aadhaar
        g1 = gate1_validator.validate_gate1("AADHAAR", {"document_number": res.fields["document_number"].value})
        assert g1["gate1_passed"] is True


# -----------------------------------------------------------------------------
# 4. Passport with readable MRZ
# -----------------------------------------------------------------------------
def test_passport_with_mrz_scan():
    scanner = GeminiDocumentScanner()
    mrz_lines = [
        "P<INDSHARMA<<RAHUL<<<<<<<<<<<<<<<<<<<<<<<<<<",
        "Z839102459IND9208142M3105098<<<<<<<<<<<<<<<00"
    ]
    mock_payload = {
        "document_type": "PASSPORT",
        "classification_status": "RECOGNIZED",
        "fields": {
            "document_number": {"value": "Z83910245", "confidence": 0.99, "status": "PRESENT"},
            "holder_full_name": {"value": "RAHUL SHARMA", "confidence": 0.98, "status": "PRESENT"},
            "nationality": {"value": "IND", "confidence": 0.99, "status": "PRESENT"}
        },
        "mrz": {
            "lines": mrz_lines,
            "document_code": "P",
            "issuing_country": "IND",
            "passport_number": "Z83910245",
            "date_of_birth": "1992-08-14",
            "expiry_date": "2031-05-09",
            "gender": "M"
        },
        "processing_status": "COMPLETED"
    }

    with patch.object(GeminiDocumentScanner, "api_key", new_callable=PropertyMock, return_value="AIzaSyTestValidKey123"), \
         patch.object(scanner, "_call_gemini_with_sdk", return_value=json.dumps(mock_payload)):
        res = scanner.scan_document(create_test_image_bytes())
        assert res.document_type == "PASSPORT"
        assert res.mrz is not None
        assert len(res.mrz.lines) == 2

        # Gate 1 check
        g1 = gate1_validator.validate_gate1("PASSPORT", {k: v.value for k, v in res.fields.items()}, mrz_lines=res.mrz.lines)
        assert g1["gate1_passed"] is True


# -----------------------------------------------------------------------------
# 5. Visa image test
# -----------------------------------------------------------------------------
def test_visa_image_scan():
    scanner = GeminiDocumentScanner()
    mock_payload = {
        "document_type": "VISA",
        "classification_status": "RECOGNIZED",
        "fields": {
            "document_number": {"value": "V12345678", "confidence": 0.93, "status": "PRESENT"},
            "holder_full_name": {"value": "JOHN DOE", "confidence": 0.95, "status": "PRESENT"},
            "expiry_date": {"value": "2027-12-31", "confidence": 0.95, "status": "PRESENT"}
        },
        "processing_status": "COMPLETED"
    }

    with patch.object(GeminiDocumentScanner, "api_key", new_callable=PropertyMock, return_value="AIzaSyTestValidKey123"), \
         patch.object(scanner, "_call_gemini_with_sdk", return_value=json.dumps(mock_payload)):
        res = scanner.scan_document(create_test_image_bytes())
        assert res.document_type == "VISA"
        assert res.fields["document_number"].value == "V12345678"


# -----------------------------------------------------------------------------
# 6. Driving licence image test
# -----------------------------------------------------------------------------
def test_driving_license_image_scan():
    scanner = GeminiDocumentScanner()
    mock_payload = {
        "document_type": "DRIVING_LICENSE",
        "classification_status": "RECOGNIZED",
        "fields": {
            "document_number": {"value": "DL-1420110012345", "confidence": 0.96, "status": "PRESENT"},
            "holder_full_name": {"value": "VIKAS KUMAR", "confidence": 0.94, "status": "PRESENT"},
            "vehicle_class": {"value": "MCWG, LMV", "confidence": 0.92, "status": "PRESENT"}
        },
        "processing_status": "COMPLETED"
    }

    with patch.object(GeminiDocumentScanner, "api_key", new_callable=PropertyMock, return_value="AIzaSyTestValidKey123"), \
         patch.object(scanner, "_call_gemini_with_sdk", return_value=json.dumps(mock_payload)):
        res = scanner.scan_document(create_test_image_bytes())
        assert res.document_type == "DRIVING_LICENSE"
        g1 = gate1_validator.validate_gate1("DRIVING_LICENSE", {"document_number": "DL-1420110012345"})
        assert g1["gate1_passed"] is True


# -----------------------------------------------------------------------------
# 7. Blurry or glare-affected document
# -----------------------------------------------------------------------------
def test_blurry_glare_affected_document():
    scanner = GeminiDocumentScanner()
    mock_payload = {
        "document_type": "PAN",
        "classification_status": "RECOGNIZED",
        "image_quality": {"status": "DEGRADED", "issues": ["severe_laminate_glare"]},
        "fields": {
            "document_number": {"value": "ABCDE1234F", "confidence": 0.92, "status": "PRESENT"},
            "holder_full_name": {"value": None, "confidence": 0.0, "status": "UNREADABLE", "unreadable_reason": "obscured by flash glare"}
        },
        "visual_observations": [
            {"finding_type": "GLARE_OR_BLUR", "description": "Laminate glare over holder name zone", "severity": "INFO"}
        ],
        "processing_status": "COMPLETED"
    }

    with patch.object(GeminiDocumentScanner, "api_key", new_callable=PropertyMock, return_value="AIzaSyTestValidKey123"), \
         patch.object(scanner, "_call_gemini_with_sdk", return_value=json.dumps(mock_payload)):
        res = scanner.scan_document(create_test_image_bytes())
        assert res.image_quality.status == "DEGRADED"
        assert res.fields["holder_full_name"].status == "UNREADABLE"
        assert res.fields["holder_full_name"].value is None


# -----------------------------------------------------------------------------
# 8. Unsupported document
# -----------------------------------------------------------------------------
def test_unsupported_document_scan():
    scanner = GeminiDocumentScanner()
    mock_payload = {
        "document_type": "UNSUPPORTED",
        "classification_status": "UNSUPPORTED",
        "image_quality": {"status": "UNREADABLE", "issues": ["not_an_id_document"]},
        "fields": {},
        "processing_status": "COMPLETED"
    }

    with patch.object(GeminiDocumentScanner, "api_key", new_callable=PropertyMock, return_value="AIzaSyTestValidKey123"), \
         patch.object(scanner, "_call_gemini_with_sdk", return_value=json.dumps(mock_payload)):
        res = scanner.scan_document(create_test_image_bytes())
        assert res.document_type == "UNSUPPORTED"
        assert res.classification_status == "UNSUPPORTED"


# -----------------------------------------------------------------------------
# 9. Gemini timeout handling
# -----------------------------------------------------------------------------
def test_gemini_timeout_handling():
    scanner = GeminiDocumentScanner()
    with patch.object(GeminiDocumentScanner, "api_key", new_callable=PropertyMock, return_value="AIzaSyTestValidKey123"), \
         patch.object(scanner, "_call_gemini_with_sdk", side_effect=TimeoutError("Request timed out")), \
         patch.object(scanner, "_call_gemini_with_rest", side_effect=TimeoutError("REST timed out")):
        res = scanner.scan_document(create_test_image_bytes(), timeout=0.1)
        assert res.processing_status == "LOCAL_FALLBACK"
        assert "timed out" in res.uncertainties[0].lower()


# -----------------------------------------------------------------------------
# 10. Invalid Gemini JSON handling
# -----------------------------------------------------------------------------
def test_invalid_gemini_json_handling():
    scanner = GeminiDocumentScanner()
    with patch.object(GeminiDocumentScanner, "api_key", new_callable=PropertyMock, return_value="AIzaSyTestValidKey123"), \
         patch.object(scanner, "_call_gemini_with_sdk", return_value="INVALID NON-JSON RESPONSE"):
        res = scanner.scan_document(create_test_image_bytes())
        assert res.processing_status == "PARTIAL"
        assert "Failed to decode model JSON" in res.uncertainties[0]


# -----------------------------------------------------------------------------
# 11. Missing API key handling
# -----------------------------------------------------------------------------
def test_missing_api_key_handling():
    scanner = GeminiDocumentScanner()
    with patch.object(GeminiDocumentScanner, "api_key", new_callable=PropertyMock, return_value=""):
        res = scanner.scan_document(create_test_image_bytes())
        assert res.processing_status == "LOCAL_FALLBACK"
        assert "not configured" in res.uncertainties[0].lower()


# -----------------------------------------------------------------------------
# 12. API rate limit handling (429)
# -----------------------------------------------------------------------------
def test_api_rate_limit_handling():
    scanner = GeminiDocumentScanner()
    with patch.object(GeminiDocumentScanner, "api_key", new_callable=PropertyMock, return_value="AIzaSyTestValidKey123"), \
         patch.object(scanner, "_call_gemini_with_sdk", side_effect=Exception("429 ResourceExhausted: Quota exceeded")), \
         patch.object(scanner, "_call_gemini_with_rest", return_value=None):
        res = scanner.scan_document(create_test_image_bytes())
        assert res.processing_status == "LOCAL_FALLBACK"
        assert "429" in res.uncertainties[0]


# -----------------------------------------------------------------------------
# 13. OCR partial extraction
# -----------------------------------------------------------------------------
def test_ocr_partial_extraction():
    scanner = GeminiDocumentScanner()
    mock_payload = {
        "document_type": "PAN",
        "classification_status": "RECOGNIZED",
        "fields": {
            "document_number": {"value": "ABCDE1234F", "confidence": 0.95, "status": "PRESENT"},
            "holder_full_name": {"value": None, "confidence": 0.0, "status": "UNREADABLE"}
        },
        "processing_status": "COMPLETED"
    }

    with patch.object(GeminiDocumentScanner, "api_key", new_callable=PropertyMock, return_value="AIzaSyTestValidKey123"), \
         patch.object(scanner, "_call_gemini_with_sdk", return_value=json.dumps(mock_payload)):
        res = scanner.scan_document(create_test_image_bytes())
        assert res.fields["document_number"].value == "ABCDE1234F"
        assert res.fields["holder_full_name"].status == "UNREADABLE"


# -----------------------------------------------------------------------------
# 14. False HIGH RISK caused by missing EXIF prevention
# -----------------------------------------------------------------------------
def test_missing_exif_no_high_risk():
    # Valid passport with clean forensics but no EXIF metadata
    g1 = {"gate1_passed": True, "failed_checks": []}
    g2 = {"gate2_passed": True, "localized_findings": [], "metadata_present": False}
    
    g3 = gate3_scorer.evaluate_multi_gate(
        gate1_result=g1,
        gate2_result=g2,
        image_quality_data={"quality_score": 85.0},
        record_verification_data={"status": "NOT_VERIFIED"}
    )
    assert g3["risk_level"] == "LOW"
    assert g3["risk_score"] < 25.0


# -----------------------------------------------------------------------------
# 15. False HIGH RISK caused by ordinary compression prevention
# -----------------------------------------------------------------------------
def test_ordinary_compression_no_high_risk():
    g1 = {"gate1_passed": True, "failed_checks": []}
    g2 = {
        "gate2_passed": True,
        "localized_findings": [],
        "ela_statistics": {"global_ela": 12.5, "delta_z_face": 0.5, "delta_z_text": 0.6}
    }
    
    g3 = gate3_scorer.evaluate_multi_gate(
        gate1_result=g1,
        gate2_result=g2,
        image_quality_data={"quality_score": 68.0},
        record_verification_data={"status": "NOT_VERIFIED"}
    )
    assert g3["risk_level"] == "LOW"
    assert g3["risk_score"] < 25.0


# -----------------------------------------------------------------------------
# 16. Correct display of localized visual findings
# -----------------------------------------------------------------------------
def test_localized_visual_findings_mapping():
    scanner = GeminiDocumentScanner()
    mock_payload = {
        "document_type": "PAN",
        "classification_status": "RECOGNIZED",
        "fields": {
            "document_number": {"value": "ABCDE1234F", "confidence": 0.95, "status": "PRESENT"}
        },
        "visual_observations": [
            {
                "finding_type": "EDITING_BOUNDARY",
                "description": "Potential digital font splicing around date of birth",
                "severity": "HIGH",
                "bbox": {"x": 200, "y": 300, "width": 400, "height": 100},
                "evidence_category": "TYPOGRAPHY",
                "requires_independent_verification": True
            }
        ],
        "processing_status": "COMPLETED"
    }

    with patch.object(GeminiDocumentScanner, "api_key", new_callable=PropertyMock, return_value="AIzaSyTestValidKey123"), \
         patch.object(scanner, "_call_gemini_with_sdk", return_value=json.dumps(mock_payload)):
        res = scanner.scan_document(create_test_image_bytes(w=1000, h=800))
        assert len(res.visual_observations) == 1
        obs = res.visual_observations[0]
        assert obs.finding_type == "EDITING_BOUNDARY"
        assert obs.bbox["x"] == 200
        assert obs.requires_independent_verification is True
