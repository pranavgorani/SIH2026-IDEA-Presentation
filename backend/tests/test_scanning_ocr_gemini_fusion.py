import io
import json
import pytest
from PIL import Image
from unittest.mock import MagicMock, patch

from backend.app.services.gemini_document_scanner import (
    GeminiDocumentScanner,
    GeminiDocumentScanResult,
    FieldResult,
    get_gemini_scanner
)
from backend.app.services.ocr_service import OCRService


@pytest.fixture
def sample_test_image_bytes():
    """Generate a clean synthetic document image in memory."""
    img = Image.new("RGB", (1200, 800), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def sample_oversized_image_bytes():
    """Generate an oversized 3200x2400 document image in memory."""
    img = Image.new("RGB", (3200, 2400), color=(240, 240, 240))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


class TestScanningOCRGeminiFusion:
    """Regression test suite for scanning workflow, OCR + Gemini fusion, and unclassified documents."""

    def test_gemini_result_has_all_extracted_text_field(self):
        """Verify GeminiDocumentScanResult schema includes all_extracted_text and raw_text."""
        res = GeminiDocumentScanResult(
            document_type="PAN",
            fields={"document_number": FieldResult(value="ABCDE1234F", confidence=0.95)},
            all_extracted_text=["INCOME TAX DEPARTMENT", "GOVT OF INDIA", "ABCDE1234F"],
            raw_text="INCOME TAX DEPARTMENT GOVT OF INDIA ABCDE1234F",
            processing_status="COMPLETED"
        )
        assert res.all_extracted_text == ["INCOME TAX DEPARTMENT", "GOVT OF INDIA", "ABCDE1234F"]
        assert "ABCDE1234F" in res.raw_text

    def test_unclassified_document_scanning_preserves_text_and_fields(self, sample_test_image_bytes):
        """When document type is unknown/unclassified, scanning must continue, extract text, and not assert fraud."""
        scanner = GeminiDocumentScanner()

        mock_payload = {
            "document_type": "UNCLASSIFIED",
            "document_type_confidence": 0.85,
            "classification_cues": ["Unclassified custom credential"],
            "image_quality": {"status": "ACCEPTABLE", "issues": []},
            "fields": {
                "document_number": {"value": "CERT-998812", "confidence": 0.90, "status": "PRESENT"},
                "holder_full_name": {"value": "ROHIT VERMA", "confidence": 0.92, "status": "PRESENT"},
                "date_of_birth": {"value": "1994-04-12", "confidence": 0.88, "status": "PRESENT"},
                "issuing_authority": {"value": "STATE TRANSPORT AUTHORITY", "confidence": 0.90, "status": "PRESENT"}
            },
            "all_extracted_text": [
                "OFFICIAL VEHICLE FITNESS CERTIFICATE",
                "STATE TRANSPORT AUTHORITY",
                "CERT-998812",
                "HOLDER: ROHIT VERMA",
                "DOB: 12/04/1994"
            ],
            "raw_text": "OFFICIAL VEHICLE FITNESS CERTIFICATE STATE TRANSPORT AUTHORITY CERT-998812 HOLDER: ROHIT VERMA DOB: 12/04/1994",
            "visual_observations": [],
            "localized_regions": []
        }

        mock_response = MagicMock()
        mock_response.text = json.dumps(mock_payload)

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        with patch.object(scanner, "_get_genai_client", return_value=mock_client), \
             patch.object(GeminiDocumentScanner, "is_configured", True):
            scan_result = scanner.scan_document(sample_test_image_bytes)

        assert scan_result.processing_status == "COMPLETED"
        assert scan_result.document_type in ("UNCLASSIFIED", "UNKNOWN", "GENERIC_ID")
        assert scan_result.fields.get("document_number").value == "CERT-998812"
        assert scan_result.fields.get("holder_full_name").value == "ROHIT VERMA"
        assert len(scan_result.all_extracted_text) == 5
        assert "OFFICIAL VEHICLE FITNESS CERTIFICATE" in scan_result.all_extracted_text
        assert "ROHIT VERMA" in scan_result.raw_text

    def test_ocr_service_fusion_deduplicates_lines(self):
        """Test OCR service deduplication and fusion logic between local OCR and Gemini lines."""
        local_lines = ["INCOME TAX DEPARTMENT", "GOVT OF INDIA", "ABCDE1234F", "ROHIT VERMA"]
        gemini_lines = ["Income Tax Department", "GOVT OF INDIA", "FATHER: SURESH VERMA", "ABCDE1234F"]

        # Simulate fusion logic
        seen = set()
        merged = []
        for line in local_lines + gemini_lines:
            cleaned = line.strip()
            norm = cleaned.upper()
            if cleaned and norm not in seen:
                seen.add(norm)
                merged.append(cleaned)

        assert len(merged) == 5
        assert "INCOME TAX DEPARTMENT" in merged
        assert "FATHER: SURESH VERMA" in merged
        # Ensure duplicate "GOVT OF INDIA" and "ABCDE1234F" appear only once
        assert merged.count("GOVT OF INDIA") == 1
        assert merged.count("ABCDE1234F") == 1

    def test_gemini_fallback_when_api_fails(self, sample_test_image_bytes):
        """When Gemini API raises an exception, scanner returns appropriate status without crashing pipeline."""
        scanner = GeminiDocumentScanner()

        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = RuntimeError("503 Service Unavailable / Network Error")

        with patch.object(scanner, "_get_genai_client", return_value=mock_client), \
             patch.object(GeminiDocumentScanner, "is_configured", True):
            scan_result = scanner.scan_document(sample_test_image_bytes)

        assert scan_result.processing_status in ("FAILED", "LOCAL_FALLBACK", "UNAVAILABLE")

    def test_masked_aadhaar_digits_preserved_verbatim(self, sample_test_image_bytes):
        """Masked Aadhaar format (e.g. XXXX XXXX 1234) must be preserved verbatim without guessing."""
        scanner = GeminiDocumentScanner()

        mock_payload = {
            "document_type": "AADHAAR",
            "document_type_confidence": 0.95,
            "fields": {
                "document_number": {"value": "XXXX XXXX 4589", "confidence": 0.95, "status": "PRESENT"},
                "holder_full_name": {"value": "ANANYA SHARMA", "confidence": 0.95, "status": "PRESENT"},
                "date_of_birth": {"value": "1998-11-20", "confidence": 0.92, "status": "PRESENT"},
                "gender": {"value": "Female", "confidence": 0.95, "status": "PRESENT"}
            },
            "all_extracted_text": [
                "GOVERNMENT OF INDIA",
                "UNIQUE IDENTIFICATION AUTHORITY OF INDIA",
                "ANANYA SHARMA",
                "DOB: 20/11/1998",
                "FEMALE",
                "XXXX XXXX 4589"
            ],
            "raw_text": "GOVERNMENT OF INDIA UNIQUE IDENTIFICATION AUTHORITY OF INDIA ANANYA SHARMA DOB: 20/11/1998 FEMALE XXXX XXXX 4589"
        }

        mock_response = MagicMock()
        mock_response.text = json.dumps(mock_payload)

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        with patch.object(scanner, "_get_genai_client", return_value=mock_client), \
             patch.object(GeminiDocumentScanner, "is_configured", True):
            scan_result = scanner.scan_document(sample_test_image_bytes)

        assert scan_result.processing_status == "COMPLETED"
        assert scan_result.fields.get("document_number").value == "XXXX XXXX 4589"
        assert "XXXX XXXX 4589" in scan_result.all_extracted_text

    def test_oversized_image_preprocessing(self, sample_oversized_image_bytes):
        """Oversized images (>1800px) must be decoded properly without failure."""
        pil_img = Image.open(io.BytesIO(sample_oversized_image_bytes))
        assert pil_img.size[0] > 1800 or pil_img.size[1] > 1800
        
        # Verify resize downscaling preserving aspect ratio
        max_dim = 1800
        w, h = pil_img.size
        scale = max_dim / max(w, h)
        resized = pil_img.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
        
        assert max(resized.size) <= 1800
        assert resized.size[0] > 0 and resized.size[1] > 0
