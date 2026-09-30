import os
import cv2
import numpy as np
from PIL import Image, ImageOps
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

class ImagePreprocessingPipeline:
    """
    Production-grade document image preprocessor fulfilling Section 5:
    1. Decode image
    2. Validate image
    3. Correct EXIF orientation
    4. Convert to RGB/BGR
    5. Detect document boundary
    6. Crop document if necessary
    7. Correct perspective if possible
    8. Resize for OCR
    9. Improve contrast (CLAHE)
    10. Denoise
    11. Sharpen carefully
    12. Create OCR-optimized image + dedicated MRZ region
    """

    def process(self, image_path: str) -> Dict[str, Any]:
        path = Path(image_path)
        if not path.exists():
            return {
                "success": False,
                "error": "File does not exist",
                "image": None,
                "ocr_image": None,
                "mrz_image": None,
                "metadata": {}
            }

        # 1. Decode image & 3. Correct EXIF orientation using Pillow
        try:
            pil_img = Image.open(path)
            pil_img = ImageOps.exif_transpose(pil_img)
            # Ensure RGB
            if pil_img.mode != "RGB":
                pil_img = pil_img.convert("RGB")
            # 4. Convert to OpenCV BGR
            img_rgb = np.array(pil_img)
            img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
        except Exception as e:
            # Fallback to direct OpenCV reading
            img_bgr = cv2.imread(str(path))
            if img_bgr is None:
                return {
                    "success": False,
                    "error": f"Failed to decode image: {e}",
                    "image": None,
                    "ocr_image": None,
                    "mrz_image": None,
                    "metadata": {}
                }

        # 2. Validate image
        orig_h, orig_w = img_bgr.shape[:2]
        if orig_h < 50 or orig_w < 50:
            return {
                "success": False,
                "error": "Image dimensions too small for OCR processing",
                "image": img_bgr,
                "ocr_image": img_bgr,
                "mrz_image": None,
                "metadata": {"width": orig_w, "height": orig_h}
            }

        metadata: Dict[str, Any] = {
            "original_width": orig_w,
            "original_height": orig_h,
            "perspective_corrected": False,
            "cropped": False,
            "resized": False
        }

        # 5, 6, 7. Detect document boundary, crop and correct perspective if prominent
        deskewed_bgr, was_deskewed = self._detect_boundary_and_warp(img_bgr)
        metadata["perspective_corrected"] = was_deskewed

        working_img = deskewed_bgr if was_deskewed else img_bgr
        h, w = working_img.shape[:2]

        # 8. Resize for OCR
        # Target standard width: 1400px - 2200px where OCR-B characters and text are sharpest
        target_w = w
        target_h = h
        if w < 1000:
            scale = 1400.0 / float(w)
            target_w = int(w * scale)
            target_h = int(h * scale)
            working_img = cv2.resize(working_img, (target_w, target_h), interpolation=cv2.INTER_CUBIC)
            metadata["resized"] = True
        elif w > 2800:
            scale = 2200.0 / float(w)
            target_w = int(w * scale)
            target_h = int(h * scale)
            working_img = cv2.resize(working_img, (target_w, target_h), interpolation=cv2.INTER_AREA)
            metadata["resized"] = True

        h, w = working_img.shape[:2]

        # 9. Improve contrast using CLAHE in LAB color space (preserves natural chrominance)
        lab = cv2.cvtColor(working_img, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.2, tileGridSize=(8, 8))
        cl = clahe.apply(l_channel)
        merged_lab = cv2.merge((cl, a_channel, b_channel))
        contrast_enhanced = cv2.cvtColor(merged_lab, cv2.COLOR_LAB2BGR)

        # 10. Denoise with edge-preserving bilateral filter
        denoised = cv2.bilateralFilter(contrast_enhanced, d=5, sigmaColor=35, sigmaSpace=35)

        # 11. Sharpen carefully using unsharp masking (no harsh halos)
        gaussian = cv2.GaussianBlur(denoised, (0, 0), sigmaX=1.5)
        sharpened = cv2.addWeighted(denoised, 1.35, gaussian, -0.35, 0)

        # 12. Create OCR-optimized image & dedicated MRZ region
        # MRZ zone: typically bottom 22% - 32% of standard ID / Passport documents
        mrz_top = int(h * 0.68)
        mrz_roi = sharpened[mrz_top:h, 0:w]

        # Further optimize MRZ ROI for OCR-B character readability
        mrz_gray = cv2.cvtColor(mrz_roi, cv2.COLOR_BGR2GRAY)
        mrz_clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(6, 6))
        mrz_enhanced = mrz_clahe.apply(mrz_gray)
        # Gentle median blur to clean background noise
        mrz_clean = cv2.medianBlur(mrz_enhanced, 3)
        mrz_bgr = cv2.cvtColor(mrz_clean, cv2.COLOR_GRAY2BGR)

        metadata["processed_width"] = w
        metadata["processed_height"] = h

        return {
            "success": True,
            "image": working_img,
            "ocr_image": sharpened,
            "mrz_image": mrz_bgr,
            "metadata": metadata
        }

    def _detect_boundary_and_warp(self, img: np.ndarray) -> Tuple[np.ndarray, bool]:
        """
        Attempts to detect rectangular document boundary and correct perspective.
        If quadrilateral detection is ambiguous, safely returns original image.
        """
        try:
            h, w = img.shape[:2]
            img_area = float(h * w)

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            edges = cv2.Canny(blurred, 50, 150)

            # Dilate edges slightly to close gaps
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            dilated = cv2.dilate(edges, kernel, iterations=1)

            contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if not contours:
                return img, False

            # Sort contours by area descending
            sorted_contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]

            for cnt in sorted_contours:
                area = cv2.contourArea(cnt)
                # Must occupy at least 30% of image area to be considered a document outline
                if area < img_area * 0.30:
                    continue

                peri = cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)

                if len(approx) == 4 and cv2.isContourConvex(approx):
                    pts = approx.reshape(4, 2)
                    warped = self._four_point_transform(img, pts)
                    wh, ww = warped.shape[:2]
                    # Verify reasonable aspect ratio for identity credentials (between 1.1 and 1.8)
                    aspect = float(ww) / float(wh) if wh > 0 else 0
                    if 1.05 <= aspect <= 2.2:
                        return warped, True
        except Exception:
            pass

        return img, False

    @staticmethod
    def _order_points(pts: np.ndarray) -> np.ndarray:
        # pts shape (4, 2) -> returns top-left, top-right, bottom-right, bottom-left
        rect = np.zeros((4, 2), dtype="float32")
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]

        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        return rect

    def _four_point_transform(self, image: np.ndarray, pts: np.ndarray) -> np.ndarray:
        rect = self._order_points(pts)
        (tl, tr, br, bl) = rect

        # Width of new image
        width_a = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        width_b = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        max_w = max(int(width_a), int(width_b))

        # Height of new image
        height_a = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        height_b = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        max_h = max(int(height_a), int(height_b))

        dst = np.array([
            [0, 0],
            [max_w - 1, 0],
            [max_w - 1, max_h - 1],
            [0, max_h - 1]
        ], dtype="float32")

        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(image, M, (max_w, max_h))
        return warped

image_preprocessor = ImagePreprocessingPipeline()
