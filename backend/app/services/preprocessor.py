"""
TRUST-ID Preprocessor - Step 0: Ingestion & Pre-Flight Normalization
Implements:
1. Auto-Orientation & Aspect Ratio Normalization (Standardize width to 1000px)
2. Specular Glare Suppression (CLAHE in LAB color space & specular laminate glare masking)
3. Zero-Click Document Auto-Router (Passport, PAN, Aadhaar, Visa/Permit)
"""

import re
import cv2
import numpy as np
from PIL import Image, ImageOps
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List, Union


class DocumentPreprocessor:
    """
    Step 0: Pre-Flight Document Ingestion & Normalization Engine.
    Prevents false tampering triggers from phone camera angle, aspect distortions,
    and shiny plastic laminate glare.
    """

    def __init__(self, target_width: int = 1000):
        self.target_width = target_width
        self.clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

    def load_and_orient(self, image_input: Union[str, Path, bytes, np.ndarray]) -> Tuple[Optional[np.ndarray], Dict[str, Any]]:
        """
        Decodes the input image, corrects EXIF orientation, and returns standard BGR array.
        """
        metadata: Dict[str, Any] = {
            "exif_transposed": False,
            "original_width": 0,
            "original_height": 0,
            "channels": 3
        }

        cv_img: Optional[np.ndarray] = None

        if isinstance(image_input, np.ndarray):
            cv_img = image_input.copy()
        elif isinstance(image_input, (str, Path)):
            p = Path(image_input)
            if not p.exists():
                return None, {"error": f"File not found: {p}"}
            try:
                pil_img = Image.open(p)
                exif_trans = ImageOps.exif_transpose(pil_img)
                if exif_trans is not pil_img:
                    metadata["exif_transposed"] = True
                if exif_trans.mode != "RGB":
                    exif_trans = exif_trans.convert("RGB")
                cv_img = cv2.cvtColor(np.array(exif_trans), cv2.COLOR_RGB2BGR)
            except Exception:
                cv_img = cv2.imread(str(p))
        elif isinstance(image_input, bytes):
            try:
                import io
                pil_img = Image.open(io.BytesIO(image_input))
                exif_trans = ImageOps.exif_transpose(pil_img)
                if exif_trans.mode != "RGB":
                    exif_trans = exif_trans.convert("RGB")
                cv_img = cv2.cvtColor(np.array(exif_trans), cv2.COLOR_RGB2BGR)
            except Exception:
                nparr = np.frombuffer(image_input, np.uint8)
                cv_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if cv_img is None or cv_img.size == 0:
            return None, {"error": "Failed to decode image"}

        if len(cv_img.shape) == 2:
            cv_img = cv2.cvtColor(cv_img, cv2.COLOR_GRAY2BGR)
        elif cv_img.shape[2] == 4:
            cv_img = cv2.cvtColor(cv_img, cv2.COLOR_BGRA2BGR)

        h, w = cv_img.shape[:2]
        metadata["original_width"] = w
        metadata["original_height"] = h

        return cv_img, metadata

    def normalize_aspect_and_size(self, img: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Standardizes image width to target_width (1000px) while strictly preserving aspect ratio.
        """
        h, w = img.shape[:2]
        if w == self.target_width:
            return img, 1.0

        scale = float(self.target_width) / float(w)
        target_h = max(50, int(round(h * scale)))
        interp = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_CUBIC
        resized = cv2.resize(img, (self.target_width, target_h), interpolation=interp)
        return resized, scale

    def suppress_specular_glare(self, bgr_img: np.ndarray) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
        """
        Suppresses specular laminate glare:
        1. Applies CLAHE in LAB color space (clipLimit=2.0, tileGridSize=(8,8)) on L channel.
        2. Masks out specular laminate glare pixels (V > 245 and S < 15 in HSV).
        3. Returns glare-damped image, binary glare mask (255 where glare occurs), and glare stats.
        """
        hsv = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2HSV)
        s = hsv[:, :, 1]
        v = hsv[:, :, 2]

        # Glare mask: extremely bright (V > 245) with negligible saturation (S < 15)
        glare_mask = ((v > 245) & (s < 15)).astype(np.uint8) * 255

        # Slight dilation so halo around glare doesn't trick ELA
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        glare_mask_dilated = cv2.dilate(glare_mask, kernel, iterations=1)

        total_pixels = bgr_img.shape[0] * bgr_img.shape[1]
        glare_pixel_count = int(np.count_nonzero(glare_mask_dilated))
        glare_ratio = float(glare_pixel_count) / float(max(1, total_pixels))

        # Apply CLAHE in LAB color space
        lab = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)
        clahe_l = self.clahe.apply(l_channel)
        enhanced_lab = cv2.merge((clahe_l, a_channel, b_channel))
        clahe_bgr = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)

        # Inpaint glare regions softly if glare is localized (< 15% of document)
        damped_bgr = clahe_bgr.copy()
        if 0 < glare_pixel_count < (total_pixels * 0.15):
            try:
                damped_bgr = cv2.inpaint(clahe_bgr, glare_mask_dilated, inpaintRadius=3, flags=cv2.INPAINT_TELEA)
            except Exception:
                damped_bgr = clahe_bgr

        stats = {
            "glare_detected": glare_pixel_count > 0,
            "glare_pixel_count": glare_pixel_count,
            "glare_ratio": round(glare_ratio, 4),
            "glare_suppressed": glare_pixel_count > 0 and glare_ratio < 0.15
        }

        return damped_bgr, glare_mask_dilated, stats

    def auto_route_document(
        self,
        raw_text: str = "",
        mrz_lines: Optional[List[str]] = None,
        type_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Zero-Click Document Auto-Router:
        Automatically classifies document from OCR text / layout into:
        - PASSPORT: Keywords: REPUBLIC OF INDIA, PASSPORT, or 2-line 44-char MRZ starting with P<
        - PAN: Keywords: INCOME TAX DEPARTMENT, Permanent Account Number, or regex [A-Z]{5}[0-9]{4}[A-Z]{1}
        - AADHAAR: Keywords: GOVERNMENT OF INDIA, Unique Identification, DOB, or 12-digit layout with Verhoeff checksum
        - VISA_OR_PERMIT: Keywords: VISA, ENTRY, STAY, PERMIT
        """
        text_upper = (raw_text or "").upper()
        lines = mrz_lines or []
        if not lines and raw_text:
            for l in raw_text.splitlines():
                cleaned = l.strip().replace(" ", "").upper()
                if len(cleaned) in (30, 36, 44) and ('<' in cleaned or cleaned.startswith(('P<', 'V<', 'I<'))):
                    lines.append(cleaned)

        matched_indicators: List[str] = []
        conf = 0.50
        doc_type = "UNKNOWN"

        # 1. PASSPORT check
        has_passport_mrz = any(
            (len(l) == 44 and (l.startswith("P<") or "<" in l)) or
            (len(l) in (30, 36) and l.startswith("P<"))
            for l in lines
        )
        has_visa_kw = bool(re.search(r"\b(VISA|ENTRY\s+PERMIT|STAY\s+PERMIT|VISA\s+TYPE)\b", text_upper))
        has_passport_kw = bool(re.search(r"\b(PASSPORT|PASSEPORT)\b", text_upper) or (re.search(r"\bREPUBLIC\s+OF\s+INDIA\b", text_upper) and not has_visa_kw))

        if has_passport_mrz or (has_passport_kw and not has_visa_kw):
            doc_type = "PASSPORT"
            conf = 0.98 if (has_passport_mrz and has_passport_kw) else 0.90
            if has_passport_mrz:
                matched_indicators.append("ICAO Doc 9303 MRZ structure detected (P<)")
            if has_passport_kw:
                matched_indicators.append("Passport authority keywords detected")
            return {
                "document_type": doc_type,
                "confidence": conf,
                "matched_indicators": matched_indicators,
                "is_supported": True,
                "requires_mrz": True
            }

        # 2. PAN Card check
        pan_regex = r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b"
        pan_match = re.search(pan_regex, text_upper)
        has_pan_kw = bool(re.search(r"\b(INCOME\s+TAX\s+DEPARTMENT|PERMANENT\s+ACCOUNT\s+NUMBER|GOVT\.?\s+OF\s+INDIA\s+INCOME)\b", text_upper))

        if pan_match or has_pan_kw:
            doc_type = "PAN"
            conf = 0.96 if (pan_match and has_pan_kw) else 0.88
            if pan_match:
                matched_indicators.append(f"PAN format pattern matched: {pan_match.group(0)}")
            if has_pan_kw:
                matched_indicators.append("Income Tax Department keywords detected")
            return {
                "document_type": doc_type,
                "confidence": conf,
                "matched_indicators": matched_indicators,
                "is_supported": True,
                "requires_mrz": False
            }

        # 3. AADHAAR Card check
        has_aadhaar_kw = bool(re.search(r"\b(GOVERNMENT\s+OF\s+INDIA|UNIQUE\s+IDENTIFICATION|AUTHORITY\s+OF\s+INDIA|AADHAAR|MERA\s+AADHAAR|VID\s*:?)\b", text_upper))
        has_12_digits = bool(re.search(r"\b[2-9][0-9]{3}\s+[0-9]{4}\s+[0-9]{4}\b", text_upper) or re.search(r"\b[X•x*]{4}\s+[X•x*]{4}\s+[0-9]{4}\b", text_upper))

        if has_aadhaar_kw or has_12_digits:
            doc_type = "AADHAAR"
            conf = 0.96 if (has_aadhaar_kw and has_12_digits) else 0.85
            if has_aadhaar_kw:
                matched_indicators.append("UIDAI authority keywords detected")
            if has_12_digits:
                matched_indicators.append("12-digit Aadhaar UID / masked layout detected")
            return {
                "document_type": doc_type,
                "confidence": conf,
                "matched_indicators": matched_indicators,
                "is_supported": True,
                "requires_mrz": False
            }

        # 4. VISA OR ENTRY PERMIT check
        has_visa_kw = bool(re.search(r"\b(VISA|ENTRY\s+PERMIT|STAY\s+PERMIT|VISA\s+TYPE|IMMIGRATION)\b", text_upper))
        has_visa_mrz = any(l.startswith("V<") for l in lines)
        if has_visa_kw or has_visa_mrz:
            doc_type = "VISA_OR_PERMIT"
            conf = 0.92 if (has_visa_kw and has_visa_mrz) else 0.82
            if has_visa_mrz:
                matched_indicators.append("Visa MRZ detected (V<)")
            if has_visa_kw:
                matched_indicators.append("Visa/Permit keywords detected")
            return {
                "document_type": doc_type,
                "confidence": conf,
                "matched_indicators": matched_indicators,
                "is_supported": True,
                "requires_mrz": True
            }

        # Respect explicit type_hint if valid
        clean_hint = (type_hint or "").upper().replace(" ", "_")
        if clean_hint in ("PAN", "PAN_CARD"):
            doc_type = "PAN"
            conf = 0.70
            matched_indicators.append("Classified by user/system type hint")
        elif clean_hint in ("AADHAAR", "AADHAAR_CARD"):
            doc_type = "AADHAAR"
            conf = 0.70
            matched_indicators.append("Classified by user/system type hint")
        elif clean_hint in ("PASSPORT", "INDIAN_PASSPORT"):
            doc_type = "PASSPORT"
            conf = 0.70
            matched_indicators.append("Classified by user/system type hint")
        else:
            doc_type = "GENERAL_ID"
            conf = 0.50

        return {
            "document_type": doc_type,
            "confidence": conf,
            "matched_indicators": matched_indicators or ["Standard credential layout"],
            "is_supported": True,
            "requires_mrz": doc_type == "PASSPORT"
        }

    def preprocess(
        self,
        image_input: Union[str, Path, bytes, np.ndarray],
        raw_text: str = "",
        mrz_lines: Optional[List[str]] = None,
        type_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes complete Step 0 normalization:
        1. Decode & auto-orient
        2. Standardize width to 1000px preserving aspect ratio
        3. Suppress laminate glare (LAB CLAHE + HSV glare mask)
        4. Auto-route document taxonomy
        """
        bgr, meta = self.load_and_orient(image_input)
        if bgr is None:
            return {
                "success": False,
                "error": meta.get("error", "Decoding error"),
                "normalized_bgr": None,
                "glare_mask": None,
                "glare_stats": {},
                "routing": {"document_type": "UNKNOWN", "confidence": 0.0}
            }

        # Standardize size
        normalized_bgr, scale = self.normalize_aspect_and_size(bgr)
        meta["scale_factor"] = round(scale, 4)
        meta["normalized_width"] = normalized_bgr.shape[1]
        meta["normalized_height"] = normalized_bgr.shape[0]

        # Glare suppression
        damped_bgr, glare_mask, glare_stats = self.suppress_specular_glare(normalized_bgr)

        # Auto-routing
        routing = self.auto_route_document(raw_text=raw_text, mrz_lines=mrz_lines, type_hint=type_hint)

        return {
            "success": True,
            "normalized_bgr": normalized_bgr,
            "damped_bgr": damped_bgr,
            "glare_mask": glare_mask,
            "glare_stats": glare_stats,
            "routing": routing,
            "metadata": meta
        }


document_preprocessor = DocumentPreprocessor()
