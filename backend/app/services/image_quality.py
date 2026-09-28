import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Any
from backend.app.models.schemas import ImageQualityResult

class ImageQualityAnalyzer:
    def analyze(self, image_path: str) -> ImageQualityResult:
        """
        Analyzes image quality metrics including blur, glare, lighting, resolution, and contrast.
        Returns ImageQualityResult without declaring low quality as fraudulent.
        """
        path = Path(image_path)
        if not path.exists():
            return ImageQualityResult(
                quality_score=0.0,
                issues=["file_not_found"],
                is_acceptable=False,
                recommendation="File could not be found on server."
            )

        # Read image with OpenCV
        img = cv2.imread(str(path))
        if img is None:
            return ImageQualityResult(
                quality_score=0.0,
                issues=["unreadable_image"],
                is_acceptable=False,
                recommendation="Image format corrupted or unreadable."
            )

        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        issues: List[str] = []
        score = 100.0

        # 1. Resolution Check
        if w < 500 or h < 350:
            issues.append("low_resolution")
            score -= 30.0
        elif w < 800 or h < 550:
            issues.append("suboptimal_resolution")
            score -= 10.0

        # 2. Blur / Sharpness Check (Laplacian Variance)
        laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        if laplacian_var < 50.0:
            issues.append("severe_blur")
            score -= 35.0
        elif laplacian_var < 100.0:
            issues.append("moderate_blur")
            score -= 15.0

        # 3. Glare / Overexposure Check
        # Fraction of pixels with brightness > 250
        glare_ratio = float(np.sum(gray > 250)) / float(gray.size)
        if glare_ratio > 0.08:
            issues.append("severe_glare")
            score -= 25.0
        elif glare_ratio > 0.03:
            issues.append("minor_glare")
            score -= 10.0

        # 4. Under-exposure / Poor Lighting Check
        mean_intensity = float(np.mean(gray))
        if mean_intensity < 40.0:
            issues.append("underexposed_dark")
            score -= 25.0
        elif mean_intensity > 230.0:
            issues.append("overexposed_washed_out")
            score -= 20.0

        # 5. Low Contrast Check
        contrast_std = float(np.std(gray))
        if contrast_std < 25.0:
            issues.append("very_low_contrast")
            score -= 20.0

        # 6. Excessive Compression Check (Blocking / high-frequency drop)
        try:
            # Estimate blockiness across 8x8 JPEG boundaries
            diff_h = np.abs(gray[7::8, :] - gray[8::8, :])
            diff_v = np.abs(gray[:, 7::8] - gray[:, 8::8])
            mean_boundary_delta = (np.mean(diff_h) + np.mean(diff_v)) / 2.0
            if mean_boundary_delta > 18.0:
                issues.append("excessive_compression")
                score -= 15.0
        except Exception:
            pass

        # 7. Rotation / Skew Angle Check
        try:
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=100, minLineLength=w // 4, maxLineGap=20)
            if lines is not None and len(lines) > 5:
                angles = []
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
                    if abs(angle) > 3.0 and abs(angle) < 85.0:
                        angles.append(angle)
                if len(angles) > (len(lines) // 3):
                    issues.append("rotation_detected")
                    score -= 10.0
        except Exception:
            pass

        # 8. Crop Problems / Cut-off Edges Check
        # Check border intensity variance (if document text/details run directly off the canvas edge)
        try:
            border_top = np.mean(gray[0:3, :])
            border_bottom = np.mean(gray[-3:, :])
            border_left = np.mean(gray[:, 0:3])
            border_right = np.mean(gray[:, -3:])
            # If borders have strong dark text pixels touching edge
            edge_pixels = np.concatenate([gray[0, :], gray[-1, :], gray[:, 0], gray[:, -1]])
            dark_edge_ratio = float(np.sum(edge_pixels < 80)) / float(edge_pixels.size)
            if dark_edge_ratio > 0.15:
                issues.append("crop_problems")
                score -= 15.0
        except Exception:
            pass

        # 9. Unreadable Regions Check (Local patch saturation or zero contrast)
        try:
            unreadable_patches = 0
            bh, bw = max(20, h // 6), max(20, w // 6)
            for r in range(0, h - bh, bh):
                for c in range(0, w - bw, bw):
                    patch = gray[r:r+bh, c:c+bw]
                    if np.std(patch) < 4.0 or np.mean(patch) > 252.0:
                        unreadable_patches += 1
            if unreadable_patches > 6:
                issues.append("unreadable_regions")
                score -= 15.0
        except Exception:
            pass

        # 10. Poor Lighting Summary Tag
        if "underexposed_dark" in issues or "overexposed_washed_out" in issues:
            issues.append("poor_lighting")

        score = max(5.0, min(100.0, round(score, 1)))
        is_acceptable = score >= 45.0

        recommendation = None
        if not is_acceptable:
            recommendation = "Insufficient Image Quality — Re-upload Recommended"
        elif len(issues) > 0:
            recommendation = f"Acceptable quality ({score}%). Detected minor factors: {', '.join(issues)}."
        else:
            recommendation = "Image quality is optimal for AI forensic analysis."

        return ImageQualityResult(
            quality_score=score,
            issues=issues,
            is_acceptable=is_acceptable,
            recommendation=recommendation
        )

image_quality_service = ImageQualityAnalyzer()
