# ==============================================================================
# Universal Image Scanner — Core Image Processing & Forensics Engine
# Independent of Streamlit UI (Import-safe in headless & testing environments)
# Features: Contour detection, Perspective warp, Enhancements, OCR, QR/Barcode,
#           Sensitive PII Masking, Security Validation, Non-authenticity Disclaimers
# ==============================================================================

import os
import re
import shutil
import logging
from typing import Tuple, Optional, Dict, Any, List

import cv2
import numpy as np
from PIL import Image

# Configure quiet logger (NEVER log sensitive document content or PII)
logger = logging.getLogger("universal_scanner")
logger.setLevel(logging.INFO)

# Optional Tesseract OCR & Pyzbar imports with graceful availability detection
PYTESSERACT_AVAILABLE = False
try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    pass

PYZBAR_AVAILABLE = False
try:
    from pyzbar.pyzbar import decode as pyzbar_decode
    PYZBAR_AVAILABLE = True
except (ImportError, Exception):
    pyzbar_decode = None

RAPIDOCR_AVAILABLE = False
try:
    from rapidocr_onnxruntime import RapidOCR
    rapid_ocr_engine = RapidOCR()
    RAPIDOCR_AVAILABLE = True
except Exception:
    rapid_ocr_engine = None

# Configure Tesseract binary path if on Windows or custom path
def get_tesseract_cmd() -> Optional[str]:
    """Locate tesseract executable across common OS paths."""
    which_cmd = shutil.which("tesseract")
    if which_cmd:
        return which_cmd

    common_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Users\AppData\Local\Tesseract-OCR\tesseract.exe",
        "/usr/bin/tesseract",
        "/usr/local/bin/tesseract",
    ]
    for path in common_paths:
        if os.path.exists(path):
            return path
    return None

if PYTESSERACT_AVAILABLE:
    t_cmd = get_tesseract_cmd()
    if t_cmd:
        pytesseract.pytesseract.tesseract_cmd = t_cmd

# ---------------- SECURITY & INPUT VALIDATION ----------------

MAX_FILE_SIZE_MB = 15
MIN_DIMENSION = 100
MAX_DIMENSION = 8000

def validate_image_bytes(file_bytes: bytes, max_mb: int = MAX_FILE_SIZE_MB) -> Tuple[bool, Optional[str], Optional[np.ndarray]]:
    """
    Validates uploaded file size, byte headers, dimensions, and decodes safely.
    Rejects corrupted, oversized, or non-image payloads.
    """
    if not file_bytes or len(file_bytes) == 0:
        return False, "Uploaded file is empty (0 bytes).", None

    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > max_mb:
        return False, f"File size ({size_mb:.1f} MB) exceeds maximum allowed limit ({max_mb} MB).", None

    # Magic byte check for common image formats (JPEG, PNG, WEBP, BMP)
    is_valid_header = (
        file_bytes.startswith(b"\xff\xd8\xff") or  # JPEG
        file_bytes.startswith(b"\x89PNG\r\n\x1a\n") or  # PNG
        (len(file_bytes) > 12 and file_bytes[:4] == b"RIFF" and file_bytes[8:12] == b"WEBP") or  # WEBP
        file_bytes.startswith(b"BM")  # BMP
    )
    if not is_valid_header:
        return False, "Unsupported file format. Please upload a standard JPG, PNG, WEBP, or BMP image.", None

    try:
        np_arr = np.frombuffer(file_bytes, np.uint8)
        image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if image is None or image.size == 0:
            return False, "Failed to decode image. The file may be corrupted.", None

        h, w = image.shape[:2]
        if h < MIN_DIMENSION or w < MIN_DIMENSION:
            return False, f"Image dimensions ({w}x{h}) are too small (minimum {MIN_DIMENSION}x{MIN_DIMENSION} required).", None

        if h > MAX_DIMENSION or w > MAX_DIMENSION:
            return False, f"Image dimensions ({w}x{h}) exceed maximum allowed limit ({MAX_DIMENSION}x{MAX_DIMENSION}).", None

        return True, None, image
    except Exception as exc:
        return False, f"Image processing error: {str(exc)}", None

# ---------------- DOCUMENT DETECTION & WARPING ----------------

def order_points(pts: np.ndarray) -> np.ndarray:
    """
    Orders 4 points in clockwise order: [top-left, top-right, bottom-right, bottom-left].
    """
    pts = pts.reshape(4, 2)
    rect = np.zeros((4, 2), dtype="float32")

    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]

    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]

    return rect

