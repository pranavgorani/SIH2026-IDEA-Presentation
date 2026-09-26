import os
import io
import re
import shutil
import hashlib
import logging
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional
from PIL import Image, ImageOps

from backend.app.core.config import settings
from backend.app.core.exceptions import InvalidDocumentException, FileTooLargeException

logger = logging.getLogger("trustid.storage")

class StorageService:
    def __init__(self, base_dir: Path = settings.STORAGE_DIR):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        (self.base_dir / "heatmaps").mkdir(parents=True, exist_ok=True)
        (self.base_dir / "synthetic").mkdir(parents=True, exist_ok=True)

    def save_upload(
        self,
        case_id: str,
        filename: str,
        content: bytes,
        mime_type: Optional[str] = None,
        return_meta: bool = False
    ) -> Any:
        """
        Saves uploaded file securely under case-specific directory.
        Supports: PDF, PNG, JPG, JPEG, WEBP.
        
        Performs:
        1. File existence & empty file check.
        2. Size limit check (25MB).
        3. Extension and MIME type verification.
        4. PDF page extraction & rasterization (multi-page support via pypdfium2).
        5. Image normalization (RGB conversion, EXIF orientation fix, min resolution check).
        
        Returns:
            (primary_image_path, sha256_hash, file_size_bytes, width, height)
        """
        if not content or len(content) == 0:
            raise InvalidDocumentException("Uploaded document file is empty.", code="EMPTY_FILE")

        # 25MB maximum limit
        max_bytes = settings.UPLOAD_MAX_SIZE_MB * 1024 * 1024
        if len(content) > max_bytes:
            raise FileTooLargeException(f"Uploaded file exceeds the maximum allowed size of {settings.UPLOAD_MAX_SIZE_MB}MB.")

        case_dir = self.base_dir / case_id
        case_dir.mkdir(parents=True, exist_ok=True)

        sha256_hash = hashlib.sha256(content).hexdigest()

        # Sanitize filename safely without evaluating path traversal
        raw_name = Path(filename or "document.png").name
        clean_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', raw_name)
        if not clean_name:
            clean_name = "document.png"

        ext = Path(clean_name).suffix.lower()
        if ext not in settings.ALLOWED_EXTENSIONS:
            raise InvalidDocumentException(
                f"Unsupported file extension '{ext}'. Supported formats: PDF, PNG, JPG, JPEG, WEBP.",
                code="INVALID_DOCUMENT"
            )

        is_pdf = ext == ".pdf" or content.startswith(b"%PDF")

        # =====================================================================
        # PDF DOCUMENT PROCESSING (Multi-page extraction and rendering)
        # =====================================================================
        if is_pdf:
            if not settings.ENABLE_PDF_PROCESSING:
                raise InvalidDocumentException(
                    "PDF processing is not enabled in this deployment.",
                    code="PDF_UNSUPPORTED"
                )

            pdf_path = case_dir / "original_document.pdf"
            with open(pdf_path, "wb") as f:
                f.write(content)

            page_image_paths: List[str] = []
            page_records: List[Dict[str, Any]] = []
            primary_width = 800
            primary_height = 1100

            try:
                import pypdfium2
                pdf_doc = pypdfium2.PdfDocument(pdf_path)
                total_pages = len(pdf_doc)
                if total_pages == 0:
                    raise InvalidDocumentException("PDF document contains no renderable pages.", code="INVALID_DOCUMENT")

                max_pages = min(total_pages, settings.OCR_MAX_PAGES)
                for page_idx in range(max_pages):
                    page = pdf_doc.get_page(page_idx)
                    # Render at 2x scale (~150-200 DPI) for crisp OCR
                    pil_page = page.render(scale=2.0).to_pil()
                    page_file_path = case_dir / f"page_{page_idx + 1}.png"
                    pil_page.save(page_file_path, format="PNG")
                    page_image_paths.append(str(page_file_path))
                    page_records.append({
                        "page_number": page_idx + 1,
                        "file_path": str(page_file_path),
                        "width": pil_page.width,
                        "height": pil_page.height
                    })

                    if page_idx == 0:
                        primary_width = pil_page.width
                        primary_height = pil_page.height

                primary_path = page_image_paths[0]

            except Exception as pdf_err:
                logger.warning(f"pypdfium2 error, attempting pypdf text inspection: {pdf_err}")
                try:
                    import pypdf
                    reader = pypdf.PdfReader(io.BytesIO(content))
                    total_pages = len(reader.pages)
                    if total_pages == 0:
                        raise InvalidDocumentException("Corrupted or empty PDF file.", code="INVALID_DOCUMENT")
                    
                    # Create blank page representation if visual renderer unavailable
                    blank = Image.new("RGB", (800, 1100), (255, 255, 255))
                    fallback_path = case_dir / "page_1.png"
                    blank.save(fallback_path, format="PNG")
                    primary_path = str(fallback_path)
                    page_image_paths = [primary_path]
                    page_records = [{"page_number": 1, "file_path": primary_path, "width": 800, "height": 1100}]
                except Exception as pypdf_err:
                    raise InvalidDocumentException(
                        f"Failed to decode or parse PDF document: {str(pypdf_err)}",
                        code="INVALID_DOCUMENT"
                    )

            extra_meta = {
                "is_pdf": True,
                "total_pages": total_pages,
                "processed_pages": len(page_image_paths),
                "original_file_path": str(pdf_path),
                "pages": page_records
            }
            self.last_upload_meta = extra_meta
            if return_meta:
                return primary_path, sha256_hash, len(content), primary_width, primary_height, extra_meta
            return primary_path, sha256_hash, len(content), primary_width, primary_height

        # =====================================================================
        # STANDARD IMAGE PROCESSING (PNG, JPG, WEBP)
        # =====================================================================
        try:
            pil_img = Image.open(io.BytesIO(content))
            # Correct orientation from EXIF metadata (mobile phone captures)
            pil_img = ImageOps.exif_transpose(pil_img) or pil_img

            # Check minimum resolution
            if pil_img.width < 250 or pil_img.height < 180:
                raise InvalidDocumentException(
                    f"Image resolution is too low ({pil_img.width}x{pil_img.height}). Minimum resolution of 250x180 pixels is required for document screening.",
                    code="INVALID_DOCUMENT"
                )

            # Convert RGBA/Palette/Grayscale to RGB with clean white background
            if pil_img.mode in ("RGBA", "LA") or ("transparency" in pil_img.info):
                bg = Image.new("RGB", pil_img.size, (255, 255, 255))
                rgba_img = pil_img.convert("RGBA")
                bg.paste(rgba_img, mask=rgba_img.split()[3])
                pil_img = bg
            elif pil_img.mode != "RGB":
                pil_img = pil_img.convert("RGB")

            # Downsample if image is excessively massive (> 3840px)
            max_dim = 3840
            if pil_img.width > max_dim or pil_img.height > max_dim:
                pil_img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

            width, height = pil_img.size
            stem = Path(clean_name).stem
            safe_name = f"{stem}.png"
            target_path = case_dir / safe_name
            pil_img.save(target_path, format="PNG", quality=95)
            file_size = target_path.stat().st_size

        except InvalidDocumentException:
            raise
        except Exception as e:
            err_str = str(e)
            logger.warning(f"Image decode error: {err_str}")
            raise InvalidDocumentException(
                "The uploaded image file is invalid, unsupported, or corrupted.",
                code="CORRUPTED_DOCUMENT"
            )

        extra_meta = {
            "is_pdf": False,
            "total_pages": 1,
            "processed_pages": 1,
            "original_file_path": str(target_path),
            "pages": [{"page_number": 1, "file_path": str(target_path), "width": width, "height": height}]
        }
        self.last_upload_meta = extra_meta
        if return_meta:
            return str(target_path), sha256_hash, file_size, width, height, extra_meta
        return str(target_path), sha256_hash, file_size, width, height

storage_service = StorageService()
