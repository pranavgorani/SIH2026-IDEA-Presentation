from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# Auth Schemas
class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: Optional[str] = None
    role: str
    is_active: bool

# Image Quality
class ImageQualityResult(BaseModel):
    quality_score: float
    issues: List[str]
    is_acceptable: bool
    recommendation: Optional[str] = None

# Document Schemas
class DocumentResponse(BaseModel):
    id: str
    case_id: str
    side: str
    filename: str
    file_path: str
    file_size_bytes: int
    mime_type: str
    sha256_hash: str
    width: Optional[int] = None
    height: Optional[int] = None
    quality_score: Optional[float] = None
    quality_issues: Optional[List[str]] = None
    created_at: datetime

# OCR & MRZ
class ExtractedFields(BaseModel):
    name: Optional[str] = ""
    document_number: Optional[str] = ""
    nationality: Optional[str] = ""
    date_of_birth: Optional[str] = ""
    date_of_issue: Optional[str] = ""
    date_of_expiry: Optional[str] = ""
    gender: Optional[str] = ""
    issuing_country: Optional[str] = ""

class MRZData(BaseModel):
    valid: bool
    raw_mrz: Optional[List[str]] = []
    document_type: Optional[str] = None
    country_code: Optional[str] = None
    surname: Optional[str] = None
    given_names: Optional[str] = None
    passport_number: Optional[str] = None
    nationality: Optional[str] = None
    date_of_birth: Optional[str] = None
    sex: Optional[str] = None
    expiry_date: Optional[str] = None
    personal_number: Optional[str] = None
    checksum_overall: bool = True
    checksum_passport_number: bool = True
    checksum_dob: bool = True
    checksum_expiry: bool = True

class BoundingBox(BaseModel):
    text: str
    x: int
    y: int
    width: int
    height: int
    confidence: float

class OCRResultResponse(BaseModel):
    raw_text: str
    fields: ExtractedFields
    mrz: Optional[MRZData] = None
    confidence: float
    bounding_boxes: List[BoundingBox] = []
    engine_used: str

# Validation
class ValidationCheck(BaseModel):
    name: str
    status: str # PASS, FAIL, WARNING, UNAVAILABLE
    severity: str # LOW, MEDIUM, HIGH, CRITICAL
    message: str
    evidence: Optional[Dict[str, Any]] = None

class ValidationSummary(BaseModel):
    valid: bool
    passed_count: int
    failed_count: int
    warning_count: int
    checks: List[ValidationCheck]

# Visual Forensics / Tampering
class TamperRegion(BaseModel):
    x: int
    y: int
    width: int
    height: int
    type: str
    confidence: float
    explanation: str

class TamperResultResponse(BaseModel):
    tampering_detected: bool
    confidence: float
    regions: List[TamperRegion] = []
    signals: Dict[str, Any] = {}
    heatmap_url: Optional[str] = None
    evidence: List[str] = []

# Face Verification
class FaceVerificationResponse(BaseModel):
    document_face_detected: bool
    live_face_detected: bool
    document_face_quality: float
    live_face_quality: float
    similarity: float
    status: str # MATCH_CONFIRMED, MATCH_REVIEW, MISMATCH_DETECTED, UNAVAILABLE
    explanation: str

# Record Verification (Simulated)
class RecordVerificationResponse(BaseModel):
    record_found: bool
    status: str # VALID, SUSPENDED, REVOKED, NOT_FOUND, UNAVAILABLE
    document_number: Optional[str] = None
    source: str = "DEMO_VERIFICATION_DATABASE (SIMULATED)"
    match_details: Optional[Dict[str, Any]] = None
    checked_at: datetime
    disclaimer: str = "SIMULATED / DEMONSTRATION DATA"

# Multi-Signal Risk Assessment
class RiskAssessmentResponse(BaseModel):
    risk_score: float
    risk_level: str # LOW, MEDIUM, HIGH
    confidence: float
    recommended_action: str
    signal_scores: Dict[str, float]
    risk_factors: List[str]
    positive_signals: List[str]
    explanation: str
    weights_used: Optional[Dict[str, float]] = None

# Human Review Decision
class ReviewDecisionRequest(BaseModel):
    decision: str # APPROVE_AFTER_REVIEW, REQUEST_REUPLOAD, ESCALATE, MARK_FOR_INVESTIGATION
    reason: str

class ReviewDecisionResponse(BaseModel):
    id: str
    case_id: str
    reviewer_id: str
    reviewer_name: str
    decision: str
    reason: str
    timestamp: datetime

# Audit Event
class AuditEventResponse(BaseModel):
    id: str
    case_id: str
    actor_id: str
    action: str
    details: Optional[Dict[str, Any]] = None
    previous_hash: str
    event_hash: str
    sequence_number: int
    timestamp: datetime

class AuditIntegrityResponse(BaseModel):
    status: str # VERIFIED, COMPROMISED
    total_events: int
    is_valid: bool
    verified_at: datetime
    last_block_hash: str

# Cases
class CaseCreate(BaseModel):
    document_type: Optional[str] = "UNKNOWN"
    notes: Optional[str] = None

class CaseResponse(BaseModel):
    id: str
    case_number: str
    document_type: str
    status: str
    risk_level: str
    risk_score: float
    confidence: float
    requires_human_review: bool
    assigned_reviewer_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class CaseDetailResponse(CaseResponse):
    documents: List[DocumentResponse] = []
    ocr_result: Optional[OCRResultResponse] = None
    validation_summary: Optional[ValidationSummary] = None
    tamper_result: Optional[TamperResultResponse] = None
    face_verification: Optional[FaceVerificationResponse] = None
    record_verification: Optional[RecordVerificationResponse] = None
    risk_assessment: Optional[RiskAssessmentResponse] = None
    review_decision: Optional[ReviewDecisionResponse] = None
    audit_events: List[AuditEventResponse] = []

# Analytics / Dashboard
class DashboardStatsResponse(BaseModel):
    total_screened: int
    requiring_review: int
    high_risk_cases: int
    medium_risk_cases: int
    low_risk_cases: int
    tampering_detected_count: int
    face_mismatch_alerts: int
    expired_documents_count: int
    avg_processing_time_sec: float
    average_risk_score: float
    risk_distribution: List[Dict[str, Any]]
    document_types: List[Dict[str, Any]]
    detection_categories: List[Dict[str, Any]]
    screening_volume_trend: List[Dict[str, Any]]

# Admin Settings
class SystemSettingsModel(BaseModel):
    weights: Dict[str, float]
    threshold_low: float
    threshold_medium: float
    ai_provider: str
    verification_mode: str