def validate_quadrilateral(pts: np.ndarray, img_area: float) -> bool:
    """
    Verifies that a 4-point contour forms a legitimate document quadrilateral:
    1. Convexity
    2. Minimum area (at least 12% of total image area)
    3. Maximum area (at most 98% of total image area)
    4. Reasonable aspect ratio (between 0.25 and 4.0)
    """
    if not cv2.isContourConvex(pts.astype(np.int32)):
        return False

    quad_area = cv2.contourArea(pts.astype(np.float32))
    area_ratio = quad_area / max(img_area, 1.0)
    if area_ratio < 0.12 or area_ratio > 0.98:
        return False

    # Check edge lengths
    ordered = order_points(pts)
    w1 = np.linalg.norm(ordered[1] - ordered[0])
    w2 = np.linalg.norm(ordered[2] - ordered[3])
    h1 = np.linalg.norm(ordered[3] - ordered[0])
    h2 = np.linalg.norm(ordered[2] - ordered[1])

    avg_w = (w1 + w2) / 2.0
    avg_h = (h1 + h2) / 2.0
    if avg_w < 20 or avg_h < 20:
        return False

    ratio = avg_w / avg_h
    if ratio < 0.25 or ratio > 4.0:
        return False

    return True

def find_document_contour(image: np.ndarray) -> Optional[np.ndarray]:
    """
    Finds document border contour using adaptive Canny edge detection,
    dilation, and strict geometric quadrilateral validation.
    """
    orig_h, orig_w = image.shape[:2]
    total_area = float(orig_h * orig_w)

    scale_width = 800.0
    ratio = orig_w / scale_width
    resized = cv2.resize(image, (int(scale_width), int(orig_h / ratio)))

    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Edge detection
    edges = cv2.Canny(blurred, 40, 160)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    edges = cv2.dilate(edges, kernel, iterations=1)

    contours, _ = cv2.findContours(edges.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:8]

    for contour in contours:
        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)

        if len(approx) == 4:
            scaled_pts = approx.reshape(4, 2) * ratio
            if validate_quadrilateral(scaled_pts, total_area):
                return scaled_pts

    return None

def scan_document(image: np.ndarray) -> Tuple[np.ndarray, bool]:
    """
    Applies perspective transformation if a valid document quadrilateral is detected.
    Falls back cleanly to the original image if no border is detected.
    """
    contour = find_document_contour(image)
    if contour is None:
        return image, False

    ordered = order_points(contour)
    tl, tr, br, bl = ordered

    width_top = np.linalg.norm(tr - tl)
    width_bottom = np.linalg.norm(br - bl)
    width = int(max(width_top, width_bottom))

    height_left = np.linalg.norm(bl - tl)
    height_right = np.linalg.norm(br - tr)
    height = int(max(height_left, height_right))

    # Guard against invalid warp dimensions
    if width < 50 or height < 50:
        return image, False

    destination = np.array([
        [0, 0],
        [width - 1, 0],
        [width - 1, height - 1],
        [0, height - 1]
    ], dtype="float32")

    matrix = cv2.getPerspectiveTransform(ordered, destination)
    scanned = cv2.warpPerspective(image, matrix, (width, height))
    return scanned, True

# ---------------- IMAGE ENHANCEMENT ----------------

def enhance_image(image: np.ndarray, mode: str = "color") -> np.ndarray:
    """
    Applies post-scan enhancements:
    - color: original full color
    - gray: standard grayscale
    - black_white: adaptive Gaussian threshold for clean scanned document look
    - sharp: unsharp masking kernel
    """
    if mode == "gray":
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    if mode == "black_white":
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        filtered = cv2.bilateralFilter(gray, 9, 75, 75)
        result = cv2.adaptiveThreshold(
            filtered,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,
            4
        )
        return result

    if mode == "sharp":
        gaussian = cv2.GaussianBlur(image, (0, 0), 3.0)
        sharp = cv2.addWeighted(image, 1.5, gaussian, -0.5, 0)
        return sharp

    return image

# ---------------- OCR PROCESSING ----------------

