import os
import shutil
import hashlib
from pathlib import Path
from typing import Tuple
from PIL import Image
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
        Returns (relative_file_path, sha256_hash, file_size_bytes, width, height)
        """
        case_dir = self.base_dir / case_id
        case_dir.mkdir(parents=True, exist_ok=True)

        # Sanitize filename
        safe_name = "".join(c for c in filename if c.isalnum() or c in "._-")
        if not safe_name:
            safe_name = "document.png"

        target_path = case_dir / safe_name
        with open(target_path, "wb") as f:
            f.write(content)

        file_size = len(content)
        sha256_hash = hashlib.sha256(content).hexdigest()

        # Extract dimensions if image
        width, height = 0, 0
        try:
            with Image.open(target_path) as img:
                width, height = img.size
        except Exception:
            pass

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
