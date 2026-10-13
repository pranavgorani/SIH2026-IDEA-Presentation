# Smart India Hackathon (SIH) 2026 Submission Document

## 1. Project Title
**Nyaya-Tula AI — Automated Forensic Document Screening, Tampering Detection & Clearance Support**

## 2. Problem Statement
Identity fraud and tampered travel documents pose critical security vulnerabilities at borders, immigration checkpoints, and civil authentication centers. Frontline verification personnel face high passenger volumes with limited forensic tools, leading to either long queues or missed fraudulent alterations.

## 3. Proposed Solution
An end-to-end, zero-cost, local AI screening system that:
1. Automatically identifies document types (Passport, Aadhaar, PAN, Voter ID, Driving Licence, Vehicle RC, Visa).
2. Extracts certified fields using multi-orientation OCR and ICAO 7-3-1 check digit mathematics.
3. Performs 100-check forensic analysis including Error Level Analysis (ELA) and typography verification.
4. Provides explainable, traceable risk scoring without fabricated default scores.
5. Immutably records every transaction in a SHA-256 hash-chained audit ledger.

## 4. Key Differentiators & Novelty
- **Explainability First**: Every elevated risk point is backed by documented forensic evidence.
- **Fairness & Rescan Handling**: Blurry scans trigger `RESCAN REQUIRED` instead of false fraud accusations.
- **DPDP Act Compliant**: Supports masked Aadhaar by default, zero permanent image storage.
- **Zero Cloud API Lock-in**: Can run completely locally in air-gapped security configurations.

## 5. Technical Feasibility & Roadmap
- Complete backend running FastAPI with ONNX/OpenCV runtime.
- High-performance responsive web dashboard built in Next.js 16 (Turbopack).
- Comprehensive test coverage with 143+ automated regression tests.
