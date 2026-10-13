# Nyaya-Tula AI — System Architecture

Nyaya-Tula AI (न्याय-तुला: "Scales of Justice") is an AI-powered document screening, tampering detection, and border clearance decision support system developed for the Smart India Hackathon (SIH) 2026.

## 1. High-Level Architecture

```mermaid
flowchart TD
    A[Document Upload] --> B[Image Preprocessing & Multi-Orientation Check]
    B --> C[Document Classification Engine]
    C -->|Supported Document| D[OCR & Field Extraction]
    C -->|Unreadable / Low Contrast| CR[NEEDS_RESCAN]
    C -->|Unsupported Format| CU[UNSUPPORTED]
    D --> E[Document-Specific Validation]
    E --> F[Forensic Tampering Analysis]
    D --> G[Facial Biometric Comparison]
    E --> H[Explainable Risk Scoring Engine]
    F --> H
    G --> H
    CR --> H
    CU --> H
    H --> I[Border Clearance Decision Dashboard]
    I --> J[Screening Report Export CSV / PDF / Excel]
    I --> K[Hash-Linked Audit Ledger SHA-256]
```

## 2. Core Architectural Principles

1. **Document-Specific Extraction & Validation**:
   - Pan cards use Income Tax alphanumeric rules (`[A-Z]{5}[0-9]{4}[A-Z]`).
   - Aadhaar cards support both 12-digit standard and masked formats (`XXXX XXXX 1234`).
   - Passports parse ICAO Doc 9303 TD3 2-line MRZ and evaluate 7-3-1 repeating check digits.
   - Voter ID uses Election Commission EPIC syntax; Driving Licences use SARATHI/Parivahan structures.
   - No cross-pollution: PAN cards are never evaluated against passport MRZ rules.

2. **Strict Separation of OCR and External Verification**:
   - Successful local OCR extraction results in `ocr_status: "COMPLETED"`.
   - External official database lookups (e.g., NSDL, UIDAI) remain `external_verification_status: "NOT_VERIFIED"` unless an authorized live integration is configured.
   - An unconfigured external API never triggers a fraud risk finding.

3. **Ground-Truth Risk Evaluation**:
   - If document classification fails or an image is blurred, `risk_score` is set to `null` (displayed as `N/A`), preventing misleading arbitrary fraud scores.
   - High risk is generated exclusively from verifiable forensic discrepancies (checksum mismatches, ELA compression anomalies, blacklists).

4. **Cryptographic Tamper-Evident Ledger**:
   - Each scan transaction is hashed using canonical SHA-256 and chained to predecessor blocks, creating an immutable audit trail without external blockchain overhead.
