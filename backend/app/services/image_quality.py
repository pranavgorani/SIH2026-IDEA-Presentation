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

        score = max(5.0, min(100.0, round(score, 1)))
        is_acceptable = score >= 45.0

        recommendation = None
        if not is_acceptable:
            recommendation = "Insufficient Image Quality — Re-upload Recommended. Please upload a well-lit, non-blurry, high-resolution document scan."
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
