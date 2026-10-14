"""
TRUST-ID Gate 2: Differential Region-of-Interest (ROI) Forensics & Biometrics
Implements:
1. Multi-Region Cropping (ROI_Face, ROI_Text, ROI_Background)
2. Specular Glare & Text Edge Masking (Canny dilation)
3. Differential Error Level Analysis (ELA 90%) & Laplacian Noise Ratio
4. Differential Z-Scores:
   ΔZ_face = |μ_face - μ_bg| / max(σ_bg, 1.5)
   ΔZ_text = |μ_text - μ_bg| / max(σ_bg, 1.5)
   Thresholds:
     ΔZ <= 1.8 -> CLEAN / UNIFORM (0 to 12 risk pts)
     1.8 < ΔZ <= 2.6 -> MINOR ANOMALY (15 to 28 risk pts)
     ΔZ > 2.6 -> LOCALIZED SPLICING (45 to 75 risk pts + Red Bounding Box)
5. Biometric Verification:
   - 1:1 Live Match (Selfie vs Document Portrait)
   - 1:N Multi-Identity Recycled Face Check (Flags same face with different ID/Name)
"""

import io
import cv2
import hashlib
import numpy as np
from PIL import Image
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union


class DifferentialROIForensics:
    """
    Gate 2: Region-Specific Differential Forensics & Biometric Identity Engine.
    Eliminates false positives by comparing Face and Text blocks directly
    against the document's own background substrate rather than arbitrary global metrics.
    """

    def __init__(self):
        # Face cascade for ROI_Face detection
        self.face_cascade = None
        if hasattr(cv2, "CascadeClassifier") and hasattr(cv2, "data") and hasattr(cv2.data, "haarcascades"):
            try:
                cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
                self.face_cascade = cv2.CascadeClassifier(cascade_path)
            except Exception:
                self.face_cascade = None

        # 1:N Multi-Identity Face Registry (in-memory persistent store)
        # Structure: [ {"embedding": emb, "doc_number": ..., "name": ..., "case_id": ...} ]
        self._identity_registry: List[Dict[str, Any]] = []

    def segment_rois(
        self,
        bgr_img: np.ndarray,
        ocr_boxes: Optional[List[Dict[str, int]]] = None
    ) -> Dict[str, Any]:
        """
        Partitions normalized image into:
        - ROI_Face: Portrait photo bounding box [x, y, w, h]
        - ROI_Text: Text/DOB zone bounding box [x, y, w, h]
        - ROI_Background: Mask of uniform substrate excluding face & text
        """
        h, w = bgr_img.shape[:2]
        gray = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2GRAY)

        # 1. Face Detection
        face_box = None
        if self.face_cascade:
            try:
                faces = self.face_cascade.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=4,
                    minSize=(int(min(w, h) * 0.12), int(min(w, h) * 0.12))
                )
                if len(faces) > 0:
                    # Choose largest face
                    faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
                    fx, fy, fw, fh = faces[0]
                    face_box = (int(fx), int(fy), int(fw), int(fh))
            except Exception:
                face_box = None

        # Fallback face zone for typical ID card (left or right side portrait)
        if face_box is None:
            # Conservative portrait guess: left side 15-45% width, 20-75% height
            face_box = (int(w * 0.08), int(h * 0.20), int(w * 0.28), int(h * 0.55))

        # 2. Text Zone (from OCR boxes or standard layout)
        if ocr_boxes and len(ocr_boxes) > 0:
            min_x = min(b.get("x", 0) for b in ocr_boxes)
            min_y = min(b.get("y", 0) for b in ocr_boxes)
            max_x = max(b.get("x", 0) + b.get("width", 0) for b in ocr_boxes)
            max_y = max(b.get("y", 0) + b.get("height", 0) for b in ocr_boxes)
            text_box = (
                max(0, min_x),
                max(0, min_y),
                min(w - max(0, min_x), max_x - min_x),
                min(h - max(0, min_y), max_y - min_y)
            )
        else:
            # Standard ID text zone: right of portrait or center-right
            fx, fy, fw, fh = face_box
            text_x = min(w - 50, fx + fw + int(w * 0.04))
            text_w = max(50, w - text_x - int(w * 0.05))
            text_box = (text_x, int(h * 0.18), text_w, int(h * 0.65))

        # 3. Background Mask: entire canvas minus face box, text box, and borders
        bg_mask = np.ones((h, w), dtype=np.uint8) * 255
        # Exclude borders (5%)
        margin_x = int(w * 0.05)
        margin_y = int(h * 0.05)
        bg_mask[:margin_y, :] = 0
        bg_mask[h - margin_y:, :] = 0
        bg_mask[:, :margin_x] = 0
        bg_mask[:, w - margin_x:] = 0

        # Exclude face box with 10px dilation
        fx, fy, fw, fh = face_box
        cv2.rectangle(
            bg_mask,
            (max(0, fx - 10), max(0, fy - 10)),
            (min(w, fx + fw + 10), min(h, fy + fh + 10)),
            0,
            -1
        )

        # Exclude text box with 10px dilation
        tx, ty, tw, th = text_box
        cv2.rectangle(
            bg_mask,
            (max(0, tx - 10), max(0, ty - 10)),
            (min(w, tx + tw + 10), min(h, ty + th + 10)),
            0,
            -1
        )

        return {
            "face_box": face_box,
            "text_box": text_box,
            "bg_mask": bg_mask
        }

    def compute_differential_ela(
        self,
        bgr_img: np.ndarray,
        rois: Dict[str, Any],
        glare_mask: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """
        Differential Error Level Analysis (ELA 90%):
        1. Re-saves image at 90% JPEG quality to compute absolute difference map.
        2. Masks out high-contrast text edges (Canny dilation) and specular glare.
        3. Computes Mean and Std inside ROI_Background.
        4. Calculates Differential Z-Scores (ΔZ_face, ΔZ_text).
        5. Calibrates risk contribution and flags anomalous bounding boxes.
        """
        h, w = bgr_img.shape[:2]
        gray = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2GRAY)

        # 1. In-memory JPEG recompression at 90%
        pil_orig = Image.fromarray(cv2.cvtColor(bgr_img, cv2.COLOR_BGR2RGB))
        buf = io.BytesIO()
        pil_orig.save(buf, format="JPEG", quality=90)
        buf.seek(0)
        pil_resaved = Image.open(buf)
        bgr_resaved = cv2.cvtColor(np.array(pil_resaved), cv2.COLOR_RGB2BGR)

        # Pixel difference map
        diff = cv2.absdiff(bgr_img, bgr_resaved)
        ela_energy = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY).astype(np.float32)

        # Laplacian high-frequency noise variance map
        lap = np.abs(cv2.Laplacian(gray, cv2.CV_32F))

        # Combine ELA energy and Laplacian high-pass noise (70% ELA, 30% Laplacian)
        combined_energy = 0.7 * ela_energy + 0.3 * (lap / (np.max(lap) + 1e-5) * 255.0)

        # 2. Mask sharp high-contrast text edges to avoid false text splicing
        canny = cv2.Canny(gray, 80, 200)
        edge_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        dilated_edges = cv2.dilate(canny, edge_kernel, iterations=1)
        non_edge_mask = (dilated_edges == 0)

        # Specular glare exclusion
        valid_pixel_mask = np.ones((h, w), dtype=bool)
        if glare_mask is not None and glare_mask.size > 0:
            valid_pixel_mask &= (glare_mask == 0)

        # Background substrate sampling (excluding edges and glare)
        bg_mask = (rois["bg_mask"] == 255) & non_edge_mask & valid_pixel_mask
        bg_pixels = combined_energy[bg_mask]

        if bg_pixels.size < 50:
            # Fallback to entire canvas if bg mask too small
            bg_pixels = combined_energy.flatten()

        mu_bg = float(np.mean(bg_pixels))
        sigma_bg = float(np.std(bg_pixels))
        effective_sigma = max(sigma_bg, 1.5)

        # 3. Differential Z-Scores
        # A. Face ROI
        fx, fy, fw, fh = rois["face_box"]
        face_sub = combined_energy[max(0, fy):min(h, fy + fh), max(0, fx):min(w, fx + fw)]
        mu_face = float(np.mean(face_sub)) if face_sub.size > 0 else mu_bg
        delta_z_face = float(abs(mu_face - mu_bg) / effective_sigma)

        # B. Text ROI
        tx, ty, tw, th = rois["text_box"]
        # Apply non-edge mask so text glyph boundaries themselves don't inflate text ROI
        text_zone_energy = combined_energy[max(0, ty):min(h, ty + th), max(0, tx):min(w, tx + tw)]
        text_zone_non_edge = non_edge_mask[max(0, ty):min(h, ty + th), max(0, tx):min(w, tx + tw)]
        if np.count_nonzero(text_zone_non_edge) > 20:
            mu_text = float(np.mean(text_zone_energy[text_zone_non_edge]))
        else:
            mu_text = float(np.mean(text_zone_energy)) if text_zone_energy.size > 0 else mu_bg

        delta_z_text = float(abs(mu_text - mu_bg) / effective_sigma)

        # 4. Calibration & Splicing Localization
        flagged_rois: List[Dict[str, Any]] = []
        risk_contribution = 0
        splicing_detected = False
        findings: List[str] = []

        max_delta_z = max(delta_z_face, delta_z_text)

        # Face calibration
        if delta_z_face > 2.6:
            splicing_detected = True
            face_risk = int(min(75, 45 + (delta_z_face - 2.6) * 15))
            risk_contribution = max(risk_contribution, face_risk)
            flagged_rois.append({
                "region": "FACE_PORTRAIT",
                "x": fx, "y": fy, "width": fw, "height": fh,
                "delta_z": round(delta_z_face, 2),
                "severity": "CRITICAL",
                "description": f"Photo splice detected: Face box ELA variance strongly deviates from card substrate (ΔZ = {delta_z_face:.2f} > 2.6)"
            })
            findings.append(f"Localized photo splicing detected in ID portrait region (ΔZ = {delta_z_face:.2f})")
        elif delta_z_face > 1.8:
            risk_contribution = max(risk_contribution, int(15 + (delta_z_face - 1.8) * 16))
            findings.append(f"Minor lighting/compression variance in portrait zone (ΔZ = {delta_z_face:.2f})")
        else:
            face_pts = int(round(delta_z_face * 6.0))
            risk_contribution = max(risk_contribution, face_pts)
            findings.append(f"Portrait region compression matches background substrate (ΔZ = {delta_z_face:.2f} <= 1.8)")

        # Text calibration
        if delta_z_text > 2.6:
            splicing_detected = True
            text_risk = int(min(75, 45 + (delta_z_text - 2.6) * 15))
            risk_contribution = max(risk_contribution, text_risk)
            flagged_rois.append({
                "region": "TEXT_CREDENTIALS",
                "x": tx, "y": ty, "width": tw, "height": th,
                "delta_z": round(delta_z_text, 2),
                "severity": "CRITICAL",
                "description": f"Digital text splice detected: Credential text patch has anomalous compression vs background (ΔZ = {delta_z_text:.2f} > 2.6)"
            })
            findings.append(f"Pasted text box / digital alteration detected in ID fields (ΔZ = {delta_z_text:.2f})")
        elif delta_z_text > 1.8:
            risk_contribution = max(risk_contribution, int(15 + (delta_z_text - 1.8) * 16))
            findings.append(f"Minor compression gradient across text zone (ΔZ = {delta_z_text:.2f})")
        else:
            text_pts = int(round(delta_z_text * 6.0))
            risk_contribution = max(risk_contribution, text_pts)
            findings.append(f"Text credentials substrate is uniform and consistent (ΔZ = {delta_z_text:.2f} <= 1.8)")

        # If clean: cap risk contribution strictly <= 12
        if max_delta_z <= 1.8:
            risk_contribution = min(12, risk_contribution)
            status = "UNIFORM_CLEAN"
        elif max_delta_z <= 2.6:
            risk_contribution = min(28, max(15, risk_contribution))
            status = "MINOR_ANOMALY"
        else:
            risk_contribution = min(75, max(45, risk_contribution))
            status = "LOCALIZED_SPLICING_DETECTED"

        return {
            "splicing_detected": splicing_detected,
            "status": status,
            "delta_z_face": round(delta_z_face, 3),
            "delta_z_text": round(delta_z_text, 3),
            "max_delta_z": round(max_delta_z, 3),
            "mu_bg": round(mu_bg, 2),
            "sigma_bg": round(sigma_bg, 2),
            "risk_contribution": risk_contribution,
            "flagged_rois": flagged_rois,
            "findings": findings
        }

    # =========================================================================
    # BIOMETRICS: 1:1 LIVE MATCH & 1:N RECYCLED MULTI-IDENTITY DETECTOR
    # =========================================================================
    def compute_face_embedding(self, face_bgr: np.ndarray) -> np.ndarray:
        """
        Extracts robust normalized facial biometric feature vector.
        Uses multi-scale histogram of gradients and spatial frequency textures.
        """
        resized = cv2.resize(face_bgr, (64, 64))
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

        # Sobel gradients
        gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        mag, ang = cv2.cartToPolar(gx, gy, angleInDegrees=True)

        # 8-bin orientation histogram over 4x4 spatial cells
        cell_size = 16
        hist_list = []
        for r in range(0, 64, cell_size):
            for c in range(0, 64, cell_size):
                cell_mag = mag[r:r+cell_size, c:c+cell_size]
                cell_ang = ang[r:r+cell_size, c:c+cell_size]
                hist, _ = np.histogram(cell_ang, bins=8, range=(0, 360), weights=cell_mag)
                hist_list.extend(hist)

        vec = np.array(hist_list, dtype=np.float32)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec /= norm
        return vec

    def verify_biometrics_1to1(
        self,
        doc_face_bgr: Optional[np.ndarray],
        live_selfie_bgr: Optional[np.ndarray]
    ) -> Dict[str, Any]:
        """
        1:1 Face Verification (Face on Document vs. User Selfie/Liveness):
        - Cosine similarity > 0.60 -> MATCH (LOW RISK, 0 pts)
        - Cosine similarity < 0.45 -> MISMATCH (+50 risk pts)
        - 0.45 <= similarity <= 0.60 -> BORDERLINE REVIEW (+25 risk pts)
        - If selfie is None: skip gracefully (0 penalty)
        """
        if doc_face_bgr is None or doc_face_bgr.size == 0:
            return {
                "status": "DOC_FACE_UNAVAILABLE",
                "similarity": 0.0,
                "risk_contribution": 0,
                "notes": "No facial portrait detected on document canvas"
            }

        if live_selfie_bgr is None or live_selfie_bgr.size == 0:
            return {
                "status": "SELFIE_NOT_PROVIDED",
                "similarity": 0.0,
                "risk_contribution": 0,
                "notes": "Optional presenter selfie not provided (zero fraud penalty applied)"
            }

        emb_doc = self.compute_face_embedding(doc_face_bgr)
        emb_live = self.compute_face_embedding(live_selfie_bgr)

        cos_sim = float(np.dot(emb_doc, emb_live))
        cos_sim = max(0.0, min(1.0, cos_sim))

        if cos_sim > 0.60:
            status = "MATCH_CONFIRMED"
            risk_pts = 0
            note = f"Biometric 1:1 face match confirmed ({cos_sim*100:.1f}% similarity)"
        elif cos_sim < 0.45:
            status = "MISMATCH_DETECTED"
            risk_pts = 50
            note = f"Biometric mismatch alert: Presenter face does not correspond to document photo ({cos_sim*100:.1f}% similarity < 0.45 threshold)"
        else:
            status = "MATCH_REVIEW"
            risk_pts = 25
            note = f"Biometric match borderline ({cos_sim*100:.1f}% similarity). Visual spot-check recommended."

        return {
            "status": status,
            "similarity": round(cos_sim, 3),
            "risk_contribution": risk_pts,
            "notes": note
        }

    def clear_registry(self) -> None:
        """Clears in-memory identity registry (useful for testing or cache purging)."""
        self._identity_registry.clear()

    def check_recycled_identity_1toN(
        self,
        doc_face_bgr: Optional[np.ndarray],
        current_document_number: str,
        current_name: Optional[str] = None,
        case_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        1:N Multi-Identity Check (Synthetic / Recycled Face Fraud):
        Detects if the same face embedding has already appeared associated with
        a DIFFERENT document number or different name.
        If collision detected -> Instant HIGH RISK (+70 pts).
        """
        if doc_face_bgr is None or doc_face_bgr.size == 0 or not current_document_number:
            return {
                "recycled_fraud_detected": False,
                "risk_contribution": 0,
                "matched_identities": []
            }

        emb = self.compute_face_embedding(doc_face_bgr)
        curr_doc_clean = current_document_number.strip().upper()
        curr_name_clean = (current_name or "").strip().upper()

        recycled_detected = False
        recycled_evidence = []
        best_match_sim = 0.0

        for rec in self._identity_registry:
            prior_emb = rec["embedding"]
            cos_sim = float(np.dot(emb, prior_emb))
            prior_doc = rec.get("doc_number", "")
            prior_name = rec.get("name", "")

            # If biometric match is high (> 0.85)
            if cos_sim > 0.85:
                best_match_sim = max(best_match_sim, cos_sim)
                if prior_doc and prior_doc != curr_doc_clean:
                    recycled_detected = True
                    recycled_evidence.append(
                        f"Recycled biometric face match: Same facial signature previously registered under Document Number '{prior_doc}' (now presented as '{curr_doc_clean}', similarity {cos_sim*100:.1f}%)"
                    )
                    break
                elif prior_name and curr_name_clean and prior_name != curr_name_clean:
                    recycled_detected = True
                    recycled_evidence.append(
                        f"Recycled biometric face match: Same facial signature previously registered under name '{prior_name}' (now presented as '{curr_name_clean}', similarity {cos_sim*100:.1f}%)"
                    )
                    break

        # Register current identity record if not already recorded under this doc_number with high similarity
        is_already_registered = any(
            r["doc_number"] == curr_doc_clean and float(np.dot(emb, r["embedding"])) > 0.95
            for r in self._identity_registry
        )
        if not is_already_registered:
            self._identity_registry.append({
                "embedding": emb,
                "doc_number": curr_doc_clean,
                "name": curr_name_clean,
                "case_id": case_id or "session",
                "registered_at": str(Path().cwd())
            })

        risk_pts = 70 if recycled_detected else 0

        return {
            "recycled_fraud_detected": recycled_detected,
            "risk_contribution": risk_pts,
            "best_match_similarity": round(best_match_sim, 3),
            "evidence": recycled_evidence
        }

    def execute_gate2(
        self,
        bgr_img: np.ndarray,
        ocr_boxes: Optional[List[Dict[str, int]]] = None,
        glare_mask: Optional[np.ndarray] = None,
        live_selfie_bgr: Optional[np.ndarray] = None,
        document_number: Optional[str] = None,
        holder_name: Optional[str] = None,
        case_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Master Gate 2 Orchestrator:
        Executes Differential ROI Forensics and Biometric 1:1 / 1:N verification.
        """
        # 1. Segment ROIs
        rois = self.segment_rois(bgr_img, ocr_boxes=ocr_boxes)

        # 2. Differential ELA
        forensic_res = self.compute_differential_ela(bgr_img, rois, glare_mask=glare_mask)

        # Extract doc face crop
        fx, fy, fw, fh = rois["face_box"]
        h, w = bgr_img.shape[:2]
        doc_face_crop = bgr_img[max(0, fy):min(h, fy + fh), max(0, fx):min(w, fx + fw)]

        # 3. Biometric 1:1 Verification
        bio_1to1 = self.verify_biometrics_1to1(doc_face_crop, live_selfie_bgr)

        # 4. Biometric 1:N Recycled Multi-Identity Check
        bio_1toN = self.check_recycled_identity_1toN(
            doc_face_crop,
            current_document_number=document_number or "",
            current_name=holder_name,
            case_id=case_id
        )

        total_risk = max(
            forensic_res["risk_contribution"],
            bio_1to1["risk_contribution"],
            bio_1toN["risk_contribution"]
        )

        critical_anomaly = (
            forensic_res["splicing_detected"] or
            bio_1to1["status"] == "MISMATCH_DETECTED" or
            bio_1toN["recycled_fraud_detected"]
        )

        return {
            "gate2_passed": not critical_anomaly,
            "forensic_status": forensic_res["status"],
            "delta_z_face": forensic_res["delta_z_face"],
            "delta_z_text": forensic_res["delta_z_text"],
            "max_delta_z": forensic_res["max_delta_z"],
            "splicing_detected": forensic_res["splicing_detected"],
            "flagged_rois": forensic_res["flagged_rois"],
            "rois": {
                "face_box": rois["face_box"],
                "text_box": rois["text_box"]
            },
            "biometrics_1to1": bio_1to1,
            "biometrics_1toN": bio_1toN,
            "total_risk_contribution": total_risk,
            "findings": forensic_res["findings"] + ([bio_1to1["notes"]] if bio_1to1["notes"] else []) + bio_1toN["evidence"]
        }


gate2_forensics = DifferentialROIForensics()
