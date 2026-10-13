# Nyaya-Tula AI — Security & Privacy Architecture

## 1. Compliance with India DPDP Act 2023

Nyaya-Tula AI is engineered around the principles of the **Digital Personal Data Protection (DPDP) Act, 2023**:

1. **Data Minimization**:
   - Only identity fields required for border clearance validation are parsed and processed.
   - Masked Aadhaar cards (`XXXX XXXX 1234`) are fully supported by default to prevent raw 12-digit UID exposure.
2. **Zero Permanent Image Storing**:
   - Document images are processed in volatile memory buffers for optical analysis and hashing.
   - Only cryptographic SHA-256 fingerprints are permanently stored in the audit ledger.
3. **Sensitive Identifier Masking**:
   - Log outputs and telemetry never log raw identity numbers or personal biographics.

## 2. Air-Gapped & Local Model Execution

- All primary OCR (RapidOCR/PaddleOCR/Tesseract) and forensic checks run 100% locally on CPU/local GPU.
- No outbound cloud telemetry is required for core screening operation.

## 3. Cryptographic Audit Ledger Integrity

- Records are chained using canonical SHA-256 block hashes (`current_hash = SHA256(prev_hash + payload)`).
- Ensures tamper-evidence across inspection logs.
