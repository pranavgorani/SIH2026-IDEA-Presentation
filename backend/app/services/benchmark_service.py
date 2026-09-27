"""
TRUST-ID — 100-Document Border Stream Benchmark & Simulation Service
Generates realistic 100-document inspection batches reflecting the 7 core border checkpoint challenges:
1. Fake passports and visas
2. Altered photographs (Photo replacement)
3. Modified dates of birth
4. Tampered visa stamps
5. Identity impersonation (Biometric mismatch)
6. Multiple identities / Expired / Blacklisted documents
7. High passenger volume delay mitigation (Sub-2s processing)

Covers the 4 SIH Architecture Modules:
- Module 1: OCR Extraction (Passport & Visa fields)
- Module 2: Document Validation (Standards, Expiry, Logic)
- Module 3: Tampering Detection (AI Forensics, ELA, Splicing)
- Module 4: Face Verification (1:1 Biometric Comparison)
"""

import random
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

SAMPLE_NAMES = [
    ("Vikramaditya Sharma", "IND", "M"),
    ("Elena Rostova", "DEU", "F"),
    ("Kwame Mensah", "GHA", "M"),
    ("Mei-Ling Chen", "SGP", "F"),
    ("Carlos Mendoza", "MEX", "M"),
    ("Fatima Al-Mansoor", "ARE", "F"),
    ("David O'Connor", "GBR", "M"),
    ("Amina Diallo", "SEN", "F"),
    ("Hans Mueller", "DEU", "M"),
    ("Kenji Takahashi", "JPN", "M"),
    ("Sophia Dubois", "FRA", "F"),
    ("Mateo Rossi", "ITA", "M"),
    ("Ananya Patel", "IND", "F"),
    ("Liam Smith", "AUS", "M"),
    ("Chloe Tremblay", "CAN", "F"),
    ("Alejandro Silva", "BRA", "M"),
    ("Zara Ibrahim", "NGA", "F"),
    ("Tariq Al-Fassi", "MAR", "M"),
    ("Olga Ivanova", "KAZ", "F"),
    ("Min-Jun Kim", "KOR", "M")
]

VISA_TYPES = [
    ("Consular Tourist B-2", "MULTIPLE", "90 Days"),
    ("Business Visitor C-1", "SINGLE", "30 Days"),
    ("Diplomatic Official A-1", "MULTIPLE", "180 Days"),
    ("Work Assignment H-1", "MULTIPLE", "365 Days"),
    ("Transit Transit G-2", "SINGLE", "7 Days")
]

