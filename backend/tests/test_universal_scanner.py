import pytest
import numpy as np
import cv2
from PIL import Image
import io

from scanner_app import (
    validate_image_bytes,
    order_points,
    validate_quadrilateral,
    find_document_contour,
    scan_document,
    enhance_image,
    clean_text,
    mask_sensitive_data,
    detect_document_type,
    extract_fields,
    read_codes,
    extract_text,
)

def test_validate_image_bytes_valid_jpeg():
    # Create valid synthetic RGB image
    img = np.full((300, 300, 3), 128, dtype=np.uint8)
    _, enc = cv2.imencode(".jpg", img)
    valid, err, decoded = validate_image_bytes(enc.tobytes())
    assert valid is True
    assert err is None
    assert decoded is not None
    assert decoded.shape == (300, 300, 3)

def test_validate_image_bytes_empty_and_corrupt():
    # Empty
    valid, err, _ = validate_image_bytes(b"")
    assert valid is False
    assert "empty" in err.lower()

    # Corrupt
    valid, err, _ = validate_image_bytes(b"\xff\xd8\xffcorrupteddatahere")
    assert valid is False

def test_validate_image_bytes_min_dimension_rejection():
    tiny = np.full((50, 50, 3), 255, dtype=np.uint8)
    _, enc = cv2.imencode(".png", tiny)
    valid, err, _ = validate_image_bytes(enc.tobytes())
    assert valid is False
    assert "too small" in err.lower()

def test_mask_sensitive_data():
    sample = (
        "Name: John Doe\n"
        "Aadhaar Number: 1234 5678 9012\n"
        "PAN: ABCDE1234F\n"
        "Mobile: +91 9876543210\n"
    )
    masked = mask_sensitive_data(sample)

    # Aadhaar masked
    assert "1234 5678 9012" not in masked
    assert "XXXX XXXX 9012" in masked

    # PAN masked
    assert "ABCDE1234F" not in masked
    assert "XXXXX0000X" in masked

    # Phone masked
    assert "9876543210" not in masked
    assert "XXXXXX9999" in masked

def test_detect_document_type():
    assert detect_document_type("Government of India Unique Identification Authority of India UIDAI") == "Aadhaar Card"
    assert detect_document_type("INCOME TAX DEPARTMENT PERMANENT ACCOUNT NUMBER CARD") == "PAN Card"
    assert detect_document_type("ELECTION COMMISSION OF INDIA ELECTOR PHOTO IDENTITY CARD") == "Voter ID"
    assert detect_document_type("UNION OF INDIA DRIVING LICENCE TRANSPORT DEPARTMENT") == "Driving Licence"
    assert detect_document_type("REPUBLIC OF INDIA PASSPORT") == "Passport"
    assert detect_document_type("TAX INVOICE GSTIN TOTAL AMOUNT DUE") == "Invoice / Bill"
    assert detect_document_type("Random notes or textbook page") == "General Document"

def test_extract_fields():
    text = (
        "Government of India\n"
        "Name: Pranav Sharma\n"
        "DOB: 15/08/1995\n"
        "Gender: Male\n"
        "ABCDE1234F\n"
        "5555 6666 7777\n"
    )
    fields = extract_fields(text)
    assert fields.get("Name") == "Pranav Sharma"
    assert fields.get("Date of Birth") == "15/08/1995"
    assert fields.get("Gender") == "Male"
    assert "PROTECTED" in fields.get("PAN", "")
    assert "PROTECTED" in fields.get("Aadhaar", "")

def test_contour_detection_and_perspective_warp():
    # Create background image with a bright document rectangle placed inside
    bg = np.zeros((600, 800, 3), dtype=np.uint8)
    # Draw white document quad
    pts = np.array([[100, 100], [700, 120], [680, 500], [120, 480]], dtype=np.int32)
    cv2.fillPoly(bg, [pts], (255, 255, 255))

    contour = find_document_contour(bg)
    assert contour is not None
    assert len(contour) == 4

    scanned, detected = scan_document(bg)
    assert detected is True
    assert scanned.shape[0] > 0 and scanned.shape[1] > 0

def test_enhance_image_modes():
    img = np.full((200, 200, 3), 150, dtype=np.uint8)
    cv2.putText(img, "TEST", (30, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (20, 20, 20), 2)

    gray = enhance_image(img, "gray")
    assert len(gray.shape) == 2

    bw = enhance_image(img, "black_white")
    assert len(bw.shape) == 2

    sharp = enhance_image(img, "sharp")
    assert sharp.shape == img.shape

def test_read_codes_non_crashing():
    # Plain image should return empty list without crashing
    plain = np.full((200, 200, 3), 255, dtype=np.uint8)
    codes, err = read_codes(plain)
    assert isinstance(codes, list)
    assert len(codes) == 0

def test_extract_text_graceful():
    # Plain image text extraction should not raise an unhandled exception
    plain = np.full((200, 200, 3), 255, dtype=np.uint8)
    text, note = extract_text(plain)
    assert isinstance(text, str)
