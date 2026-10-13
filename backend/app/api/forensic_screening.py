import json
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from backend.app.services.ag_idfse import ag_idfse_engine

router = APIRouter(prefix="/idfse", tags=["Forensic Screening Engine (AG-IDFSE)"])

@router.post(
    "/screen",
    summary="Screen identity/travel document through AG-IDFSE forensic pipeline",
    response_description="Forensic inspection report or REJECTED_UNSUPPORTED_DOCUMENT"
)
async def screen_document_idfse(
    file: Optional[UploadFile] = File(None, description="Front image of identity credential"),
    live_person_file: Optional[UploadFile] = File(None, description="Optional live checkpoint selfie / webcam portrait"),
    document_type_hint: Optional[str] = Form(None, description="PASSPORT, VISA, NATIONAL_ID, or DRIVING_LICENSE"),
    raw_text: Optional[str] = Form(None, description="Optional pre-extracted OCR text string"),
    raw_mrz: Optional[str] = Form(None, description="Optional raw MRZ string (lines separated by newline)"),
    viz_data: Optional[str] = Form(None, description="Optional JSON string of Visual Inspection Zone key-values")
):
    """
    Automated Forensic Inspection Engine for border security, civil identity verification,
    and anti-fraud document auditing (AG-IDFSE).
    
    Validates:
    - Allowed taxonomy: Passports (TD3), Visas (MRVA/MRVB), National ID (TD1/TD2), Driver's License (ISO 18013).
    - Spatial & Geometric Alignment (Border quad, aspect ratio, skew angle, glare).
    - Zonal Scanning (VIZ, MRZ baseline, face & ghost face detection).
    - Pixel Forensics (ELA, edge splicing, typography anomalies, digital stamps).
    - Biometric Matching & Liveness Verification against presented individual.
    - Check digits (7-3-1 weights) and VIZ vs MRZ consistency check.
    - Temporal validity check.
    """
    image_bytes = None
    if file:
        image_bytes = await file.read()

    live_bytes = None
    if live_person_file:
        live_bytes = await live_person_file.read()

    mrz_lines = []
    if raw_mrz:
        mrz_lines = [l.strip() for l in raw_mrz.splitlines() if l.strip()]

    parsed_viz = {}
    if viz_data:
        try:
            parsed_viz = json.loads(viz_data)
        except Exception:
            pass

    result = ag_idfse_engine.screen_document(
        image_input=image_bytes,
        live_person_input=live_bytes,
        raw_text_override=raw_text,
        mrz_override=mrz_lines,
        viz_override=parsed_viz,
        document_type_hint=document_type_hint
    )

    if result.get("status") == "REJECTED_UNSUPPORTED_DOCUMENT":
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "REJECTED_UNSUPPORTED_DOCUMENT"}
        )

    return JSONResponse(status_code=status.HTTP_200_OK, content=result)


@router.post(
    "/validate-mrz",
    summary="Validate ICAO 9303 check-digits for raw MRZ lines",
    response_description="Parsed MRZ and check-digit mathematical verification"
)
async def validate_mrz_endpoint(
    raw_mrz: str = Form(..., description="Raw MRZ string lines separated by newline"),
    doc_type: Optional[str] = Form("PASSPORT")
):
    lines = [l.strip() for l in raw_mrz.splitlines() if l.strip()]
    return ag_idfse_engine.parse_and_validate_mrz(lines, doc_type=doc_type or "PASSPORT")
