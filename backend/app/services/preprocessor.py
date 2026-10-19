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

    def denoise_conservative(self, bgr_img: np.ndarray) -> np.ndarray:
        """
        Conservative bilateral filtering: Reduces camera sensor noise while
        strictly preserving fine text edges, guilloche patterns, and stamps.
        """
        try:
            return cv2.bilateralFilter(bgr_img, d=5, sigmaColor=35, sigmaSpace=35)
        except Exception:
            return bgr_img

    def map_bbox_norm_to_orig(self, bbox: Dict[str, int], scale_factor: float, orig_w: Optional[int] = None, orig_h: Optional[int] = None) -> Dict[str, int]:
        """Maps bounding box from normalized image coordinates back to original image space."""
        if not scale_factor or scale_factor <= 0:
            return bbox
        inv_scale = 1.0 / scale_factor
        nx = int(round(bbox.get("x", 0) * inv_scale))
        ny = int(round(bbox.get("y", 0) * inv_scale))
        nw = int(round(bbox.get("width", 0) * inv_scale))
        nh = int(round(bbox.get("height", 0) * inv_scale))
        if orig_w is not None and orig_h is not None:
            nx = max(0, min(orig_w - 1, nx))
            ny = max(0, min(orig_h - 1, ny))
            nw = min(orig_w - nx, nw)
            nh = min(orig_h - ny, nh)
        return {"x": nx, "y": ny, "width": nw, "height": nh}

    def map_bbox_orig_to_norm(self, bbox: Dict[str, int], scale_factor: float, norm_w: Optional[int] = None, norm_h: Optional[int] = None) -> Dict[str, int]:
        """Maps bounding box from original image space to normalized image coordinates."""
        if not scale_factor or scale_factor <= 0:
            return bbox
        nx = int(round(bbox.get("x", 0) * scale_factor))
        ny = int(round(bbox.get("y", 0) * scale_factor))
        nw = int(round(bbox.get("width", 0) * scale_factor))
        nh = int(round(bbox.get("height", 0) * scale_factor))
        if norm_w is not None and norm_h is not None:
            nx = max(0, min(norm_w - 1, nx))
            ny = max(0, min(norm_h - 1, ny))
            nw = min(norm_w - nx, nw)
            nh = min(norm_h - ny, nh)
        return {"x": nx, "y": ny, "width": nw, "height": nh}

    def auto_route_document(
        self,
        raw_text: str = "",
        mrz_lines: Optional[List[str]] = None,
        type_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Zero-Click Document Auto-Router:
        Automatically classifies document from OCR text / layout into:
        - PASSPORT
        - PAN
        - AADHAAR
        - VISA
        - DRIVING_LICENSE
        - GENERIC_ID
        - UNKNOWN
        """
        text_upper = (raw_text or "").upper()
        lines = mrz_lines or []
        if not lines and raw_text:
            for l in raw_text.splitlines():
                cleaned = l.strip().replace(" ", "").upper()
                if len(cleaned) in (30, 36, 44) and ('<' in cleaned or cleaned.startswith(('P<', 'V<', 'I<'))):
                    lines.append(cleaned)

        matched_indicators: List[str] = []
        competing: List[Dict[str, Any]] = []
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
                "competing_classifications": competing,
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
                "competing_classifications": competing,
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
                "competing_classifications": competing,
                "is_supported": True,
                "requires_mrz": False
            }

        # 4. DRIVING LICENCE check
        has_dl_kw = bool(re.search(r"\b(DRIVING\s+LICEN[SC]E|UNION\s+OF\s+INDIA|AUTHORISED\s+TO\s+DRIVE|DL\s*NO|MOTOR\s+VEHICLES?\s+ACT|TRANSPORT\s+DEPARTMENT|SARATHI|PARIVAHAN)\b", text_upper))
        dl_match = re.search(r"\b[A-Z]{2}[-\s]?[0-9]{2}[-\s]?[0-9]{4}[-\s]?[0-9]{7}\b", text_upper)
        if has_dl_kw or dl_match:
            doc_type = "DRIVING_LICENSE"
            conf = 0.95 if (has_dl_kw and dl_match) else 0.85
            if dl_match:
                matched_indicators.append(f"Driving licence identifier pattern matched: {dl_match.group(0)}")
            if has_dl_kw:
                matched_indicators.append("Driving licence regulatory authority labels detected")
            return {
                "document_type": doc_type,
                "confidence": conf,
                "matched_indicators": matched_indicators,
                "competing_classifications": competing,
                "is_supported": True,
                "requires_mrz": False
            }

        # 5. VISA OR ENTRY PERMIT check
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
                "competing_classifications": competing,
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
        elif clean_hint in ("DRIVING_LICENSE", "DRIVING_LICENCE"):
            doc_type = "DRIVING_LICENSE"
            conf = 0.70
            matched_indicators.append("Classified by user/system type hint")
        elif clean_hint in ("VISA", "VISA_OR_PERMIT", "INDIAN_VISA"):
            doc_type = "VISA"
            conf = 0.70
            matched_indicators.append("Classified by user/system type hint")
        elif len(text_upper.strip()) > 30:
            doc_type = "GENERIC_ID"
            conf = 0.55
            matched_indicators.append("General identity card textual layout detected")
        else:
            doc_type = "UNKNOWN"
            conf = 0.10
            matched_indicators.append("No specific credential markers identified")

        is_supported = doc_type not in ("UNKNOWN", "UNSUPPORTED")
        return {
            "document_type": doc_type,
            "confidence": conf,
            "matched_indicators": matched_indicators,
            "competing_classifications": competing,
            "is_supported": is_supported,
            "requires_mrz": doc_type in ("PASSPORT", "VISA")
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
        4. Conservative denoising
        5. Auto-route document taxonomy
        """
        bgr, meta = self.load_and_orient(image_input)
        if bgr is None:
            return {
                "success": False,
                "error": meta.get("error", "Decoding error"),
                "normalized_bgr": None,
                "damped_bgr": None,
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

        # Conservative denoising on normalized working copy
        denoised_bgr = self.denoise_conservative(damped_bgr)

        # Auto-routing
        routing = self.auto_route_document(raw_text=raw_text, mrz_lines=mrz_lines, type_hint=type_hint)

        return {
            "success": True,
            "original_bgr": bgr,
            "normalized_bgr": normalized_bgr,
            "damped_bgr": damped_bgr,
            "denoised_bgr": denoised_bgr,
            "glare_mask": glare_mask,
            "glare_stats": glare_stats,
            "routing": routing,
            "metadata": meta
        }

    def normalize_document(
        self,
        image_input: Union[str, Path, bytes, np.ndarray],
        raw_text: str = "",
        mrz_lines: Optional[List[str]] = None,
        type_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Public Pre-Flight Ingestion & Normalization API:
        Returns normalized BGR image, denoised copy, glare mask, coordinate scale factor,
        and auto-route prediction without altering original forensic source.
        """
        res = self.preprocess(image_input, raw_text=raw_text, mrz_lines=mrz_lines, type_hint=type_hint)
        meta = res.get("metadata", {})
        return {
            "success": res.get("success", True),
            "original_bgr": res.get("original_bgr"),
            "normalized_bgr": res.get("normalized_bgr"),
            "damped_bgr": res.get("damped_bgr"),
            "denoised_bgr": res.get("denoised_bgr"),
            "glare_mask": res.get("glare_mask"),
            "scale_factor": float(meta.get("scale_factor", 1.0)),
            "original_dimensions": (int(meta.get("original_width", 1000)), int(meta.get("original_height", 600))),
            "normalized_dimensions": (int(meta.get("normalized_width", 1000)), int(meta.get("normalized_height", 600))),
            "metadata": meta,
            "glare_details": res.get("glare_stats", {}),
            "transformations_applied": ["auto_orient", "normalize_1000px", "lab_clahe", "bilateral_denoise"],
            "auto_route": res.get("routing", {})
        }


document_preprocessor = DocumentPreprocessor()
