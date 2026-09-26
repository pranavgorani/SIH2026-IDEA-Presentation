import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, Any, List
from backend.app.core.config import settings

class SyntheticDataGenerator:
    """
    Generates realistic synthetic identity documents labeled with clear demo banners.
    Includes accompanying sidecar metadata for deterministic test scenarios.
    """
    def __init__(self, output_dir: Path = settings.STORAGE_DIR / "synthetic"):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_all_presets(self) -> Dict[str, Dict[str, Any]]:
        scenarios = {
            "CASE-001": self._build_case_001_genuine_passport(),
            "CASE-002": self._build_case_002_medium_risk_id(),
            "CASE-003": self._build_case_003_high_risk_forged(),
            "CASE-004": self._build_case_004_expired_passport(),
            "CASE-005": self._build_case_005_photo_tampered(),
            "CASE-006": self._build_case_006_text_manipulated(),
            "CASE-007": self._build_case_007_face_mismatch(),
            "CASE-008": self._build_case_008_poor_quality()
        }

        generated_cases = {}
        for case_id, conf in scenarios.items():
            img_path = self.output_dir / f"{case_id}_doc.png"
            json_path = self.output_dir / f"{case_id}_doc.json"

            # Create visual image
            self._render_document_image(conf, img_path)

            # Optional live person image for face check
            live_path = None
            if conf.get("has_live_image"):
                live_path = self.output_dir / f"{case_id}_live.png"
                self._render_live_face_image(conf.get("live_match", True), live_path)

            # Write sidecar metadata
            meta = {
                "case_id": case_id,
                "title": conf["title"],
                "document_type": conf["document_type"],
                "raw_text": conf["raw_text"],
                "fields": conf["fields"],
                "tampering": conf.get("tampering", {"detected": False}),
                "target_risk": conf.get("target_risk", "LOW"),
                "live_match": conf.get("live_match"),
                "image_path": str(img_path),
                "live_image_path": str(live_path) if live_path else None
            }
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2)

            generated_cases[case_id] = meta

        return generated_cases

    def _render_document_image(self, conf: Dict[str, Any], target_path: Path):
        w, h = 880, 560
        # Background color
        bg_color = conf.get("bg_color", (242, 245, 249))
        img = Image.new("RGB", (w, h), bg_color)
        draw = ImageDraw.Draw(img)

        # Border
        draw.rectangle([10, 10, w - 10, h - 10], outline=(150, 165, 185), width=3)
        draw.rectangle([16, 16, w - 16, h - 16], outline=(200, 215, 230), width=1)

        # Header banner (Government look)
        header_color = conf.get("header_color", (24, 43, 73))
        draw.rectangle([16, 16, w - 16, 75], fill=header_color)

        # Demo Banner (Mandatory safety notice)
        draw.rectangle([16, 76, w - 16, 102], fill=(220, 38, 38))
        draw.text((w // 2 - 190, 81), "DEMO / SYNTHETIC DATA — FOR SIH HACKATHON EVALUATION ONLY", fill=(255, 255, 255))

        # Title text
        doc_title = conf.get("title", "PASSPORT / PASSEPORT").upper()
        draw.text((35, 32), doc_title, fill=(255, 255, 255))
        draw.text((w - 220, 32), conf.get("doc_code", "DEMO ISSUANCE"), fill=(210, 225, 245))

        # Portrait Box (Left)
        draw.rectangle([40, 130, 250, 410], fill=(225, 232, 242), outline=(130, 145, 165), width=2)
        # Face silhouette / mock photo
        draw.ellipse([100, 170, 190, 270], fill=(160, 175, 195)) # head
        draw.ellipse([70, 280, 220, 420], fill=(110, 130, 155)) # shoulders
        draw.text((75, 380), "[ SYNTHETIC PHOTO ]", fill=(60, 75, 95))

        # If photo tampered scenario, draw visible splice boundary or noise
        if conf.get("is_photo_tampered"):
            draw.rectangle([35, 125, 255, 415], outline=(255, 0, 0), width=3)
            draw.text((45, 135), "TAMPERED REGION", fill=(255, 0, 0))

        # Text Fields (Right)
        fields = conf.get("fields", {})
        cx = 290
        cy = 135
        row_h = 42

        labels = [
            ("DOCUMENT NUMBER", fields.get("document_number", "K81927361")),
            ("SURNAME / NOM", fields.get("name", "SHARMA").split()[0] if fields.get("name") else ""),
            ("GIVEN NAMES", " ".join(fields.get("name", "").split()[1:]) if fields.get("name") else ""),
            ("NATIONALITY", fields.get("nationality", "DEMO")),
            ("DATE OF BIRTH", fields.get("date_of_birth", "1992-05-14")),
            ("SEX", fields.get("gender", "M")),
            ("EXPIRY DATE", fields.get("date_of_expiry", "2028-06-09")),
        ]

        for i, (label, val) in enumerate(labels):
            y_pos = cy + i * row_h
            if y_pos > 430:
                break
            draw.text((cx, y_pos), label, fill=(100, 116, 139))
            draw.text((cx + 210, y_pos), str(val), fill=(15, 23, 42))
            draw.line([(cx, y_pos + 32), (w - 40, y_pos + 32)], fill=(226, 232, 240), width=1)

        # If text manipulated, add visual artifact in DOB area
        if conf.get("is_text_tampered"):
            draw.rectangle([cx + 200, cy + 4 * row_h - 4, cx + 380, cy + 4 * row_h + 28], outline=(255, 100, 0), width=2)

        # Bottom MRZ band
        if conf.get("has_mrz", True):
            draw.rectangle([16, 445, w - 16, 545], fill=(238, 242, 246), outline=(180, 195, 210), width=1)
            mrz_lines = conf.get("mrz_lines", [
                "P<DEMSHARMA<<ARJUN<VIKRAM<<<<<<<<<<<<<<<<<<<",
                "K819273615DEM9205148M2806093<<<<<<<<<<<<<<02"
            ])
            for idx, line in enumerate(mrz_lines):
                draw.text((35, 460 + idx * 36), line, fill=(15, 23, 42))

        # Save
        img.save(target_path, "PNG")

    def _render_live_face_image(self, is_matching: bool, target_path: Path):
        img = Image.new("RGB", (400, 400), (235, 240, 248))
        draw = ImageDraw.Draw(img)
        draw.rectangle([5, 5, 395, 395], outline=(180, 195, 215), width=2)
        draw.text((20, 20), "LIVE CAMERA CAPTURE (DEMO)", fill=(30, 41, 59))

        if is_matching:
            # Similar geometry
            draw.ellipse([130, 100, 270, 250], fill=(160, 175, 195))
            draw.ellipse([80, 260, 320, 410], fill=(110, 130, 155))
            draw.text((120, 350), "[ MATCHING INDIVIDUAL ]", fill=(30, 41, 59))
        else:
            # Different geometry (mismatch scenario)
            draw.ellipse([150, 120, 250, 230], fill=(195, 160, 160))
            draw.ellipse([90, 240, 310, 400], fill=(145, 100, 100))
            draw.text((110, 350), "[ DIFFERENT PERSON ]", fill=(180, 0, 0))

        img.save(target_path, "PNG")

    # 8 Presets
    def _build_case_001_genuine_passport(self) -> Dict[str, Any]:
        return {
            "title": "REPUBLIC OF DEMO — PASSPORT",
            "doc_code": "OFFICIAL CREDENTIAL",
            "document_type": "PASSPORT",
            "target_risk": "LOW",
            "has_mrz": True,
            "has_live_image": True,
            "live_match": True,
            "fields": {
                "name": "SHARMA ARJUN VIKRAM",
                "document_number": "K81927361",
                "nationality": "DEMO",
                "date_of_birth": "1992-05-14",
                "date_of_issue": "2018-06-10",
                "date_of_expiry": "2028-06-09",
                "gender": "M",
                "issuing_country": "DEMO"
            },
            "mrz_lines": [
                "P<DEMSHARMA<<ARJUN<VIKRAM<<<<<<<<<<<<<<<<<<<",
                "K819273611DEM9205141M2806099<<<<<<<<<<<<<<04"
            ],
            "raw_text": "REPUBLIC OF DEMO\nPASSPORT\nSurname: SHARMA\nGiven Names: ARJUN VIKRAM\nPassport No: K81927361\nNationality: DEMO\nDOB: 14 MAY 1992\nExpiry: 09 JUN 2028\nP<DEMSHARMA<<ARJUN<VIKRAM<<<<<<<<<<<<<<<<<<<\nK819273611DEM9205141M2806099<<<<<<<<<<<<<<04"
        }

    def _build_case_002_medium_risk_id(self) -> Dict[str, Any]:
        return {
            "title": "NATIONAL IDENTITY CARD",
            "doc_code": "CIVIL REGISTRY",
            "document_type": "NATIONAL_ID",
            "target_risk": "MEDIUM",
            "has_mrz": False,
            "has_live_image": False,
            "fields": {
                "name": "KUMAR RAJESH",
                "document_number": "ID99281720",
                "nationality": "DEMO",
                "date_of_birth": "1988-11-23",
                "date_of_issue": "2016-03-01",
                "date_of_expiry": "2027-02-28",
                "gender": "M",
                "issuing_country": "DEMO"
            },
            "raw_text": "NATIONAL IDENTITY CARD\nID No: ID99281720\nName: KUMAR RAJESH\nDOB: 23 NOV 1988\nExpiry: 28 FEB 2027\nNationality: DEMO"
        }

    def _build_case_003_high_risk_forged(self) -> Dict[str, Any]:
        return {
            "title": "CONSULAR TRAVEL VISA",
            "doc_code": "BORDER CONTROL",
            "document_type": "VISA",
            "target_risk": "HIGH",
            "has_mrz": False,
            "has_live_image": False,
            "tampering": {
                "detected": True,
                "confidence": 0.91,
                "regions": [
                    {"x": 280, "y": 140, "width": 320, "height": 60, "type": "spliced_text_header", "confidence": 0.89, "explanation": "Font metrics and compression rate discontinuity in visa class header."}
                ],
                "evidence": ["Inconsistent background security guilloche pattern.", "Document reported REVOKED in simulated visa issuance records."]
            },
            "fields": {
                "name": "ALTERED RECORD",
                "document_number": "TAMPER007",
                "nationality": "FORGE",
                "date_of_birth": "1975-01-01",
                "date_of_issue": "2020-01-01",
                "date_of_expiry": "2027-04-12",
                "gender": "M",
                "issuing_country": "UNKNOWN"
            },
            "raw_text": "CONSULAR TRAVEL VISA\nVisa No: TAMPER007\nBearer: ALTERED RECORD\nDOB: 01 JAN 1975\nExpiry: 12 APR 2027"
        }

    def _build_case_004_expired_passport(self) -> Dict[str, Any]:
        return {
            "title": "REPUBLIC OF DEMO — PASSPORT (EXPIRED)",
            "doc_code": "EXPIRED CREDENTIAL",
            "document_type": "PASSPORT",
            "target_risk": "HIGH",
            "has_mrz": True,
            "has_live_image": False,
            "fields": {
                "name": "PATEL PRIYA",
                "document_number": "EXP998877",
                "nationality": "DEMO",
                "date_of_birth": "1985-04-12",
                "date_of_issue": "2011-01-16",
                "date_of_expiry": "2022-01-15",
                "gender": "F",
                "issuing_country": "DEMO"
            },
            "mrz_lines": [
                "P<DEMPATEL<<PRIYA<<<<<<<<<<<<<<<<<<<<<<<<<<<",
                "EXP9988772DEM8504124F2201156<<<<<<<<<<<<<<04"
            ],
            "raw_text": "REPUBLIC OF DEMO\nPASSPORT\nSurname: PATEL\nGiven Names: PRIYA\nPassport No: EXP998877\nDOB: 12 APR 1985\nExpiry: 15 JAN 2022\nP<DEMPATEL<<PRIYA<<<<<<<<<<<<<<<<<<<<<<<<<<<\nEXP9988772DEM8504124F2201156<<<<<<<<<<<<<<04"
        }

    def _build_case_005_photo_tampered(self) -> Dict[str, Any]:
        return {
            "title": "PASSPORT — SUSPICIOUS PHOTO OVERLAY",
            "doc_code": "BORDER ALERT",
            "document_type": "PASSPORT",
            "target_risk": "HIGH",
            "has_mrz": True,
            "is_photo_tampered": True,
            "has_live_image": False,
            "tampering": {
                "detected": True,
                "confidence": 0.94,
                "regions": [
                    {"x": 40, "y": 130, "width": 210, "height": 280, "type": "photo_replacement", "confidence": 0.95, "explanation": "High Error Level Analysis (ELA) variance along photo boundaries indicates secondary digital overlay."}
                ],
                "evidence": ["Edge discontinuity along photo border.", "Compression artifact mismatch between portrait and substrate."]
            },
            "fields": {
                "name": "SINGH GURPREET",
                "document_number": "P88129031",
                "nationality": "DEMO",
                "date_of_birth": "1990-08-19",
                "date_of_issue": "2019-02-11",
                "date_of_expiry": "2029-02-10",
                "gender": "M",
                "issuing_country": "DEMO"
            },
            "mrz_lines": [
                "P<DEMSINGH<<GURPREET<<<<<<<<<<<<<<<<<<<<<<<<",
                "P881290314DEM9008191M2902108<<<<<<<<<<<<<<01"
            ],
            "raw_text": "REPUBLIC OF DEMO\nPASSPORT\nSurname: SINGH\nGiven Names: GURPREET\nPassport No: P88129031\nDOB: 19 AUG 1990\nExpiry: 10 FEB 2029"
        }

    def _build_case_006_text_manipulated(self) -> Dict[str, Any]:
        return {
            "title": "NATIONAL ID — TEXT ALTERATION",
            "doc_code": "FORENSIC ALERT",
            "document_type": "NATIONAL_ID",
            "target_risk": "HIGH",
            "has_mrz": False,
            "is_text_tampered": True,
            "has_live_image": False,
            "tampering": {
                "detected": True,
                "confidence": 0.88,
                "regions": [
                    {"x": 490, "y": 300, "width": 220, "height": 45, "type": "text_manipulation", "confidence": 0.89, "explanation": "Localized pixel noise inconsistency and font aliasing in Date of Birth text block."}
                ],
                "evidence": ["Local pixel variance delta in DOB field.", "Sub-pixel font interpolation disparity."]
            },
            "fields": {
                "name": "VERMA ANITA",
                "document_number": "ID77218390",
                "nationality": "DEMO",
                "date_of_birth": "1980-03-25",
                "date_of_issue": "2021-05-10",
                "date_of_expiry": "2031-05-09",
                "gender": "F",
                "issuing_country": "DEMO"
            },
            "raw_text": "NATIONAL ID\nID: ID77218390\nName: VERMA ANITA\nDOB: 25 MAR 1980\nExpiry: 09 MAY 2031"
        }

    def _build_case_007_face_mismatch(self) -> Dict[str, Any]:
        return {
            "title": "PASSPORT — BIOMETRIC MISMATCH SCENARIO",
            "doc_code": "BIOMETRIC GATE",
            "document_type": "PASSPORT",
            "target_risk": "HIGH",
            "has_mrz": True,
            "has_live_image": True,
            "live_match": False, # Triggers face mismatch
            "fields": {
                "name": "SMITH JOHN EDWARD",
                "document_number": "A12345678",
                "nationality": "USA",
                "date_of_birth": "1987-12-04",
                "date_of_issue": "2019-11-21",
                "date_of_expiry": "2029-11-20",
                "gender": "M",
                "issuing_country": "USA"
            },
            "mrz_lines": [
                "P<USASMITH<<JOHN<EDWARD<<<<<<<<<<<<<<<<<<<<<",
                "A123456780USA8712042M2911201<<<<<<<<<<<<<<06"
            ],
            "raw_text": "UNITED STATES OF AMERICA\nPASSPORT\nSurname: SMITH\nGiven Names: JOHN EDWARD\nPassport No: A12345678\nDOB: 04 DEC 1987\nExpiry: 20 NOV 2029"
        }

    def _build_case_008_poor_quality(self) -> Dict[str, Any]:
        return {
            "title": "BLURRY & UNDEREXPOSED SCAN",
            "doc_code": "QUALITY REJECTION",
            "document_type": "DRIVING_LICENSE",
            "target_risk": "MEDIUM",
            "bg_color": (80, 85, 95), # dark underexposed
            "header_color": (30, 35, 45),
            "has_mrz": False,
            "has_live_image": False,
            "fields": {
                "name": "UNKNOWN DRIVER",
                "document_number": "DL99812",
                "nationality": "DEMO",
                "date_of_birth": "1991-01-01",
                "date_of_issue": "2015-01-01",
                "date_of_expiry": "2030-01-01",
                "gender": "M",
                "issuing_country": "DEMO"
            },
            "raw_text": "DRIVING LICENCE\nDL NO: DL99812\nNAME: UNKNOWN DRIVER"
        }

synthetic_generator = SyntheticDataGenerator()
