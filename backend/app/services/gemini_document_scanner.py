import os
import re
import io
import time
import json
import base64
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
from PIL import Image, ImageOps

from pydantic import BaseModel, Field
from backend.app.core.config import settings

logger = logging.getLogger("trustid.gemini_scanner")

# Official model code and thinking level as mandated
OFFICIAL_GEMINI_MODEL = "gemini-3.8-flash"
OFFICIAL_THINKING_LEVEL = "high"

def mask_credential(val: Optional[str]) -> str:
    """Safe credential masking for diagnostics and logs."""
    if not val:
        return ""
    s = str(val).strip()
    if len(s) <= 4:
        return "****"
    return f"{s[:2]}*****{s[-2:]}"


# =============================================================================
# TYPED STRUCTURED OUTPUT SCHEMAS (Section 3 of Specification)
# =============================================================================

class ImageQualityInfo(BaseModel):
    status: str = "ACCEPTABLE"  # ACCEPTABLE, DEGRADED, UNREADABLE
    issues: List[str] = []

class FieldResult(BaseModel):
    value: Optional[str] = None
    confidence: float = 0.90
    status: str = "PRESENT"  # PRESENT, ABSENT, UNREADABLE, NOT_APPLICABLE
    unreadable_reason: Optional[str] = None

class GeminiMRZInfo(BaseModel):
    lines: List[str] = []
    document_code: Optional[str] = None
    issuing_country: Optional[str] = None
    passport_number: Optional[str] = None
    date_of_birth: Optional[str] = None
    expiry_date: Optional[str] = None
    gender: Optional[str] = None
    raw_mrz: Optional[str] = None

class QRAnalysisInfo(BaseModel):
    status: str = "NOT_APPLICABLE"  # NOT_APPLICABLE, DETECTED_READABLE, DETECTED_UNREADABLE, NOT_PRESENT
    payload_type: Optional[str] = None
    details: Optional[str] = None

class VisualObservation(BaseModel):
    finding_type: str  # TEXT_CONSISTENCY, PHOTO_INTEGRITY, EDITING_BOUNDARY, STAMP_CONSISTENCY, GLARE_OR_BLUR
    description: str
    severity: str = "LOW"  # LOW, MEDIUM, HIGH, INFO
    bbox: Optional[Dict[str, int]] = None  # {x, y, width, height} in original image pixels
    evidence_category: str = "VISUAL_INSPECTION"
    requires_independent_verification: bool = False

class LocalizedRegion(BaseModel):
    region_type: str  # ROI_FACE, ROI_TEXT, ROI_MRZ, ROI_STAMP, ROI_BACKGROUND
    bbox: Dict[str, int]  # {x, y, width, height}
    confidence: float = 0.90

class GeminiDocumentScanResult(BaseModel):
    document_type: str = "UNKNOWN"  # PAN, AADHAAR, PASSPORT, VISA, DRIVING_LICENSE, VOTER_ID, GENERIC_ID, UNSUPPORTED, UNKNOWN
    classification_status: str = "RECOGNIZED"  # RECOGNIZED, UNCERTAIN, UNSUPPORTED, LOCAL_FALLBACK
    classification_cues: List[str] = []
    image_quality: ImageQualityInfo = Field(default_factory=ImageQualityInfo)
    fields: Dict[str, FieldResult] = {}
    mrz: Optional[GeminiMRZInfo] = None
    qr_analysis: QRAnalysisInfo = Field(default_factory=QRAnalysisInfo)
    visual_observations: List[VisualObservation] = []
    localized_regions: List[LocalizedRegion] = []
    all_extracted_text: List[str] = []
    raw_text: str = ""
    uncertainties: List[str] = []
    processing_status: str = "COMPLETED"  # COMPLETED, PARTIAL, LOCAL_FALLBACK, FAILED
    model_used: str = OFFICIAL_GEMINI_MODEL
    thinking_level: str = OFFICIAL_THINKING_LEVEL.upper()
    execution_time_ms: float = 0.0


# =============================================================================
# GEMINI 3.8 FLASH DOCUMENT SCANNER SERVICE
# =============================================================================

