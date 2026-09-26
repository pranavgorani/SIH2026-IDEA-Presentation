import os
import io
import re
import shutil
import hashlib
from pathlib import Path
from typing import Tuple, Optional
from PIL import Image, ImageOps
from backend.app.core.config import settings

class StorageService:
    def __init__(self, base_dir: Path = settings.STORAGE_DIR):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        (self.base_dir / "heatmaps").mkdir(parents=True, exist_ok=True)
        (self.base_dir / "synthetic").mkdir(parents=True, exist_ok=True)

    def save_upload(self, case_id: str, filename: str, content: bytes) -> Tuple[str, str, int, int, int]:
        """
        Saves uploaded file securely under case-specific directory.
        Normalizes image formats (PNG, JPG, JPEG, WEBP), handles EXIF orientation,
        and converts transparent/alpha channels to standard RGB for OpenCV compatibility.
        Detects PDF files and returns a clean explanation if PDF engine is not active.
        
        Returns:
            (saved_file_path, sha256_hash, file_size_bytes, width, height)
        """
        if not content:
            raise ValueError("Uploaded file is empty.")

        # Check for file size limit (25MB)
        if len(content) > 25 * 1024 * 1024:
            raise ValueError("Uploaded file exceeds the maximum allowed size of 25MB.")

        # Check for PDF magic bytes (%PDF)
        if content.startswith(b"%PDF") or filename.lower().endswith(".pdf"):
            raise ValueError("PDF processing is not enabled in this deployment.")

        case_dir = self.base_dir / case_id
        case_dir.mkdir(parents=True, exist_ok=True)

        # 1. Sanitize filename safely without evaluating code or directory traversal
        base_name = Path(filename).name
        clean_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', base_name)
        if not clean_name:
            clean_name = "document.png"
        
        # Ensure standard image extension
        ext = Path(clean_name).suffix.lower()
        if ext not in (".png", ".jpg", ".jpeg", ".webp"):
            ext = ".png"
        stem = Path(clean_name).stem
        safe_name = f"{stem}{ext}"

        target_path = case_dir / safe_name
        sha256_hash = hashlib.sha256(content).hexdigest()

        # 2. Image verification and normalization (Pillow -> RGB -> EXIF -> Safe Save)
        try:
            pil_img = Image.open(io.BytesIO(content))
            # Correct orientation from EXIF metadata (e.g. mobile camera captures)
            pil_img = ImageOps.exif_transpose(pil_img) or pil_img

            # Check minimum resolution
            if pil_img.width < 250 or pil_img.height < 180:
                raise ValueError(
                    f"Image resolution is too low ({pil_img.width}x{pil_img.height}). "
                    f"Minimum resolution of 250x180 pixels is required for document screening."
                )

            # Normalize color channels: convert RGBA/Palette/Grayscale to RGB with clean white background
            if pil_img.mode in ("RGBA", "LA") or ("transparency" in pil_img.info):
                bg = Image.new("RGB", pil_img.size, (255, 255, 255))
                rgba_img = pil_img.convert("RGBA")
                bg.paste(rgba_img, mask=rgba_img.split()[3])
                pil_img = bg
            elif pil_img.mode != "RGB":
                pil_img = pil_img.convert("RGB")

            # Downsample if image is excessively massive (e.g., > 3840px in any dimension)
            max_dim = 3840
            if pil_img.width > max_dim or pil_img.height > max_dim:
                pil_img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

            width, height = pil_img.size

            # Save normalized image
            save_format = "PNG" if ext == ".png" else ("WEBP" if ext == ".webp" else "JPEG")
            pil_img.save(target_path, format=save_format, quality=95)
            file_size = target_path.stat().st_size

        except ValueError:
            raise
        except Exception as e:
            err_str = str(e)
            if "cannot identify image file" in err_str:
                raise ValueError("The uploaded image file is invalid, unsupported, or corrupted.")
            raise ValueError(f"The uploaded document could not be decoded or normalized: {err_str}")

        return str(target_path), sha256_hash, file_size, width, height

    def save_heatmap(self, case_id: str, heatmap_image: Image.Image) -> str:
        """
        Saves forensic heatmap image and returns path.
        """
        heatmap_dir = self.base_dir / case_id
        heatmap_dir.mkdir(parents=True, exist_ok=True)
        target_path = heatmap_dir / "forensic_heatmap.png"
        heatmap_image.save(target_path, format="PNG")
        return str(target_path)

storage_service = StorageService()
