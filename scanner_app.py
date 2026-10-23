# ==============================================================================
# Universal Image Scanner — Streamlit User Interface & Presentation Layer
# Multi-platform: Streamlit Cloud, Local, Containerized (Render/Docker)
# Features: Contour detection, Perspective warp, Enhancements, OCR, QR/Barcode,
#           Sensitive PII Masking, Security Validation, Non-authenticity Disclaimers
# ==============================================================================

import os
import cv2
import numpy as np
from PIL import Image

try:
    import streamlit as st
except ImportError:
    st = None

# Re-export all core functionality from the Streamlit-independent core module
from scanner_core import (
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
    get_tesseract_cmd,
    logger,
    MAX_FILE_SIZE_MB,
    MIN_DIMENSION,
    MAX_DIMENSION,
    PYTESSERACT_AVAILABLE,
    PYZBAR_AVAILABLE,
    RAPIDOCR_AVAILABLE,
    pyzbar_decode,
    rapid_ocr_engine,
)

__all__ = [
    "validate_image_bytes",
    "order_points",
    "validate_quadrilateral",
    "find_document_contour",
    "scan_document",
    "enhance_image",
    "clean_text",
    "mask_sensitive_data",
    "detect_document_type",
    "extract_fields",
    "read_codes",
    "extract_text",
    "get_tesseract_cmd",
    "logger",
    "MAX_FILE_SIZE_MB",
    "MIN_DIMENSION",
    "MAX_DIMENSION",
    "PYTESSERACT_AVAILABLE",
    "PYZBAR_AVAILABLE",
    "RAPIDOCR_AVAILABLE",
    "pyzbar_decode",
    "rapid_ocr_engine",
    "main",
]

# ---------------- STREAMLIT USER INTERFACE ----------------

def main():
    if st is None:
        raise ImportError(
            "Streamlit is required to launch the interactive scanner UI. "
            "Please install it using: pip install streamlit"
        )

    st.set_page_config(
        page_title="Universal Image Scanner | TRUST-ID",
        page_icon="📷",
        layout="wide"
    )

    st.title("📷 Universal Image Scanner")
    st.caption("AI-Assisted Document Scanning, Perspective Correction, OCR & Forensic Data Extraction.")

    # Mandatory Legal & Forensic Disclaimer
    st.info(
        "🛡️ **Compliance & Authenticity Notice**: Visual contour detection and OCR classification extract visible text from "
        "the uploaded image. They do NOT verify legal validity or detect physical document tampering. All sensitive identity "
        "numbers (Aadhaar, PAN) are automatically masked in accordance with data privacy guidelines."
    )

    uploaded_file = st.file_uploader(
        "Upload a document or photo",
        type=["jpg", "jpeg", "png", "webp", "bmp"],
        help=f"Supported: JPG, PNG, WEBP, BMP. Max file size: {MAX_FILE_SIZE_MB}MB."
    )

    if uploaded_file is None:
        st.write("---")
        col_info1, col_info2, col_info3 = st.columns(3)
        with col_info1:
            st.markdown("### 📐 Step 1: Detect")
            st.write("Automatic document quadrilateral detection and geometric perspective unwarping.")
        with col_info2:
            st.markdown("### 🔍 Step 2: Enhance & OCR")
            st.write("Bilingual English/Hindi text recognition with adaptive high-contrast binarization.")
        with col_info3:
            st.markdown("### 🔒 Step 3: Privacy")
            st.write("Automatic client-side masking of UIDAI Aadhaar, PAN, and phone numbers.")
        return

    # Process and validate uploaded file
    file_bytes = uploaded_file.read()
    valid, err_msg, original = validate_image_bytes(file_bytes)

    if not valid or original is None:
        st.error(f"❌ Upload Error: {err_msg}")
        return

    # Document contour detection and perspective warp
    scanned, document_detected = scan_document(original)

    st.subheader("⚙️ Scanning & Enhancement Options")
    col_a, col_b, col_c = st.columns(3)

    with col_a:
        enhancement = st.selectbox(
            "Output Style",
            ["Color", "Gray", "Black & White", "Sharp"],
            index=0
        )

    with col_b:
        run_ocr = st.checkbox("Extract Text (OCR)", value=True)

    with col_c:
        read_qr = st.checkbox("Read QR / Barcode", value=True)

    mode_map = {
        "Color": "color",
        "Gray": "gray",
        "Black & White": "black_white",
        "Sharp": "sharp"
    }

    final_image = enhance_image(scanned, mode_map[enhancement])

    # Side-by-side image display
    st.write("---")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Original Upload")
        st.image(cv2.cvtColor(original, cv2.COLOR_BGR2RGB), use_container_width=True)

    with col2:
        st.markdown("#### Scanned & Enhanced Output")
        if len(final_image.shape) == 2:
            st.image(final_image, use_container_width=True, channels="GRAY")
        else:
            st.image(cv2.cvtColor(final_image, cv2.COLOR_BGR2RGB), use_container_width=True)

    if document_detected:
        st.success("✅ Document border detected: perspective corrected and cropped.")
    else:
        st.warning("⚠️ Document border was not clearly isolated from the background. Showing enhanced full image.")

    # QR / Barcode results
    if read_qr:
        codes, qr_err = read_codes(scanned)
        if codes:
            st.markdown("### 📱 QR & Barcode Results")
            for idx, code in enumerate(codes, 1):
                with st.expander(f"Code #{idx}: {code['type']}", expanded=True):
                    st.code(code["data"], language="text")
        elif qr_err:
            st.caption(f"ℹ️ {qr_err}")

    # OCR extraction results
    if run_ocr:
        st.markdown("### 📝 Extracted Information")
        with st.spinner("Extracting text and detecting fields..."):
            raw_text, ocr_warning = extract_text(scanned)
            cleaned = clean_text(raw_text)
            masked = mask_sensitive_data(cleaned)
            doc_type = detect_document_type(cleaned)
            fields = extract_fields(cleaned)

        if ocr_warning:
            st.caption(f"ℹ️ {ocr_warning}")

        col_meta1, col_meta2 = st.columns([1, 2])
        with col_meta1:
            st.metric("Detected Document Type", doc_type)

        with col_meta2:
            st.markdown("**Structured Fields Extracted:**")
            if fields:
                for k, v in fields.items():
                    st.markdown(f"- **{k}:** `{v}`")
            else:
                st.caption("No standard identity fields found.")

        st.markdown("#### Extracted Text (Sensitive Data Masked)")
        st.text_area("OCR Result", masked if masked else "(No readable text extracted)", height=240)

        # Download buttons
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            if masked:
                st.download_button(
                    "📥 Download Masked Text (.txt)",
                    data=masked,
                    file_name="scanned_document_masked.txt",
                    mime="text/plain",
                    use_container_width=True
                )
        with col_dl2:
            success, enc_jpg = cv2.imencode(".jpg", final_image)
            if success:
                st.download_button(
                    "📥 Download Scanned Image (.jpg)",
                    data=enc_jpg.tobytes(),
                    file_name="scanned_document.jpg",
                    mime="image/jpeg",
                    use_container_width=True
                )

if __name__ == "__main__":
    main()
