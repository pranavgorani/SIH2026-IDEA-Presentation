import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean, DateTime,
    ForeignKey, JSON, Index, create_engine
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from backend.app.core.config import settings

Base = declarative_base()

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

# 1. Users
class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(150), nullable=True)
    role = Column(String(50), nullable=False, default="VERIFIER") # ADMIN, VERIFIER, INVESTIGATOR
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

# 2. Cases
class Case(Base):
    __tablename__ = "cases"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    case_number = Column(String(50), unique=True, nullable=False, index=True)
    document_type = Column(String(50), nullable=False, default="UNKNOWN") # PASSPORT, VISA, NATIONAL_ID, DRIVING_LICENSE, PERMIT, TRAVEL_AUTHORIZATION
    status = Column(String(50), nullable=False, default="UPLOADED", index=True) 
    # UPLOADED, PROCESSING, OCR_COMPLETE, FORENSICS_COMPLETE, VALIDATION_COMPLETE, IDENTITY_COMPLETE, RISK_COMPLETE, REVIEW_REQUIRED, COMPLETED, REJECTED
    risk_level = Column(String(20), nullable=False, default="PENDING", index=True) # LOW, MEDIUM, HIGH, PENDING
    risk_score = Column(Float, nullable=False, default=0.0)
    confidence = Column(Float, nullable=False, default=0.0)
    requires_human_review = Column(Boolean, default=False)
    assigned_reviewer_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, index=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    documents = relationship("Document", back_populates="case", cascade="all, delete-orphan")
    ocr_result = relationship("OCRResult", back_populates="case", uselist=False, cascade="all, delete-orphan")
    validation_results = relationship("ValidationResult", back_populates="case", cascade="all, delete-orphan")
    tamper_result = relationship("TamperResult", back_populates="case", uselist=False, cascade="all, delete-orphan")
    face_verification = relationship("FaceVerificationResult", back_populates="case", uselist=False, cascade="all, delete-orphan")
    record_verification = relationship("RecordVerificationResult", back_populates="case", uselist=False, cascade="all, delete-orphan")
    risk_assessment = relationship("RiskAssessment", back_populates="case", uselist=False, cascade="all, delete-orphan")
    review_decision = relationship("ReviewDecision", back_populates="case", uselist=False, cascade="all, delete-orphan")
    audit_events = relationship("AuditEvent", back_populates="case", cascade="all, delete-orphan")
    document_checks = relationship("DocumentCheck", back_populates="case", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="case", cascade="all, delete-orphan")
    investigation_notes = relationship("InvestigationNote", back_populates="case", cascade="all, delete-orphan")

# 3. Documents
class Document(Base):
    __tablename__ = "documents"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    case_id = Column(String(36), ForeignKey("cases.id"), nullable=False, index=True)
    side = Column(String(20), nullable=False, default="FRONT") # FRONT, BACK, LIVE_PERSON
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    sha256_hash = Column(String(64), nullable=False)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    quality_score = Column(Float, nullable=True)
    quality_issues = Column(JSON, nullable=True) # list of strings
    created_at = Column(DateTime, default=utc_now)

    case = relationship("Case", back_populates="documents")

# 4. OCR Results
class OCRResult(Base):
    __tablename__ = "ocr_results"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    case_id = Column(String(36), ForeignKey("cases.id"), nullable=False, index=True)
    raw_text = Column(Text, nullable=False)
    extracted_fields = Column(JSON, nullable=False) # {name, document_number, nationality, date_of_birth, ...}
    mrz_data = Column(JSON, nullable=True) # {passport_number, country_code, surname, checksum_valid, ...}
    confidence = Column(Float, nullable=False, default=0.0)
    bounding_boxes = Column(JSON, nullable=True) # list of {text, box, confidence}
    engine_used = Column(String(50), default="OCRService_Modular")
    created_at = Column(DateTime, default=utc_now)

    case = relationship("Case", back_populates="ocr_result")

# 5. Validation Results
class ValidationResult(Base):
    __tablename__ = "validation_results"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    case_id = Column(String(36), ForeignKey("cases.id"), nullable=False, index=True)
    check_name = Column(String(100), nullable=False) # "Expiry Check", "MRZ Checksum", etc.
    status = Column(String(20), nullable=False) # PASS, FAIL, WARNING, UNAVAILABLE
    severity = Column(String(20), nullable=False, default="MEDIUM") # LOW, MEDIUM, HIGH, CRITICAL
    message = Column(Text, nullable=False)
    evidence = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    case = relationship("Case", back_populates="validation_results")

# 6. Tamper / Visual Forensics Results
class TamperResult(Base):
    __tablename__ = "tamper_results"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    case_id = Column(String(36), ForeignKey("cases.id"), nullable=False, index=True)
    tampering_detected = Column(Boolean, nullable=False, default=False)
    confidence = Column(Float, nullable=False, default=0.0)
    regions = Column(JSON, nullable=False, default=list) # [{x, y, width, height, type, confidence, explanation}]
    signals = Column(JSON, nullable=False, default=dict) # {ela_score, edge_inconsistency, noise_variance, ...}
    heatmap_path = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=utc_now)

    case = relationship("Case", back_populates="tamper_result")

# 7. Face Verification Results
class FaceVerificationResult(Base):
    __tablename__ = "face_verification_results"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    case_id = Column(String(36), ForeignKey("cases.id"), nullable=False, index=True)
    document_face_detected = Column(Boolean, default=False)
    live_face_detected = Column(Boolean, default=False)
    document_face_box = Column(JSON, nullable=True)
    live_face_box = Column(JSON, nullable=True)
    document_face_quality = Column(Float, default=0.0)
    live_face_quality = Column(Float, default=0.0)
    similarity = Column(Float, default=0.0) # 0.0 - 1.0
    status = Column(String(50), default="UNAVAILABLE") # MATCH_CONFIRMED, MATCH_REVIEW, MISMATCH_DETECTED, UNAVAILABLE
    explanation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    case = relationship("Case", back_populates="face_verification")

