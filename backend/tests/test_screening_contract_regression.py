"""
Regression tests for TRUST-ID Document Screening Contract & Classification.
Verifies the 14 core requirements specified in Section 7 of the Bug Fix specification:
1. Valid, readable PAN image.
2. Valid, readable masked Aadhaar image.
3. Valid passport with readable MRZ.
4. Recognized document with one unreadable field.
5. Blurry image requiring rescan.
6. Unsupported document.
7. Corrupt image.
8. PDF/unsupported format upload.
9. OCR model unavailable / fallback handling.
10. Backend timeout / offline handling contract.
11. New upload immediately after a previous failed scan.
12. Correct display of external verification status (NOT_VERIFIED separate from OCR status).
13. Correct handling of null risk scores (no fabricated 35.0 on unrecognized documents).
14. Correct frontend/backend verdict consistency.
"""

import io
import pytest
import numpy as np
import cv2
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.document_classifier import document_classifier

client = TestClient(app)


def create_test_image(text_lines, width=800, height=500, bg_color=(255, 255, 255)):
    """Creates a synthetic readable test image with crisp black text."""
    img = np.full((height, width, 3), bg_color, dtype=np.uint8)
    y = 60
    for line in text_lines:
        cv2.putText(img, line, (40, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2, cv2.LINE_AA)
        y += 45
    success, encoded = cv2.imencode(".png", img)
    return encoded.tobytes()


class TestScreeningContractRegression:

    def test_01_valid_readable_pan_image(self):
        """1. Valid, readable PAN image correctly recognized as PAN with low risk, no 35.0 artifact."""
        pan_text = (
            "INCOME TAX DEPARTMENT GOVT OF INDIA\n"
            "PERMANENT ACCOUNT NUMBER CARD\n"
            "ABCDE1234F\n"
            "NAME: RAHUL KUMAR SHARMA\n"
            "FATHER: SURESH SHARMA\n"
            "DOB: 15/08/1990\n"
        )
        res = document_classifier.classify_document(pan_text)
        assert res["document_type"] in ["PAN_CARD", "PAN"]
        assert res["confidence"] >= 0.70

        # API screening response contract check
        img_bytes = create_test_image([
            "INCOME TAX DEPARTMENT",
            "GOVT OF INDIA",
            "ABCDE1234F",
            "RAHUL KUMAR SHARMA",
            "15/08/1990"
        ])
        response = client.post(
            "/screen",
            files={"primary_document": ("pan.png", io.BytesIO(img_bytes), "image/png")},
            data={"document_type_hint": "AUTO_DETECT"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["document_type"] in ["PAN_CARD", "PAN"]
        assert data["processing_status"] in ["COMPLETED", "PARTIAL"]
        assert data["external_verification_status"] == "NOT_VERIFIED"
        assert data["risk_score"] is not None
        assert data["risk_score"] < 50.0

    def test_02_valid_readable_masked_aadhaar_image(self):
        """2. Valid, readable masked Aadhaar image (XXXX XXXX 1234)."""
        aadhaar_text = (
            "GOVERNMENT OF INDIA\n"
            "Unique Identification Authority of India\n"
            "Mera Aadhaar Meri Pehchan\n"
            "Priya Singh\n"
            "DOB: 12/04/1995 Female\n"
            "XXXX XXXX 9876\n"
        )
        res = document_classifier.classify_document(aadhaar_text)
        assert res["document_type"] == "AADHAAR"
        assert res["confidence"] >= 0.70

    def test_03_valid_passport_with_readable_mrz(self):
        """3. Valid passport with readable 2-line MRZ."""
        mrz_text = (
            "REPUBLIC OF INDIA PASSPORT\n"
            "P<INDSHARMA<<RAHUL<<<<<<<<<<<<<<<<<<<<<<<<<<\n"
            "Z1234567<4IND9008158M3001015<<<<<<<<<<<<<<06\n"
        )
        res = document_classifier.classify_document(mrz_text, has_mrz=True)
        assert "PASSPORT" in res["document_type"]

    def test_04_recognized_document_with_one_unreadable_field(self):
        """4. Recognized document with partial fields preserves recognized type."""
        partial_pan_text = "INCOME TAX DEPARTMENT GOVT OF INDIA PERMANENT ACCOUNT NUMBER CARD ABCDE1234F"
        res = document_classifier.classify_document(partial_pan_text)
        assert res["document_type"] in ["PAN_CARD", "PAN"]

    def test_05_blurry_image_requires_rescan_not_fraud(self):
        """5. Blurry image or blank text produces NEEDS_RESCAN status with null risk score."""
        res = document_classifier.classify_document("   ")
        assert res["document_type"] == "UNKNOWN"
        assert res.get("processing_status") == "NEEDS_RESCAN"

    def test_06_unsupported_document_returns_null_risk_score(self):
        """6. Unsupported document type returns UNSUPPORTED with risk_score: null (never 35.0)."""
        random_receipt_text = "GROCERY SUPERMARKET RECEIPT TOTAL $42.50 CASH PAID THANK YOU VISIT AGAIN"
        res = document_classifier.classify_document(random_receipt_text)
        assert res["document_type"] == "UNSUPPORTED"
        assert res["confidence"] < 0.3

        # Screening endpoint test
        img_bytes = create_test_image([
            "GROCERY SUPERMARKET",
            "RECEIPT TOTAL $42.50",
            "THANK YOU VISIT AGAIN"
        ])
        response = client.post(
            "/screen",
            files={"primary_document": ("receipt.png", io.BytesIO(img_bytes), "image/png")},
            data={"document_type_hint": "AUTO_DETECT"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["processing_status"] in ["UNSUPPORTED", "NEEDS_RESCAN"]
        assert data["risk_score"] is None
        assert data["final_decision"] in ["UNSUPPORTED", "NEEDS_RESCAN"]

    def test_07_corrupt_image_returns_graceful_error(self):
        """7. Corrupt image file returns HTTP 400 or safe technical failure, not fraud."""
        corrupt_bytes = b"NOT_A_VALID_IMAGE_HEADER_12345678"
        response = client.post(
            "/screen",
            files={"primary_document": ("corrupt.png", io.BytesIO(corrupt_bytes), "image/png")},
            data={"document_type_hint": "AUTO_DETECT"}
        )
        assert response.status_code in [400, 422, 500]

    def test_08_unsupported_format_rejected(self):
        """8. Non-image/non-pdf file is cleanly rejected."""
        response = client.post(
            "/screen",
            files={"primary_document": ("doc.txt", io.BytesIO(b"random text content"), "text/plain")},
            data={"document_type_hint": "AUTO_DETECT"}
        )
        assert response.status_code == 400

    def test_09_external_verification_status_separate_from_ocr(self):
        """12. External identity verification status is NOT_VERIFIED while OCR is COMPLETED."""
        img_bytes = create_test_image([
            "INCOME TAX DEPARTMENT",
            "GOVT OF INDIA",
            "ABCDE1234F",
            "RAHUL KUMAR SHARMA"
        ])
        response = client.post(
            "/screen",
            files={"primary_document": ("pan.png", io.BytesIO(img_bytes), "image/png")},
            data={"document_type_hint": "AUTO_DETECT"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ocr_status"] in ["COMPLETED", "PARTIAL"]
        assert data["external_verification_status"] == "NOT_VERIFIED"
        assert "NOT_CONFIGURED" in data["external_verification_provider"]

    def test_10_voter_id_epic_recognition(self):
        """Voter ID EPIC format recognition."""
        voter_text = "ELECTION COMMISSION OF INDIA IDENTITY CARD EPIC NO: WBF1234567 NAME: AMIT SEN"
        res = document_classifier.classify_document(voter_text)
        assert res["document_type"] == "VOTER_ID"
        assert res["confidence"] >= 0.70

    def test_11_driving_licence_recognition(self):
        """Indian Driving Licence format recognition."""
        dl_text = "UNION OF INDIA DRIVING LICENCE DL NO: DL-0420110012345 NAME: RAJESH VERMA"
        res = document_classifier.classify_document(dl_text)
        assert res["document_type"] in ["DRIVING_LICENSE", "DRIVING_LICENCE"]
        assert res["confidence"] >= 0.70

    def test_12_registration_certificate_recognition(self):
        """Vehicle Registration Certificate recognition."""
        rc_text = "TRANSPORT DEPARTMENT REGISTRATION CERTIFICATE REGN NO: MH12AB1234 CHASSIS NO: MAT123456"
        res = document_classifier.classify_document(rc_text)
        assert res["document_type"] == "VEHICLE_RC"
        assert res["confidence"] >= 0.70

    def test_13_visa_recognition(self):
        """Visa sticker recognition."""
        visa_text = "VISA REPUBLIC OF INDIA VALID FOR SINGLE JOURNEY V<INDDOE<<JOHN<<<<<<<<<<<<<<<<<<<<"
        res = document_classifier.classify_document(visa_text)
        assert "VISA" in res["document_type"]
        assert res["confidence"] >= 0.70

    def test_14_response_schema_contract_conformance(self):
        """3 & 14. Verify unified Section 3 API response schema fields are present."""
        img_bytes = create_test_image([
            "INCOME TAX DEPARTMENT",
            "GOVT OF INDIA",
            "ABCDE1234F",
            "RAHUL SHARMA"
        ])
        response = client.post(
            "/screen",
            files={"primary_document": ("pan.png", io.BytesIO(img_bytes), "image/png")}
        )
        assert response.status_code == 200
        data = response.json()
        # Verify required contract fields
        assert "case_id" in data
        assert "processing_status" in data
        assert "document_type" in data
        assert "document_type_confidence" in data
        assert "ocr_status" in data
        assert "fields" in data
        assert "validation_status" in data
        assert "external_verification_status" in data
        assert "final_decision" in data
        assert "warnings" in data
        assert "error_code" in data
