# Nyaya-Tula AI — API Reference

## Endpoints Overview

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/screen` | POST | Unified document upload and forensic screening |
| `/api/forensic/screen` | POST | AG-IDFSE specialized forensic screening engine |
| `/api/cases` | GET | Retrieve paginated inspection cases |
| `/api/reports/export/csv` | GET | Export audit ledger in CSV format |
| `/api/reports/export/pdf` | GET | Generate official Ministry of Home Affairs dossier PDF |
| `/api/reports/export/docx`| GET | Generate inspection summary DOCX |
| `/api/reports/export/zip` | GET | Bundle all screening reports into cryptographic ZIP |

## Unified Screening Request Contract

**URL**: `POST /screen`  
**Content-Type**: `multipart/form-data`

### Form Fields
- `primary_document` (File, Required): Image (PNG, JPG, JPEG) or PDF of credential.
- `document_type_hint` (String, Optional): `"AUTO_DETECT"`, `"PASSPORT"`, `"PAN"`, `"AADHAAR"`, etc.

### Response Schema

```json
{
  "case_id": "CASE-1728860000",
  "case_number": "CASE-20261014-SCAN01",
  "processing_status": "COMPLETED",
  "document_type": "PAN",
  "document_type_confidence": 0.98,
  "ocr_status": "COMPLETED",
  "fields": {
    "document_number": "ABCDE1234F",
    "holder_name": "RAHUL KUMAR SHARMA",
    "date_of_birth": "1990-08-15"
  },
  "validation_status": "VALID",
  "external_verification_status": "NOT_VERIFIED",
  "external_verification_provider": "TRUST_ID_GATEWAY (NOT_CONFIGURED)",
  "risk_score": 12.0,
  "risk_factors": [],
  "final_decision": "CLEAR_TO_ENTER",
  "warnings": [],
  "error_code": null
}
```

### Response Status Definitions
- `COMPLETED`: Document classified and all expected fields extracted.
- `PARTIAL`: Document recognized, but one or more optional fields unreadable.
- `NEEDS_RESCAN`: Insufficient sharpness or lighting; rescan required.
- `UNSUPPORTED`: Non-credential or unadvertised format. `risk_score` is `null`.
- `PROCESSING_FAILED`: Technical ingestion exception. `risk_score` is `null`.