# 8. Record Verification Results (Simulated Database/API Adapter)
class RecordVerificationResult(Base):
    __tablename__ = "record_verification_results"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    case_id = Column(String(36), ForeignKey("cases.id"), nullable=False, index=True)
    record_found = Column(Boolean, default=False)
    status = Column(String(50), default="VALID") # VALID, SUSPENDED, REVOKED, NOT_FOUND, UNAVAILABLE
    document_number = Column(String(100), nullable=True, index=True)
    source = Column(String(100), default="DEMO_VERIFICATION_DATABASE")
    match_details = Column(JSON, nullable=True) # {name_match, dob_match, expiry_match}
    checked_at = Column(DateTime, default=utc_now)

    case = relationship("Case", back_populates="record_verification")

# 9. Risk Assessments & Explainability
class RiskAssessment(Base):
    __tablename__ = "risk_assessments"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    case_id = Column(String(36), ForeignKey("cases.id"), nullable=False, index=True)
    risk_score = Column(Float, nullable=False, default=0.0) # 0 to 100
    risk_level = Column(String(20), nullable=False, default="LOW") # LOW, MEDIUM, HIGH
    confidence = Column(Float, nullable=False, default=0.0)
    recommended_action = Column(String(100), nullable=False)
    signal_scores = Column(JSON, nullable=False, default=dict) # breakdown per signal
    risk_factors = Column(JSON, nullable=False, default=list) # negative indicators
    positive_signals = Column(JSON, nullable=False, default=list) # passed verifications
    explanation = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now)

    case = relationship("Case", back_populates="risk_assessment")

# 10. Review Decisions (Human-In-The-Loop)
class ReviewDecision(Base):
    __tablename__ = "review_decisions"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    case_id = Column(String(36), ForeignKey("cases.id"), nullable=False, index=True)
    reviewer_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    reviewer_name = Column(String(150), nullable=False)
    decision = Column(String(50), nullable=False) # APPROVE_AFTER_REVIEW, REQUEST_REUPLOAD, ESCALATE, MARK_FOR_INVESTIGATION
    reason = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=utc_now)

    case = relationship("Case", back_populates="review_decision")

# 11. Audit Events (Tamper-Evident SHA-256 Hash Chain)
class AuditEvent(Base):
    __tablename__ = "audit_events"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    case_id = Column(String(36), ForeignKey("cases.id"), nullable=False, index=True)
    actor_id = Column(String(100), nullable=False)
    action = Column(String(100), nullable=False)
    details = Column(JSON, nullable=True)
    previous_hash = Column(String(64), nullable=False)
    event_hash = Column(String(64), nullable=False, index=True)
    sequence_number = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=utc_now, index=True)

    case = relationship("Case", back_populates="audit_events")

# 12. System Settings
class SystemSetting(Base):
    __tablename__ = "system_settings"
    key = Column(String(100), primary_key=True)
    value = Column(JSON, nullable=False)
    description = Column(String(255), nullable=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

# 13. Document Checks (100-Point Inspection Engine)
class DocumentCheck(Base):
    __tablename__ = "document_checks"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    case_id = Column(String(36), ForeignKey("cases.id"), nullable=False, index=True)
    check_id = Column(String(20), nullable=False, index=True) # CHK-001 ... CHK-100
    category = Column(String(50), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(30), nullable=False) # PASS, FAIL, WARNING, NOT_CHECKED, NOT_APPLICABLE, UNAVAILABLE
    severity = Column(String(20), nullable=False, default="INFO") # INFO, LOW, MEDIUM, HIGH, CRITICAL
    confidence = Column(Float, nullable=False, default=1.0)
    evidence = Column(Text, nullable=True)
    value = Column(String(255), nullable=True)
    expected_value = Column(String(255), nullable=True)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now)

    case = relationship("Case", back_populates="document_checks")

# 14. Analysis Reports (PDF, CSV, DOCX exports)
class Report(Base):
    __tablename__ = "reports"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    case_id = Column(String(36), ForeignKey("cases.id"), nullable=False, index=True)
    report_hash = Column(String(64), nullable=False, index=True)
    pdf_path = Column(String(512), nullable=True)
    csv_path = Column(String(512), nullable=True)
    docx_path = Column(String(512), nullable=True)
    integrity_score = Column(Float, nullable=False, default=100.0)
    risk_score = Column(Float, nullable=False, default=0.0)
    total_checks = Column(Integer, default=100)
    passed_checks = Column(Integer, default=0)
    failed_checks = Column(Integer, default=0)
    warning_checks = Column(Integer, default=0)
    unavailable_checks = Column(Integer, default=0)
    not_applicable_checks = Column(Integer, default=0)
    created_at = Column(DateTime, default=utc_now, index=True)

    case = relationship("Case", back_populates="reports")

# 15. Investigation Notes (Inspectors / Verifiers)
class InvestigationNote(Base):
    __tablename__ = "investigation_notes"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    case_id = Column(String(36), ForeignKey("cases.id"), nullable=False, index=True)
    author_id = Column(String(36), nullable=False)
    author_name = Column(String(150), nullable=False)
    author_role = Column(String(50), nullable=False, default="INSPECTOR")
    note = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now, index=True)

    case = relationship("Case", back_populates="investigation_notes")

# Database Engine & Session
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
