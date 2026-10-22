import io
import pytest
import numpy as np
from PIL import Image
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.storage_service import storage_service
from backend.app.services.image_quality import image_quality_service
from backend.app.services.record_verification import record_verification_service
from backend.app.services.tamper_detection import tamper_detection_service
from backend.app.core.exceptions import InvalidDocumentException
from backend.app.models.schemas import DocumentField

client = TestClient(app)

def test_storage_magic_byte_validation():
    # Attempt saving arbitrary text pretending to be a PNG
    fake_png = b"THIS IS NOT A VALID PNG HEADER CONTENT"
    with pytest.raises(InvalidDocumentException) as exc_info:
        storage_service.save_upload("test-case-magic", "malicious.png", fake_png)
    assert "corrupted" in str(exc_info.value.message).lower() or "signature" in str(exc_info.value.message).lower()

def test_image_quality_structured_gate():
    # Create a small valid test image
    img = Image.new("RGB", (600, 400), color=(200, 200, 200))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    path, _, _, _, _ = storage_service.save_upload("test-case-q", "quality_test.png", buf.getvalue())
    
    res = image_quality_service.analyze(path)
    assert hasattr(res, "sharpness_score")
    assert hasattr(res, "blur_detected")
    assert hasattr(res, "glare_detected")
    assert hasattr(res, "perspective_status")
    assert hasattr(res, "orientation_status")
    assert hasattr(res, "readable_status")
    assert hasattr(res, "rescan_checklist")
    assert isinstance(res.rescan_checklist, list)

def test_document_field_provenance_model():
    field = DocumentField(
        field_name="holder_full_name",
        raw_value="JOHN DOE",
        normalized_value="JOHN DOE",
        confidence=0.98,
        source="OCR",
        page_number=1,
        validation_status="MATCHED"
    )
    assert field.field_name == "holder_full_name"
    assert field.raw_value == "JOHN DOE"
    assert field.confidence == 0.98
    assert field.source == "OCR"

def test_registry_verification_status_separation():
    # Known test passport in synthetic registry
    res = record_verification_service.verify_record("K81927361", "PASSPORT")
    assert res.verification_status == "SANDBOX_RESULT"
    assert res.record_found is True

    # Bad fake document number
    bad_res = record_verification_service.verify_record("FAKE-NUM-99999", "PASSPORT")
    assert bad_res.verification_status == "NOT_FOUND_BY_PROVIDER"
    assert bad_res.record_found is False

def test_forensic_heatmap_neutral_on_clean_scan():
    # Clean scan should produce a neutral baseline without crashing
    img = Image.new("RGB", (800, 500), color=(240, 240, 240))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    path, _, _, _, _ = storage_service.save_upload("test-clean-case", "clean.png", buf.getvalue())
    
    t_res = tamper_detection_service.analyze_document(path, case_id="test-clean-case")
    assert t_res.tampering_detected is False
    assert t_res.heatmap_url is not None

def test_reviewer_field_correction_flow():
    # Execute a demo scenario first to have a valid case with OCR results
    demo_res = client.post("/api/cases/demo/CASE-001")
    assert demo_res.status_code == 200
    case_id = demo_res.json()["case_id"]

    # Submit a field correction
    correction_payload = {
        "field_name": "name",
        "corrected_value": "SHARMA ARJUN V.",
        "rationale": "Verified against official physical credential embossing.",
        "reviewer_id": "usr-test-officer",
        "reviewer_name": "Senior Verifier Test"
    }
    corr_res = client.post(f"/api/cases/{case_id}/fields/correct", json=correction_payload)
    assert corr_res.status_code == 200
    corr_data = corr_res.json()
    assert corr_data["success"] is True
    assert corr_data["field_name"] == "name"
    assert corr_data["corrected_value"] == "SHARMA ARJUN V."
    assert "SHARMA ARJUN VIKRAM" in corr_data["original_value"]

    # Verify the case detail returns the updated value
    detail_res = client.get(f"/api/cases/{case_id}")
    assert detail_res.status_code == 200
    case_detail = detail_res.json()
    assert case_detail["ocr_result"]["fields"]["name"] == "SHARMA ARJUN V."