class BenchmarkService:
    @staticmethod
    def generate_100_document_benchmark(random_seed: Optional[int] = None) -> Dict[str, Any]:
        rng = random.Random(random_seed if random_seed is not None else 42)
        
        documents: List[Dict[str, Any]] = []
        
        # Challenge assignment for the 32 failing/flagged documents:
        # 8 Photo Replacement, 7 Modified DOB, 5 Tampered Visa Stamp, 
        # 4 Fake Passport/Visa, 4 Face Mismatch, 4 Expired/Blacklisted
        fail_challenges = (
            ["PHOTO_REPLACEMENT"] * 8 +
            ["MODIFIED_DOB"] * 7 +
            ["TAMPERED_VISA_STAMP"] * 5 +
            ["FAKE_DOCUMENT"] * 4 +
            ["IDENTITY_IMPERSONATION"] * 4 +
            ["EXPIRED_BLACKLISTED"] * 4
        )
        rng.shuffle(fail_challenges)
        
        # 68 clean documents
        all_challenges = (["CLEAN"] * 68) + fail_challenges
        rng.shuffle(all_challenges)
        
        for idx in range(1, 101):
            challenge = all_challenges[idx - 1]
            is_pass = (challenge == "CLEAN")
            
            # Select document type
            if challenge == "TAMPERED_VISA_STAMP":
                doc_type = "VISA"
            elif idx <= 45:
                doc_type = "PASSPORT"
            elif idx <= 70:
                doc_type = "VISA"
            elif idx <= 88:
                doc_type = "NATIONAL_ID"
            else:
                doc_type = "PERMIT"
                
            name_tuple = rng.choice(SAMPLE_NAMES)
            holder_name = name_tuple[0]
            nationality = name_tuple[1]
            gender = name_tuple[2]
            
            doc_num_raw = f"{rng.choice(['P', 'V', 'N', 'D'])}{rng.randint(10000000, 99999999)}"
            masked_doc_num = f"{doc_num_raw[:2]}••••{doc_num_raw[-2:]}"
            
            # Dates
            birth_year = rng.randint(1972, 2003)
            birth_month = rng.randint(1, 12)
            birth_day = rng.randint(1, 28)
            dob_str = f"{birth_year:04d}-{birth_month:02d}-{birth_day:02d}"
            
            issue_year = rng.randint(2018, 2024)
            issue_month = rng.randint(1, 12)
            issue_day = rng.randint(1, 28)
            issue_str = f"{issue_year:04d}-{issue_month:02d}-{issue_day:02d}"
            
            if challenge == "EXPIRED_BLACKLISTED" and rng.choice([True, False]):
                expiry_year = rng.randint(2021, 2023)  # Expired
            else:
                expiry_year = issue_year + rng.choice([5, 10])
            expiry_str = f"{expiry_year:04d}-{issue_month:02d}-{issue_day:02d}"
            
            # Visa fields if applicable
            visa_info = rng.choice(VISA_TYPES)
            visa_fields = {
                "visa_number": f"V-{rng.randint(1000000, 9999999)}",
                "visa_type": visa_info[0],
                "entry_validation": visa_info[1],
                "stay_duration": visa_info[2]
            } if doc_type == "VISA" else {}
            
            # Module 1: OCR Extraction
            ocr_conf = round(rng.uniform(0.93, 0.99) if is_pass else rng.uniform(0.81, 0.94), 2)
            ocr_fields = {
                "name": holder_name,
                "document_number": masked_doc_num,
                "nationality": nationality,
                "date_of_birth": dob_str,
                "date_of_expiry": expiry_str,
                "gender": gender,
                **visa_fields
            }
            
            # Module 2: Document Validation
            val_status = "PASS"
            val_issue = "Official ICAO standards satisfied"
            if challenge == "MODIFIED_DOB":
                val_status = "FAIL"
                val_issue = "Chronological violation: Birth date in visual zone contradicts MRZ encoded check digit (DOB altered)"
            elif challenge == "FAKE_DOCUMENT":
                val_status = "FAIL"
                val_issue = "Checksum mismatch: ICAO 9303 composite check digit failed arithmetic verification"
            elif challenge == "EXPIRED_BLACKLISTED":
                val_status = "FAIL"
                val_issue = "Document expired or flagged in international revocation database"
                
            # Module 3: Tampering Detection
            tamper_status = "PASS"
            photo_rep = False
            text_manip = False
            stamp_forg = False
            meta_anom = False
            ela_score = round(rng.uniform(0.04, 0.18), 3)
            tamper_desc = "No physical or digital tampering detected"
            
            if challenge == "PHOTO_REPLACEMENT":
                tamper_status = "FAIL"
                photo_rep = True
                ela_score = round(rng.uniform(0.81, 0.96), 3)
                tamper_desc = "High-confidence photo replacement detected: ELA compression boundary and edge gradient discontinuity"
            elif challenge == "TAMPERED_VISA_STAMP":
                tamper_status = "FAIL"
                stamp_forg = True
                ela_score = round(rng.uniform(0.72, 0.89), 3)
                tamper_desc = "Consular ink forgery detected: Splicing artifacts in entry validation stamp region"
            elif challenge == "MODIFIED_DOB":
                tamper_status = "FAIL"
                text_manip = True
                ela_score = round(rng.uniform(0.68, 0.84), 3)
                tamper_desc = "Digital text manipulation detected around birth year glyphs (font metric anomaly)"
            elif challenge == "FAKE_DOCUMENT":
                tamper_status = "FAIL"
                meta_anom = True
                ela_score = round(rng.uniform(0.65, 0.85), 3)
                tamper_desc = "Synthetic reproduction: Missing microscopic guilloche substrate patterns"
                
            # Module 4: Face Verification
            face_status = "PASS"
            sim_score = round(rng.uniform(0.82, 0.97), 2)
            face_desc = "Biometric 1:1 match verified between document portrait and live presenter"
            if challenge == "IDENTITY_IMPERSONATION":
                face_status = "FAIL"
                sim_score = round(rng.uniform(0.18, 0.35), 2)
                face_desc = "Identity impersonation detected: Live face does not match document portrait (Cosine distance: 0.74)"
            elif rng.random() < 0.12 and is_pass:
                face_status = "NOT_APPLICABLE"
                sim_score = 0.0
                face_desc = "Live presenter portrait not provided (Document screening only)"
                
            # Compute Risk & Integrity Scores
            if is_pass:
                risk_score = rng.randint(8, 24)
                risk_level = "LOW"
                integrity_score = rng.randint(92, 99)
                checks_passed = rng.randint(86, 95)
                checks_failed = 0
                checks_warnings = 100 - checks_passed - rng.randint(2, 6)
                checks_unavail = rng.randint(2, 4)
                checks_not_app = 100 - (checks_passed + checks_failed + checks_warnings + checks_unavail)
                verdict = "PASS"
                primary_label = "CLEAN — Low Risk"
            else:
                risk_score = rng.randint(68, 96)
                risk_level = "HIGH"
                integrity_score = rng.randint(34, 58)
                checks_failed = rng.randint(4, 11)
                checks_passed = rng.randint(62, 78)
                checks_warnings = rng.randint(8, 16)
                checks_unavail = rng.randint(2, 4)
                checks_not_app = 100 - (checks_passed + checks_failed + checks_warnings + checks_unavail)
                verdict = "FAIL"
                
                label_map = {
                    "PHOTO_REPLACEMENT": "CRITICAL: Photo Replacement Detected",
                    "MODIFIED_DOB": "HIGH RISK: Altered Date of Birth",
                    "TAMPERED_VISA_STAMP": "HIGH RISK: Tampered Visa Stamp",
                    "FAKE_DOCUMENT": "CRITICAL: Counterfeit Credential",
                    "IDENTITY_IMPERSONATION": "CRITICAL: Face Impersonation Attempt",
                    "EXPIRED_BLACKLISTED": "HIGH RISK: Blacklisted / Expired Document"
                }
                primary_label = label_map.get(challenge, "HIGH RISK: Fraud Detected")
                
            latency_sec = round(rng.uniform(1.2, 2.3), 2)
            case_num = f"CASE-2026-B{idx:03d}"
            
            # Sample checks representative snapshot
            sample_checks = [
                {
                    "check_id": "CHK-001",
                    "category": "DOCUMENT_INTEGRITY",
                    "name": "Document image readable",
                    "status": "PASS",
                    "confidence": ocr_conf,
                    "evidence": "Optical resolution 1080p, contrast ratio 8.2:1 optimal"
                },
                {
                    "check_id": "CHK-016",
                    "category": "OCR_TEXT_EXTRACTION",
                    "name": "OCR completed & fields extracted",
                    "status": "PASS",
                    "confidence": ocr_conf,
                    "evidence": f"Extracted {len(ocr_fields)} structured identity fields"
                },
                {
                    "check_id": "CHK-038",
                    "category": "FIELD_LOGICAL_VALIDATION",
                    "name": "DOB is logically valid",
                    "status": "FAIL" if challenge == "MODIFIED_DOB" else "PASS",
                    "confidence": 0.95,
                    "evidence": "Logical chronology violation detected" if challenge == "MODIFIED_DOB" else "DOB satisfies ICAO chronological logic"
                },
                {
                    "check_id": "CHK-047",
                    "category": "MRZ_DATA",
                    "name": "MRZ format valid & check digits match",
                    "status": "FAIL" if challenge == "FAKE_DOCUMENT" else "PASS",
                    "confidence": 0.98,
                    "evidence": "Composite check digit mismatch in line 2" if challenge == "FAKE_DOCUMENT" else "All 3 check digits validated via mod-10 weight algorithm"
                },
                {
                    "check_id": "CHK-057",
                    "category": "VISUAL_FORENSICS",
                    "name": "Possible photo replacement",
                    "status": "FAIL" if challenge == "PHOTO_REPLACEMENT" else "PASS",
                    "confidence": 0.92 if challenge == "PHOTO_REPLACEMENT" else 0.98,
                    "evidence": f"ELA tamper score {ela_score}: Boundary splicing detected" if challenge == "PHOTO_REPLACEMENT" else f"ELA score {ela_score}: No boundary alteration"
                },
                {
                    "check_id": "CHK-067",
                    "category": "VISUAL_FORENSICS",
                    "name": "Stamp forgery / anomaly detected",
                    "status": "FAIL" if challenge == "TAMPERED_VISA_STAMP" else "PASS",
                    "confidence": 0.89,
                    "evidence": "Stamp ink matrix discontinuity detected in consular zone" if challenge == "TAMPERED_VISA_STAMP" else "Consular stamp ink matrix is continuous"
                },
                {
                    "check_id": "CHK-076",
                    "category": "IDENTITY_VERIFICATION",
                    "name": "Face similarity between document and live presenter",
                    "status": "FAIL" if challenge == "IDENTITY_IMPERSONATION" else ("NOT_APPLICABLE" if face_status == "NOT_APPLICABLE" else "PASS"),
                    "confidence": sim_score if face_status != "NOT_APPLICABLE" else 0.0,
                    "evidence": f"Facial cosine similarity score: {sim_score} (Threshold: 0.65)"
                },
                {
                    "check_id": "CHK-083",
                    "category": "RECORD_VERIFICATION",
                    "name": "Document status valid in source database",
                    "status": "FAIL" if challenge == "EXPIRED_BLACKLISTED" else "PASS",
                    "confidence": 0.97,
                    "evidence": "Watchlist match: Document flagged on alert registry" if challenge == "EXPIRED_BLACKLISTED" else "Active status confirmed on issuing authority record"
                }
            ]
            
            risk_score_10 = round(risk_score / 10.0, 1)
            risk_verdict_10 = "LOW RISK (PASS)" if risk_score <= 35 else ("MEDIUM RISK (REVIEW)" if risk_score <= 65 else "HIGH RISK (FAIL)")

            doc_record = {
                "id": f"bench-doc-{idx:03d}",
                "case_number": case_num,
                "document_type": doc_type,
                "holder_name": holder_name,
                "nationality": nationality,
                "document_number": masked_doc_num,
                "date_of_birth": dob_str,
                "date_of_expiry": expiry_str,
                "gender": gender,
                "status": verdict,
                "challenge_category": challenge,
                "primary_challenge_label": primary_label,
                "risk_score": risk_score,
                "risk_score_10": risk_score_10,
                "risk_verdict_10": risk_verdict_10,
                "risk_level": risk_level,
                "document_integrity_score": integrity_score,
                "processing_time_sec": latency_sec,
                "modules": {
                    "ocr": {
                        "status": "PASS",
                        "confidence": ocr_conf,
                        "fields": ocr_fields
                    },
                    "validation": {
                        "status": val_status,
                        "issue": val_issue
                    },
                    "tampering": {
                        "status": tamper_status,
                        "photo_replacement": photo_rep,
                        "text_manipulation": text_manip,
                        "stamp_forgery": stamp_forg,
                        "metadata_anomaly": meta_anom,
                        "ela_score": ela_score,
                        "description": tamper_desc
                    },
                    "face": {
                        "status": face_status,
                        "similarity": sim_score,
                        "description": face_desc
                    }
                },
                "checks_summary": {
                    "total_checks": 100,
                    "passed": checks_passed,
                    "failed": checks_failed,
                    "warnings": checks_warnings,
                    "unavailable": checks_unavail,
                    "not_applicable": checks_not_app
                },
                "sample_checks": sample_checks,
                "scanned_at": (datetime.now() - timedelta(minutes=rng.randint(2, 480))).strftime("%Y-%m-%d %H:%M:%S")
            }
            documents.append(doc_record)
            
        # Top-level aggregate stats
        passed_count = sum(1 for d in documents if d["status"] == "PASS")
        failed_count = sum(1 for d in documents if d["status"] == "FAIL")
        avg_time = round(sum(d["processing_time_sec"] for d in documents) / len(documents), 2)
        avg_risk = round(sum(d["risk_score"] for d in documents) / len(documents), 1)
        avg_risk_10 = round(avg_risk / 10.0, 1)
        avg_integ = round(sum(d["document_integrity_score"] for d in documents) / len(documents), 1)
        
        challenges_breakdown = {
            "photo_replacement": sum(1 for d in documents if d["challenge_category"] == "PHOTO_REPLACEMENT"),
            "modified_dob": sum(1 for d in documents if d["challenge_category"] == "MODIFIED_DOB"),
            "tampered_visa_stamp": sum(1 for d in documents if d["challenge_category"] == "TAMPERED_VISA_STAMP"),
            "fake_document": sum(1 for d in documents if d["challenge_category"] == "FAKE_DOCUMENT"),
            "identity_impersonation": sum(1 for d in documents if d["challenge_category"] == "IDENTITY_IMPERSONATION"),
            "expired_blacklisted": sum(1 for d in documents if d["challenge_category"] == "EXPIRED_BLACKLISTED"),
            "clean_passed": passed_count
        }
        
        module_stats = {
            "module_1_ocr_pass_rate": round(100.0, 1),
            "module_2_validation_pass_rate": round(sum(1 for d in documents if d["modules"]["validation"]["status"] == "PASS") / 100 * 100, 1),
            "module_3_tampering_pass_rate": round(sum(1 for d in documents if d["modules"]["tampering"]["status"] == "PASS") / 100 * 100, 1),
            "module_4_face_pass_rate": round(sum(1 for d in documents if d["modules"]["face"]["status"] in ("PASS", "NOT_APPLICABLE")) / 100 * 100, 1),
        }

        # 100-Point Checks Category Breakdown for Charts (10 checks per category = exactly 100 checks)
        checks_100_categories_graph = [
            {"category": "Doc Physical Layout", "short": "Layout", "passed": 9, "failed": 1, "total": 10},
            {"category": "Image Clarity & DPI", "short": "Clarity", "passed": 8, "failed": 2, "total": 10},
            {"category": "ICAO 9303 MRZ Math", "short": "MRZ Math", "passed": 8, "failed": 2, "total": 10},
            {"category": "Field Logic & DOB", "short": "DOB Logic", "passed": 7, "failed": 3, "total": 10},
            {"category": "ELA Photo Forensics", "short": "Photo ELA", "passed": 6, "failed": 4, "total": 10},
            {"category": "Visa Stamp Matrix", "short": "Stamps", "passed": 6, "failed": 4, "total": 10},
            {"category": "Biometric 1:1 Face", "short": "Biometric", "passed": 7, "failed": 3, "total": 10},
            {"category": "Issuing Authority DB", "short": "Authority", "passed": 7, "failed": 3, "total": 10},
            {"category": "Multi-Signal ML Fusion", "short": "ML Fusion", "passed": 7, "failed": 3, "total": 10},
            {"category": "SHA-256 Audit Seal", "short": "Audit Seal", "passed": 10, "failed": 0, "total": 10},
        ]

        risk_distribution_10 = [
            {"tier": "0.0 - 2.0 (Low Risk / Pass)", "range": "0-2", "count": 48, "verdict": "PASS", "color": "#10B981"},
            {"tier": "2.1 - 3.5 (Low Risk / Pass)", "range": "2.1-3.5", "count": 20, "verdict": "PASS", "color": "#059669"},
            {"tier": "3.6 - 6.5 (Medium / Review)", "range": "3.6-6.5", "count": 14, "verdict": "REVIEW", "color": "#F59E0B"},
            {"tier": "6.6 - 8.5 (High Risk / Fail)", "range": "6.6-8.5", "count": 12, "verdict": "FAIL", "color": "#EF4444"},
            {"tier": "8.6 - 10.0 (Critical / Fail)", "range": "8.6-10", "count": 6, "verdict": "FAIL", "color": "#DC2626"},
        ]

        border_threats_graph = [
            {"threat": "Altered Photos", "count": challenges_breakdown["photo_replacement"], "color": "#A855F7"},
            {"threat": "Modified DOB", "count": challenges_breakdown["modified_dob"], "color": "#F59E0B"},
            {"threat": "Tampered Stamps", "count": challenges_breakdown["tampered_visa_stamp"], "color": "#F43F5E"},
            {"threat": "Fake Docs", "count": challenges_breakdown["fake_document"], "color": "#EF4444"},
            {"threat": "Impersonation", "count": challenges_breakdown["identity_impersonation"], "color": "#0EA5E9"},
            {"threat": "Expired/Blacklist", "count": challenges_breakdown["expired_blacklisted"], "color": "#DC2626"},
        ]
        
        return {
            "total_documents": 100,
            "passed": passed_count,
            "passed_count": passed_count,
            "failed": failed_count,
            "failed_count": failed_count,
            "pass_rate": round(passed_count / 100 * 100, 1),
            "fail_rate": round(failed_count / 100 * 100, 1),
            "avg_processing_time_sec": avg_time,
            "avg_risk_score": avg_risk,
            "avg_risk_score_10": avg_risk_10,
            "avg_integrity_score": avg_integ,
            "challenges_breakdown": challenges_breakdown,
            "common_challenges_breakdown": challenges_breakdown,
            "checks_100_categories_graph": checks_100_categories_graph,
            "risk_distribution_10": risk_distribution_10,
            "border_threats_graph": border_threats_graph,
            "module_stats": module_stats,
            "modules_overview": {
                "ocr": {"accuracy": 100.0, "passed": 100, "failed": 0},
                "validation": {"passed": sum(1 for d in documents if d["modules"]["validation"]["status"] == "PASS"), "failed": sum(1 for d in documents if d["modules"]["validation"]["status"] != "PASS")},
                "tampering": {"passed": sum(1 for d in documents if d["modules"]["tampering"]["status"] == "PASS"), "failed": sum(1 for d in documents if d["modules"]["tampering"]["status"] != "PASS")},
                "face_verification": {"passed": sum(1 for d in documents if d["modules"]["face"]["status"] in ("PASS", "NOT_APPLICABLE")), "failed": sum(1 for d in documents if d["modules"]["face"]["status"] == "FAIL")},
            },
            "documents": documents
        }

benchmark_service = BenchmarkService()
