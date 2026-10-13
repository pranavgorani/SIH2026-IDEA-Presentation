# 5-Minute Evaluator Demo Script for SIH 2026

## Objective
Demonstrate the end-to-end Nyaya-Tula AI forensic screening system in a crisp, technically grounded 5-minute walk-through.

---

### [0:00 - 0:30] Problem & Mission
- **Presenter**: "Good morning, evaluators. Border security personnel have seconds to verify complex credentials. Conventional systems either fail silently on non-standard cards or falsely accuse legitimate travelers due to poor scan quality. Nyaya-Tula AI delivers explainable, multi-tier forensic inspection with zero fabricated risk scores."

### [0:30 - 1:15] Document Upload & Multi-Tier Classification
- **Action**: Open the dashboard (`http://localhost:3000/screen`). Upload a sample Indian PAN card.
- **Key Observation**: Point out the top banner: `✓ DOCUMENT ANALYZED & RECOGNIZED` and `EXTERNAL VERIFICATION: NOT CONFIGURED (NOT VERIFIED)`.
- **Key Point**: "Notice that successful OCR is cleanly separated from official government database verification. We never display misleading 'DOCUMENT NOT VERIFIED' warnings when recognition has succeeded."

### [1:15 - 2:00] OCR & Check Digit Validation
- **Action**: Switch to Diplomatic Passport scenario or upload a passport scan.
- **Key Observation**: Show the **ICAO Doc 9303 7-3-1 Repeating Weights Check Digit Table**.
- **Key Point**: "Every check digit—document number, date of birth, expiry, composite—is calculated mathematically and compared with the visual zone."

### [2:00 - 2:45] Forensic Tampering & ELA Analysis
- **Action**: Click on **Module 3: Tampering AI**.
- **Key Observation**: Show the localized Error Level Analysis (ELA) compression heatmap and edge gradient analysis.
- **Key Point**: "Our ELA engine flags high-frequency compression discontinuities around the portrait substrate without claiming unproven certainty."

### [2:45 - 3:30] Fair Risk Assessment & Blurry Scan Handling
- **Action**: Upload an ambiguous/blurry sample or non-credential receipt.
- **Key Observation**: Point to the Circular Gauge showing **`N/A`** with `RESCAN REQUIRED` banner.
- **Key Point**: "When a scan is unreadable, our risk engine sets the score to null (`N/A`) and offers a one-click Rescan, rather than generating an artificial 35.0 fraud risk score."

### [3:30 - 4:15] Cryptographic Audit Ledger
- **Action**: Scroll to the Cryptographic Block Hash section.
- **Key Observation**: Show the SHA-256 fingerprint, predecessor block hash, and digital signature.
- **Key Point**: "Every transaction is immutably linked in a hash-chained ledger for legal chain-of-custody compliance under the DPDP Act 2023."

### [4:15 - 5:00] Report Export & Q&A
- **Action**: Click **Download Screening Report** (exports CSV/Excel) and show the print dossier view.
- **Key Point**: "Nyaya-Tula AI is ready for air-gapped checkpoint deployment with zero cloud dependencies. Thank you."
