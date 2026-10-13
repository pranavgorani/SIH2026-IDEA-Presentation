# Nyaya-Tula AI — SIH 2026 Pitch Deck Outline (10 Slides)

## Slide 1: Title & Vision
- **Title**: Nyaya-Tula AI (न्याय-तुला AI)
- **Tagline**: Automated Forensic Document Screening, Tampering Detection & Clearance Support
- **Category**: Smart India Hackathon (SIH) 2026 — Homeland Security & Border Management

## Slide 2: Problem Statement & Real-World Pain Points
- Rapid passenger throughput vs. meticulous forensic scrutiny.
- High false-positive rates on valid national credentials (PAN, Aadhaar).
- Opaque legacy OCR engines with no explainability or evidence tracking.

## Slide 3: Proposed Solution
- Full-stack, zero-cost, local AI identity screening architecture.
- Multi-tier document classifier supporting all advertised Indian & international credentials.
- 100-check inspection matrix combining layout geometry, check digits, and forensics.

## Slide 4: Core Innovations & Technical Differentiators
- **Fairness Guarantee**: Blurry scans trigger `RESCAN REQUIRED` with `N/A` risk score, eliminating false fraud accusations.
- **ICAO Doc 9303 Math**: Native 7-3-1 check digit computation.
- **Status Clarity**: Strict architectural separation between OCR extraction and external verification.

## Slide 5: Live Demonstration Workflow
- 5-step interactive workflow: Upload → Multi-orientation OCR → Forensic Tampering → Explainable Risk Scoring → Cryptographic Ledger.

## Slide 6: Technical Architecture & Pipeline
- FastAPI backend + ONNX/OpenCV runtime + Next.js 16 frontend.
- Sub-500ms local CPU processing latency.

## Slide 7: AI Modules & Multi-Signal Validation
- Module 1: Preprocessing & Multi-Orientation OCR.
- Module 2: Document-Specific Syntax & ICAO Checksum Verification.
- Module 3: Error Level Analysis (ELA) & Typography Forensics.
- Module 4: Explainable Multi-Factor Risk Engine.

## Slide 8: Empirical Benchmarks & Testing Rigor
- 143+ automated regression tests passing across backend and API contracts.
- 100% clean production TypeScript build on Next.js 16.
- Standardized benchmarks adhering to `metrics_schema.json`.

## Slide 9: Privacy, DPDP Act 2023 & Security
- Native masked Aadhaar handling (`XXXX XXXX 1234`).
- Zero permanent document image storage; canonical SHA-256 ledger chaining.
- Air-gapped offline operation support.

## Slide 10: Roadmap, Feasibility & Impact
- Phase 1: Airport e-gate and border checkpoint pilot.
- Phase 2: Integration with state police & transport RTO checkpoints.
- Conclusion: Restoring trust, fairness, and speed to civil and border verification.