class GeminiDocumentScanner:
    """
    High-Precision Document Understanding and OCR Scanner utilizing
    Google Gemini 3.8 Flash with HIGH Thinking Level.
    
    Adheres strictly to the 3-Gate forensic architecture:
    - Multimodal visual reasoning and field extraction
    - Preserves unreadable/absent distinctions without inventing data
    - Never uses missing EXIF or JPEG compression as proof of fraud
    - Provides candidate observations for Gate 2 and extracted fields for Gate 1
    """

    def __init__(self):
        self.model_name = OFFICIAL_GEMINI_MODEL
        self.thinking_level = OFFICIAL_THINKING_LEVEL
        self._genai_client = None

    @property
    def api_key(self) -> str:
        key = getattr(settings, "GEMINI_API_KEY", "") or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""
        return str(key).strip()

    @property
    def is_configured(self) -> bool:
        k = self.api_key
        return bool(k and k not in (
            "YOUR_GEMINI_API_KEY", "YOUR_NEW_ROTATED_GEMINI_KEY", "CHANGE_ME_LOCALLY", "CHANGE_ME"
        ))

    def _get_genai_client(self):
        if self._genai_client is None and self.is_configured:
            try:
                from google import genai
                self._genai_client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Could not initialize google-genai Client: {e}")
                self._genai_client = None
        return self._genai_client

    def validate_and_prepare_input(
        self,
        file_source: Union[str, Path, bytes]
    ) -> Tuple[bytes, str, Tuple[int, int], Image.Image]:
        """
        Validates file signature, handles PDF rendering, corrects EXIF orientation,
        and applies conservative scaling for rapid transmission without text degradation.
        Returns: (image_bytes, mime_type, (orig_w, orig_h), pil_image)
        """
        raw_bytes: bytes = b""
        mime_type = "image/jpeg"

        if isinstance(file_source, (str, Path)):
            p = Path(file_source)
            if not p.is_file():
                raise FileNotFoundError(f"Document file does not exist: {file_source}")
            file_size = p.stat().st_size
            if file_size == 0:
                raise ValueError("Document file is empty (0 bytes)")
            if file_size > 25 * 1024 * 1024:
                raise ValueError("Document file exceeds 25MB maximum limit")
            raw_bytes = p.read_bytes()
            suffix = p.suffix.lower()
            if suffix == ".pdf":
                mime_type = "application/pdf"
            elif suffix == ".png":
                mime_type = "image/png"
            elif suffix == ".webp":
                mime_type = "image/webp"
            else:
                mime_type = "image/jpeg"
        elif isinstance(file_source, bytes):
            raw_bytes = file_source
            if len(raw_bytes) == 0:
                raise ValueError("Document byte stream is empty")
            if len(raw_bytes) > 25 * 1024 * 1024:
                raise ValueError("Document byte stream exceeds 25MB limit")
            # Detect PDF signature %PDF
            if raw_bytes.startswith(b"%PDF"):
                mime_type = "application/pdf"
            elif raw_bytes.startswith(b"\x89PNG"):
                mime_type = "image/png"
            elif raw_bytes.startswith(b"RIFF") and b"WEBP" in raw_bytes[:16]:
                mime_type = "image/webp"
            else:
                mime_type = "image/jpeg"
        else:
            raise TypeError(f"Unsupported file source type: {type(file_source)}")

        # Handle PDF conversion to high-quality image if PDF
        pil_img: Image.Image
        if mime_type == "application/pdf":
            try:
                import pypdfium2
                pdf = pypdfium2.PdfDocument(raw_bytes)
                if len(pdf) == 0:
                    raise ValueError("PDF document contains no pages")
                page = pdf[0]
                # Render at 150 DPI for crystal clear OCR
                pil_img = page.render(scale=2.0).to_pil()
                orig_w, orig_h = pil_img.size
            except Exception as pe:
                logger.warning(f"pypdfium2 PDF conversion degraded: {pe}")
                # Fallback: create placeholder or raise
                raise ValueError(f"Unable to decode PDF document page: {pe}")
        else:
            # Decode image safely with PIL
            try:
                pil_img = Image.open(io.BytesIO(raw_bytes))
                pil_img.load()
            except Exception as ie:
                raise ValueError(f"Corrupt or unsupported image file: {ie}")

            # Apply EXIF rotation correction safely
            try:
                pil_img = ImageOps.exif_transpose(pil_img) or pil_img
            except Exception:
                pass

            orig_w, orig_h = pil_img.size

        # Convert to RGB if necessary (e.g. RGBA or Grayscale)
        if pil_img.mode not in ("RGB", "L"):
            pil_img = pil_img.convert("RGB")

        # Conservative scaling for lightning-fast network transport (max 1600px)
        max_dim = max(orig_w, orig_h)
        working_img = pil_img
        if max_dim > 1600:
            scale = 1600.0 / max_dim
            new_w = max(1, int(round(orig_w * scale)))
            new_h = max(1, int(round(orig_h * scale)))
            working_img = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        # Encode to JPEG buffer
        buf = io.BytesIO()
        working_img.save(buf, format="JPEG", quality=92, optimize=True)
        prepared_bytes = buf.getvalue()

        return prepared_bytes, "image/jpeg", (orig_w, orig_h), pil_img

    def _build_structured_prompt(self, document_type_hint: Optional[str] = "AUTO_DETECT") -> str:
        """Constructs an exhaustive multimodal extraction prompt with structured output constraints."""
        hint_clause = f"Document Type Hint from client: {document_type_hint}." if document_type_hint and document_type_hint != "AUTO_DETECT" else ""
        
        return f"""You are the Principal Document Forensics and High-Precision OCR Engine for TRUST-ID / Nyaya-Tula AI.
{hint_clause}

Perform a rigorous, multimodal forensic inspection of the provided identity document image.

### CLASSIFICATION TARGETS
Classify into one of:
- "PAN" (Indian Permanent Account Number card issued by Income Tax Dept)
- "AADHAAR" (Indian Unique Identification card issued by UIDAI)
- "PASSPORT" (Official international travel document with ICAO Machine Readable Zone)
- "VISA" (Entry clearance or travel visa sticker)
- "DRIVING_LICENSE" (Motor vehicle driving licence or Smart Card DL)
- "VOTER_ID" (Election Commission of India EPIC voter identity card)
- "GENERIC_ID" (Recognizable official credential of other category)
- "UNCLASSIFIED" (Legible document whose specific type is unindexed or generic)
- "UNSUPPORTED" (Not a document, completely unreadable, or corrupt)
- "UNKNOWN" (Uncertain or unknown document type)

### CRITICAL: EXTRACT ALL VISIBLE TEXT
Even if the document type is UNKNOWN, UNCLASSIFIED, or GENERIC_ID, extract ALL readable visible text lines into "all_extracted_text" and "raw_text". Never halt or skip text extraction due to an unrecognized document type!

### STRICT OCR RULES (MANDATORY)
1. NEVER FABRICATE OR GUESS MISSING CHARACTERS.
2. NEVER infer a complete identity number from a partially obscured or masked number.
3. For Aadhaar: if masked digits are visible (e.g. "XXXX XXXX 1234"), return the exact masked string with Xs.
4. If a field is not physically present on the document, mark its status as "NOT_APPLICABLE" or "ABSENT".
5. If text is present but completely unreadable due to blur or glare, mark status as "UNREADABLE" with unreadable_reason. Do NOT invent a name or date.
6. Normalize dates to YYYY-MM-DD or DD/MM/YYYY only when digits are unambiguous. If expiry is permanent/lifetime, state "Permanent".
7. For Passports: extract the 2-line TD3 (44 chars) or 3-line TD1 (30 chars) Machine Readable Zone (MRZ) accurately. Do NOT invent check digits.

### VISUAL FORENSICS & OBSERVATIONS
Observe:
- Text font consistency, geometry, and baseline alignment.
- Photo portrait boundary seams (check for digital cut-and-paste or replacement).
- Official stamps, seals, and holographic elements.
- Local glare, laminate reflection, or compression blur.
Note: Ordinary camera noise, JPEG artifacts, and laminate glare are normal physical properties and are NOT standalone proof of fraud.

### BOUNDING BOXES (0 to 1000 Normalized Scale)
For any localized finding or key document region (ROI_FACE, ROI_TEXT, ROI_MRZ, ROI_STAMP, ROI_BACKGROUND):
Return coordinates as: {{"x": int, "y": int, "width": int, "height": int}} on a 0-1000 scale where top-left is (0,0) and bottom-right is (1000, 1000).

Return ONLY valid JSON matching this schema:
{{
  "document_type": "PAN | AADHAAR | PASSPORT | VISA | DRIVING_LICENSE | VOTER_ID | GENERIC_ID | UNSUPPORTED",
  "classification_status": "RECOGNIZED | UNCERTAIN | UNSUPPORTED",
  "classification_cues": ["list of visual or textual indicators"],
  "image_quality": {{
    "status": "ACCEPTABLE | DEGRADED | UNREADABLE",
    "issues": ["list of issues, e.g. laminate_glare, minor_blur"]
  }},
  "fields": {{
    "document_number": {{"value": "string or null", "confidence": 0.95, "status": "PRESENT | ABSENT | UNREADABLE | NOT_APPLICABLE", "unreadable_reason": null}},
    "holder_full_name": {{"value": "string or null", "confidence": 0.95, "status": "PRESENT | ABSENT | UNREADABLE | NOT_APPLICABLE", "unreadable_reason": null}},
    "father_name": {{"value": "string or null", "confidence": 0.95, "status": "PRESENT | ABSENT | UNREADABLE | NOT_APPLICABLE", "unreadable_reason": null}},
    "date_of_birth": {{"value": "string or null", "confidence": 0.95, "status": "PRESENT | ABSENT | UNREADABLE | NOT_APPLICABLE", "unreadable_reason": null}},
    "gender": {{"value": "Male | Female | Other | null", "confidence": 0.95, "status": "PRESENT | ABSENT | UNREADABLE | NOT_APPLICABLE", "unreadable_reason": null}},
    "nationality": {{"value": "string or null", "confidence": 0.95, "status": "PRESENT | ABSENT | UNREADABLE | NOT_APPLICABLE", "unreadable_reason": null}},
    "issuing_country": {{"value": "string or null", "confidence": 0.95, "status": "PRESENT | ABSENT | UNREADABLE | NOT_APPLICABLE", "unreadable_reason": null}},
    "issuing_authority": {{"value": "string or null", "confidence": 0.95, "status": "PRESENT | ABSENT | UNREADABLE | NOT_APPLICABLE", "unreadable_reason": null}},
    "date_of_issue": {{"value": "string or null", "confidence": 0.95, "status": "PRESENT | ABSENT | UNREADABLE | NOT_APPLICABLE", "unreadable_reason": null}},
    "expiry_date": {{"value": "string or null", "confidence": 0.95, "status": "PRESENT | ABSENT | UNREADABLE | NOT_APPLICABLE", "unreadable_reason": null}},
    "address": {{"value": "string or null", "confidence": 0.95, "status": "PRESENT | ABSENT | UNREADABLE | NOT_APPLICABLE", "unreadable_reason": null}},
    "vehicle_class": {{"value": "string or null", "confidence": 0.95, "status": "PRESENT | ABSENT | UNREADABLE | NOT_APPLICABLE", "unreadable_reason": null}}
  }},
  "mrz": {{
    "lines": ["string"],
    "document_code": "P",
    "issuing_country": "string",
    "passport_number": "string",
    "date_of_birth": "string",
    "expiry_date": "string",
    "gender": "string",
    "raw_mrz": "string"
  }},
  "qr_analysis": {{
    "status": "NOT_APPLICABLE | NOT_PRESENT | DETECTED_READABLE | DETECTED_UNREADABLE",
    "payload_type": "string or null",
    "details": "string or null"
  }},
  "visual_observations": [
    {{
      "finding_type": "TEXT_CONSISTENCY | PHOTO_INTEGRITY | EDITING_BOUNDARY | STAMP_CONSISTENCY | GLARE_OR_BLUR",
      "description": "string",
      "severity": "LOW | MEDIUM | HIGH | INFO",
      "bbox": {{"x": 0, "y": 0, "width": 0, "height": 0}},
      "evidence_category": "TYPOGRAPHY | PORTRAIT | STAMP | SUBSTRATE",
      "requires_independent_verification": false
    }}
  ],
  "localized_regions": [
    {{
      "region_type": "ROI_FACE | ROI_TEXT | ROI_MRZ | ROI_STAMP | ROI_BACKGROUND",
      "bbox": {{"x": 0, "y": 0, "width": 0, "height": 0}},
      "confidence": 0.95
    }}
  ],
  "all_extracted_text": ["exact line of readable text 1", "exact line 2"],
  "raw_text": "complete extracted text from document",
  "uncertainties": ["list any specific ambiguities or limitations"],
  "processing_status": "COMPLETED"
}}"""

    def _call_gemini_with_sdk(
        self,
        image_bytes: bytes,
        mime_type: str,
        prompt: str,
        timeout: float = 20.0
    ) -> Optional[str]:
        """Calls official Google GenAI SDK with thinking_level='high'."""
        client = self._get_genai_client()
        if not client:
            return None

        from google.genai import types

        thinking_config = types.ThinkingConfig(thinking_level="high")
        gen_config = types.GenerateContentConfig(
            thinking_config=thinking_config,
            response_mime_type="application/json",
            temperature=0.1
        )

        image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        contents = [prompt, image_part]

        # Execute generation
        response = client.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=gen_config
        )

        if response and response.text:
            return response.text.strip()
        return None

    def _call_gemini_with_rest(
        self,
        image_bytes: bytes,
        mime_type: str,
        prompt: str,
        timeout: float = 20.0
    ) -> Optional[str]:
        """High-performance REST API fallback with thinkingLevel='high'."""
        import httpx
        encoded = base64.b64encode(image_bytes).decode("utf-8")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent"

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": encoded
                            }
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "response_mime_type": "application/json",
                "thinkingConfig": {
                    "thinkingLevel": "high"
                }
            }
        }

        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json"
        }

        with httpx.Client(timeout=timeout) as client:
            resp = client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()
            else:
                logger.warning(f"Gemini REST response status {resp.status_code}: {resp.text[:200]}")
        return None

    def scan_document(
        self,
        file_source: Union[str, Path, bytes],
        document_type_hint: Optional[str] = "AUTO_DETECT",
        timeout: float = 20.0
    ) -> GeminiDocumentScanResult:
        """
        Executes primary multimodal document scanning using Gemini 3.8 Flash (HIGH thinking level).
        Gracefully falls back to local CV/OCR if unconfigured or unavailable without raising false alarms.
        """
        t0 = time.perf_counter()

        # Step 1: Input preparation & validation
        try:
            image_bytes, mime_type, (orig_w, orig_h), pil_img = self.validate_and_prepare_input(file_source)
        except Exception as ve:
            logger.error(f"Input validation failure in GeminiDocumentScanner: {ve}")
            return GeminiDocumentScanResult(
                document_type="UNSUPPORTED",
                classification_status="UNSUPPORTED",
                image_quality=ImageQualityInfo(status="UNREADABLE", issues=[str(ve)]),
                processing_status="FAILED",
                uncertainties=[f"Input preparation error: {ve}"],
                execution_time_ms=round((time.perf_counter() - t0) * 1000, 1)
            )

        # Step 2: Check server configuration
        if not self.is_configured:
            logger.info("Gemini API key not configured; routing to local OCR/CV fallback.")
            return GeminiDocumentScanResult(
                document_type="UNKNOWN",
                classification_status="LOCAL_FALLBACK",
                processing_status="LOCAL_FALLBACK",
                uncertainties=["Gemini API credentials not configured on server; using local OCR/CV"],
                execution_time_ms=round((time.perf_counter() - t0) * 1000, 1)
            )

        # Step 3: Execute model inference
        prompt = self._build_structured_prompt(document_type_hint)
        raw_json_str: Optional[str] = None
        error_encountered: Optional[str] = None

        # Try Google GenAI SDK first
        try:
            raw_json_str = self._call_gemini_with_sdk(image_bytes, mime_type, prompt, timeout=timeout)
        except Exception as sdk_err:
            logger.warning(f"Gemini SDK call encountered error ({sdk_err}), trying REST fallback...")
            error_encountered = str(sdk_err)

        # Fallback to REST if SDK was unavailable or raised
        if not raw_json_str:
            try:
                raw_json_str = self._call_gemini_with_rest(image_bytes, mime_type, prompt, timeout=timeout)
            except Exception as rest_err:
                logger.warning(f"Gemini REST call failed: {rest_err}")
                error_encountered = str(rest_err)

        # Step 4: Handle failure / timeout gracefully
        if not raw_json_str:
            logger.warning(f"Gemini Vision inference unavailable ({error_encountered}); gracefully degrading to local fallback.")
            return GeminiDocumentScanResult(
                document_type="UNKNOWN",
                classification_status="LOCAL_FALLBACK",
                processing_status="LOCAL_FALLBACK",
                uncertainties=[f"Gemini Vision call timed out or failed ({error_encountered or 'Unknown error'})"],
                execution_time_ms=round((time.perf_counter() - t0) * 1000, 1)
            )

        # Step 5: Clean and parse JSON response
        try:
            clean_str = raw_json_str.strip()
            # Strip markdown formatting if present
            if clean_str.startswith("```"):
                clean_str = re.sub(r"^```(?:json)?\s*", "", clean_str, flags=re.IGNORECASE)
                clean_str = re.sub(r"\s*```$", "", clean_str)

            parsed = json.loads(clean_str)
            if not isinstance(parsed, dict):
                raise ValueError("Model output did not decode to a JSON object")

            # Scale bounding boxes from 0-1000 scale to original image dimensions (orig_w, orig_h)
            def scale_box(b: Any) -> Dict[str, int]:
                if not isinstance(b, dict):
                    return {"x": 0, "y": 0, "width": 0, "height": 0}
                bx = float(b.get("x", 0))
                by = float(b.get("y", 0))
                bw = float(b.get("width", 0))
                bh = float(b.get("height", 0))

                # If values are normalized 0..1000
                if max(bx, by, bw, bh) <= 1000.0 and (orig_w > 1000 or orig_h > 1000):
                    return {
                        "x": int(round((bx / 1000.0) * orig_w)),
                        "y": int(round((by / 1000.0) * orig_h)),
                        "width": int(round((bw / 1000.0) * orig_w)),
                        "height": int(round((bh / 1000.0) * orig_h))
                    }
                return {
                    "x": int(round(bx)),
                    "y": int(round(by)),
                    "width": int(round(bw)),
                    "height": int(round(bh))
                }

            # Map observations
            obs_list: List[VisualObservation] = []
            for item in parsed.get("visual_observations", []):
                if isinstance(item, dict):
                    bbox = item.get("bbox")
                    scaled_bbox = scale_box(bbox) if bbox else None
                    obs_list.append(VisualObservation(
                        finding_type=str(item.get("finding_type", "TEXT_CONSISTENCY")),
                        description=str(item.get("description", "")),
                        severity=str(item.get("severity", "LOW")),
                        bbox=scaled_bbox,
                        evidence_category=str(item.get("evidence_category", "VISUAL_INSPECTION")),
                        requires_independent_verification=bool(item.get("requires_independent_verification", False))
                    ))

            # Map localized regions
            regions_list: List[LocalizedRegion] = []
            for reg in parsed.get("localized_regions", []):
                if isinstance(reg, dict):
                    regions_list.append(LocalizedRegion(
                        region_type=str(reg.get("region_type", "ROI_TEXT")),
                        bbox=scale_box(reg.get("bbox", {})),
                        confidence=float(reg.get("confidence", 0.90))
                    ))

            # Map fields safely
            raw_fields = parsed.get("fields", {})
            mapped_fields: Dict[str, FieldResult] = {}
            if isinstance(raw_fields, dict):
                for f_name, f_val in raw_fields.items():
                    if isinstance(f_val, dict):
                        mapped_fields[f_name] = FieldResult(
                            value=str(f_val["value"]).strip() if f_val.get("value") is not None else None,
                            confidence=float(f_val.get("confidence", 0.90)),
                            status=str(f_val.get("status", "PRESENT" if f_val.get("value") else "ABSENT")),
                            unreadable_reason=f_val.get("unreadable_reason")
                        )
                    elif isinstance(f_val, str):
                        mapped_fields[f_name] = FieldResult(value=f_val.strip(), confidence=0.90, status="PRESENT")

            # Map MRZ
            raw_mrz = parsed.get("mrz")
            mrz_info = None
            if isinstance(raw_mrz, dict) and (raw_mrz.get("lines") or raw_mrz.get("passport_number")):
                mrz_info = GeminiMRZInfo(
                    lines=raw_mrz.get("lines", []),
                    document_code=raw_mrz.get("document_code"),
                    issuing_country=raw_mrz.get("issuing_country"),
                    passport_number=raw_mrz.get("passport_number"),
                    date_of_birth=raw_mrz.get("date_of_birth"),
                    expiry_date=raw_mrz.get("expiry_date"),
                    gender=raw_mrz.get("gender"),
                    raw_mrz=raw_mrz.get("raw_mrz")
                )

            # Map Image Quality
            iq_raw = parsed.get("image_quality", {})
            img_quality = ImageQualityInfo(
                status=iq_raw.get("status", "ACCEPTABLE") if isinstance(iq_raw, dict) else "ACCEPTABLE",
                issues=iq_raw.get("issues", []) if isinstance(iq_raw, dict) else []
            )

            # Map QR Analysis
            qr_raw = parsed.get("qr_analysis", {})
            qr_info = QRAnalysisInfo(
                status=qr_raw.get("status", "NOT_APPLICABLE") if isinstance(qr_raw, dict) else "NOT_APPLICABLE",
                payload_type=qr_raw.get("payload_type") if isinstance(qr_raw, dict) else None,
                details=qr_raw.get("details") if isinstance(qr_raw, dict) else None
            )

            doc_type = str(parsed.get("document_type", "UNKNOWN")).upper()
            class_status = str(parsed.get("classification_status", "RECOGNIZED")).upper()

            # Map all extracted text lines
            extracted_lines: List[str] = []
            if isinstance(parsed.get("all_extracted_text"), list):
                extracted_lines = [str(x).strip() for x in parsed["all_extracted_text"] if str(x).strip()]
            raw_text_val = str(parsed.get("raw_text") or "").strip()
            if not raw_text_val and extracted_lines:
                raw_text_val = "\n".join(extracted_lines)
            elif raw_text_val and not extracted_lines:
                extracted_lines = [line.strip() for line in raw_text_val.split("\n") if line.strip()]

            res = GeminiDocumentScanResult(
                document_type=doc_type,
                classification_status=class_status,
                classification_cues=parsed.get("classification_cues", []),
                image_quality=img_quality,
                fields=mapped_fields,
                mrz=mrz_info,
                qr_analysis=qr_info,
                visual_observations=obs_list,
                localized_regions=regions_list,
                all_extracted_text=extracted_lines,
                raw_text=raw_text_val,
                uncertainties=parsed.get("uncertainties", []),
                processing_status="COMPLETED",
                model_used=self.model_name,
                thinking_level=self.thinking_level.upper(),
                execution_time_ms=round((time.perf_counter() - t0) * 1000, 1)
            )

            logger.info(
                f"GEMINI_SCAN_COMPLETE: doc_type={res.document_type} "
                f"status={res.classification_status} fields={len(res.fields)} "
                f"time={res.execution_time_ms}ms"
            )
            return res

        except Exception as pe:
            logger.error(f"Error parsing Gemini JSON response: {pe}")
            return GeminiDocumentScanResult(
                document_type="UNKNOWN",
                classification_status="LOCAL_FALLBACK",
                processing_status="PARTIAL",
                uncertainties=[f"Failed to decode model JSON: {pe}"],
                execution_time_ms=round((time.perf_counter() - t0) * 1000, 1)
            )


# Singleton instance
gemini_document_scanner = GeminiDocumentScanner()

def get_gemini_scanner() -> GeminiDocumentScanner:
    """Return singleton Gemini document scanner instance."""
    return gemini_document_scanner
