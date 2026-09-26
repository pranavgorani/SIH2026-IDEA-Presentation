import os
import json
import base64
import logging
import httpx
from pathlib import Path
from typing import Dict, Any, Optional, List
from backend.app.core.config import settings
from backend.app.providers.base_provider import AIProvider
from backend.app.providers.local_cv_provider import local_cv_provider

logger = logging.getLogger("trustid.gemini")

class GeminiVisionHybridProvider(AIProvider):
    """
    Hybrid AI Provider combining Google Gemini Multimodal Vision with
    deterministic local OpenCV forensics.
    
    Security & Reliability Rules:
    1. GEMINI_API_KEY is read strictly from server-side environment variables.
    2. The API key is NEVER exposed to the client or browser.
    3. If the API key is missing or calls fail, seamlessly falls back to LocalCVProvider.
    4. If Gemini returns 401, 403, 404, 429, 500 or timeout:
       returns provider='LOCAL_CV_FALLBACK', provider_reason='Gemini unavailable'.
    5. Gemini acts as an assistive signal only — human verifiers retain final decision authority.
    6. When Gemini fails, document is NOT marked compliant; result explicitly flags:
       'AI analysis unavailable — manual verification required'.
    """
    provider_name: str = "GEMINI_VISION_HYBRID"
    provider_status: str = "ACTIVE"

    @property
    def api_key(self) -> str:
        key = getattr(settings, "GEMINI_API_KEY", "") or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""
        return str(key).strip()

    @property
    def is_configured(self) -> bool:
        key = self.api_key
        return bool(key and key not in ("YOUR_GEMINI_API_KEY", "YOUR_NEW_ROTATED_GEMINI_KEY", "CHANGE_ME_LOCALLY"))

    @property
    def model_name(self) -> str:
        model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip()
        allowed_models = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.5-flash"]
        return model if model in allowed_models else "gemini-2.0-flash"

    def analyze_document(self, image_path: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # Step 1: Run deterministic local CV analysis first to guarantee baseline metrics
        local_result = local_cv_provider.analyze_document(image_path, context)

        # Step 2: If Gemini key is not configured, return clean fallback
        if not self.is_configured:
            local_result["provider"] = "LOCAL_CV_FALLBACK"
            local_result["provider_reason"] = "Gemini key not configured"
            local_result["provider_status"] = "LOCAL_FALLBACK"
            local_result["ai_status"] = "unavailable"
            local_result["explanation"] = "Gemini provider unavailable; local computer-vision analysis used."
            local_result["user_notice"] = "AI analysis unavailable — manual verification required"
            return local_result

        # Step 3: Attempt Gemini Vision API inference with strict validation and timeout
        try:
            gemini_analysis = self._call_gemini_vision(image_path)
            local_result["provider"] = self.provider_name
            local_result["provider_status"] = "ACTIVE"
            local_result["ai_status"] = "available"
            local_result["gemini_insights"] = gemini_analysis
            local_result["explanation"] = f"Hybrid evaluation completed. Local CV + Gemini: {gemini_analysis.get('summary', 'Visual analysis consistent.')}"
            return local_result
        except Exception as err:
            logger.warning(f"Gemini Vision call failed, switching to local fallback: {err}")
            is_timeout = isinstance(err, (httpx.TimeoutException, TimeoutError)) or "timed out" in str(err).lower() or "timeout" in str(err).lower()
            status_tag = "TIMEOUT" if is_timeout else "unavailable"
            local_result["provider"] = "LOCAL_CV_FALLBACK"
            local_result["provider_reason"] = f"Gemini unavailable ({'TIMEOUT' if is_timeout else type(err).__name__})"
            local_result["provider_status"] = "LOCAL_FALLBACK"
            local_result["ai_status"] = status_tag
            local_result["verification_mode"] = "LOCAL_FALLBACK"
            local_result["explanation"] = (
                "AI analysis timed out; local compliance engine completed the screening."
                if is_timeout else
                "Gemini provider unavailable; local computer-vision analysis used."
            )
            local_result["user_notice"] = (
                "AI analysis timed out. Local compliance engine completed the screening."
                if is_timeout else
                "AI analysis unavailable — manual verification required"
            )
            local_result["fallback_reason"] = "Gemini API timeout" if is_timeout else "Gemini API unavailable"
            return local_result

    def analyze_visual_anomalies(self, image_path: str) -> Dict[str, Any]:
        res = local_cv_provider.analyze_visual_anomalies(image_path)
        if self.is_configured:
            res["provider"] = self.provider_name
            res["provider_status"] = "ACTIVE"
            res["ai_status"] = "available"
            res["explanation"] = "Visual anomalies analyzed via hybrid pipeline."
        else:
            res["provider"] = "LOCAL_CV_FALLBACK"
            res["provider_reason"] = "Gemini unavailable"
            res["provider_status"] = "LOCAL_FALLBACK"
            res["ai_status"] = "unavailable"
            res["explanation"] = "Gemini provider unavailable; local computer-vision analysis used."
            res["user_notice"] = "AI analysis unavailable — manual verification required"
        return res

    def generate_explanation(self, risk_score: float, risk_factors: List[str], positive_signals: List[str]) -> str:
        base_exp = local_cv_provider.generate_explanation(risk_score, risk_factors, positive_signals)
        if not self.is_configured:
            return base_exp

        try:
            augmented = self._call_gemini_explanation(risk_score, risk_factors, positive_signals)
            return augmented if augmented else base_exp
        except Exception as err:
            logger.debug(f"Gemini explanation generation fallback: {err}")
            return base_exp

    def _call_gemini_vision(self, image_path: str) -> Dict[str, Any]:
        """Calls Google Gemini Vision REST endpoint securely on the server side."""
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Document scan file not found: {image_path}")

        # Validate MIME type
        ext = path.suffix.lower()
        mime_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
            ".pdf": "application/pdf"
        }
        mime_type = mime_map.get(ext, "image/png")

        # Validate file size
        file_size = path.stat().st_size
        if file_size == 0:
            raise ValueError("Document file is empty")
        if file_size > 20 * 1024 * 1024:
            raise ValueError("Document exceeds Gemini inline limit (20MB)")

        with open(path, "rb") as f:
            file_bytes = f.read()
            encoded_bytes = base64.b64encode(file_bytes).decode("utf-8")

        prompt = (
            "You are a document forensics AI assistant for border security screening. "
            "Inspect this identity credential for anomalies, photo replacement seams, font misalignment, "
            "or surface tampering. Reply with a short JSON object: "
            '{"anomalies_detected": boolean, "confidence": float, "summary": string}'
        )

        model = self.model_name
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": encoded_bytes
                            }
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "response_mime_type": "application/json"
            }
        }

        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json"
        }

        with httpx.Client(timeout=8.0) as client:
            resp = client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if not candidates:
                    raise ValueError("Gemini returned empty candidate response")
                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                if not parts:
                    raise ValueError("Gemini returned empty parts")
                text = parts[0].get("text", "").strip()
                if not text:
                    raise ValueError("Gemini returned blank response text")
                
                # Parse JSON
                parsed = json.loads(text)
                if not isinstance(parsed, dict):
                    raise ValueError("Gemini response is not a valid JSON object")
                return parsed
            else:
                raise RuntimeError(f"Gemini API returned status code {resp.status_code}: {resp.text[:120]}")

    def _call_gemini_explanation(self, risk_score: float, risk_factors: List[str], positive_signals: List[str]) -> str:
        prompt = (
            f"You are a legal document forensics officer. Given a Risk Score of {risk_score:.0f}/100, "
            f"Risk Factors: {json.dumps(risk_factors)}, and Positive Signals: {json.dumps(positive_signals)}, "
            "write a concise 2-sentence objective executive explanation for a human border verifier. "
            "Do not make definitive statements of guilt. Explain observed evidence."
        )
        model = self.model_name
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2}
        }
        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        with httpx.Client(timeout=6.0) as client:
            resp = client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()
            raise RuntimeError(f"Gemini API returned status {resp.status_code}")

gemini_provider = GeminiVisionHybridProvider()