def extract_text(image: np.ndarray) -> Tuple[str, Optional[str]]:
    """
    Extracts text using Pytesseract (with English + Hindi) or RapidOCR ONNX fallback.
    Gracefully handles missing language packs, missing binaries, and errors.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape[:2]
    if max(h, w) < 1200:
        gray = cv2.resize(gray, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)

    # 1. Try Pytesseract if available and binary exists
    if PYTESSERACT_AVAILABLE and get_tesseract_cmd():
        try:
            # Try bilingual English + Hindi
            config = "--oem 3 --psm 6 -l eng+hin"
            text = pytesseract.image_to_string(gray, config=config)
            return text.strip(), None
        except Exception as ocr_err:
            err_str = str(ocr_err).lower()
            # If Hindi model missing, fall back to English only
            if "hin" in err_str or "traineddata" in err_str:
                try:
                    config_eng = "--oem 3 --psm 6 -l eng"
                    text = pytesseract.image_to_string(gray, config=config_eng)
                    return text.strip(), "Hindi language pack not installed. OCR processed using English only."
                except Exception as fallback_err:
                    pass

    # 2. Try RapidOCR fallback if available
    if RAPIDOCR_AVAILABLE and rapid_ocr_engine:
        try:
            ocr_results, _ = rapid_ocr_engine(image)
            if ocr_results:
                text_lines = [line[1] for line in ocr_results if len(line) > 1]
                return "\n".join(text_lines).strip(), "Processed via RapidOCR engine (ONNX Runtime)."
        except Exception:
            pass

    # 3. Inform user about missing OCR engine
    return "", "OCR engine (Tesseract or RapidOCR) is not currently installed or available on this system."

def clean_text(text: str) -> str:
    """Removes irregular whitespace and excess blank lines."""
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

# ---------------- QR / BARCODE READING ----------------

def read_codes(image: np.ndarray) -> Tuple[List[Dict[str, str]], Optional[str]]:
    """
    Decodes QR codes and Barcodes via pyzbar.
    Returns decoded code list and any non-fatal error message.
    """
    if not PYZBAR_AVAILABLE or pyzbar_decode is None:
        return [], "ZBar library (pyzbar) is not available in the current environment."

    results = []
    try:
        decoded_objs = pyzbar_decode(image)
        for obj in decoded_objs:
            raw_data = obj.data
            try:
                data_str = raw_data.decode("utf-8")
            except UnicodeDecodeError:
                data_str = raw_data.decode("latin-1", errors="replace")

            # Mask Aadhaar numbers inside QR XML/text if found
            masked_data = mask_sensitive_data(data_str)
            results.append({
                "type": obj.type,
                "data": masked_data
            })
        return results, None
    except Exception as exc:
        return [], f"Barcode / QR scanner error: {str(exc)}"

# ---------------- DOCUMENT CLASSIFICATION & FIELDS ----------------

def detect_document_type(text: str) -> str:
    """Identifies document category based on extracted text patterns."""
    lower = text.lower()

    if "aadhaar" in lower or "uidai" in lower or "आधार" in text:
        return "Aadhaar Card"
    if "income tax department" in lower or "permanent account number" in lower or re.search(r"\b[a-z]{5}\d{4}[a-z]\b", lower):
        return "PAN Card"
    if "election commission" in lower or "voter id" in lower or "elector" in lower:
        return "Voter ID"
    if "driving licence" in lower or "driving license" in lower or "licence no" in lower:
        return "Driving Licence"
    if "passport" in lower or "republic of india" in lower:
        return "Passport"
    if "invoice" in lower or "gstin" in lower or "tax invoice" in lower or "bill to" in lower:
        return "Invoice / Bill"

    return "General Document"

def extract_fields(text: str) -> Dict[str, str]:
    """Extracts common standard identity fields with sensitive data masked."""
    fields = {}

    name = re.search(r"(?:Name|नाम)\s*[:\-]?\s*([A-Za-z .]{3,60})", text, re.IGNORECASE)
    if name:
        fields["Name"] = name.group(1).strip()

    dob = re.search(
        r"(?:DOB|D\.O\.B|Date of Birth|जन्म तिथि)\s*[:\-]?\s*([0-9]{2}[\/\-\.][0-9]{2}[\/\-\.][0-9]{4})",
        text,
        re.IGNORECASE
    )
    if dob:
        fields["Date of Birth"] = dob.group(1)

    gender = re.search(r"\b(Male|Female|Transgender)\b", text, re.IGNORECASE)
    if gender:
        fields["Gender"] = gender.group(1).title()

    if re.search(r"\b[A-Z]{5}\d{4}[A-Z]\b", text):
        fields["PAN"] = "Detected — [PROTECTED / MASKED]"

    if re.search(r"\b(?:\d{4}[ -]?\d{4}[ -]?\d{4})\b", text):
        fields["Aadhaar"] = "Detected — [PROTECTED / MASKED]"

    return fields

def mask_sensitive_data(text: str) -> str:
    """
    Masks sensitive personal identification numbers (UIDAI Aadhaar 12-digit,
    Income Tax PAN 10-char, and long phone/account numbers).
    """
    # Mask 12-digit Aadhaar: keep only last 4 digits
    def mask_aadhaar(match):
        clean = match.group(0).replace(" ", "").replace("-", "")
        if len(clean) == 12:
            return f"XXXX XXXX {clean[-4:]}"
        return match.group(0)

    text = re.sub(r"\b(?:\d{4}[ -]?\d{4}[ -]?\d{4})\b", mask_aadhaar, text)

    # Mask PAN: XXXXX0000X format
    text = re.sub(r"\b[A-Z]{5}\d{4}[A-Z]\b", "XXXXX0000X", text)

    # Mask standalone 10-digit phone or bank account numbers
    text = re.sub(r"\b(?:\+91[\-\s]?)?[6-9]\d{9}\b", "XXXXXX9999", text)

    return text
