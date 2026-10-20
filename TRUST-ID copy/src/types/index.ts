/**
 * TRUST-ID Verification Data Models
 * Matches backend response specification exactly.
 */

export type DocumentType = 
  | 'AUTO_DETECT'
  | 'PAN'
  | 'PAN_CARD'
  | 'AADHAAR'
  | 'PASSPORT'
  | 'INDIAN_PASSPORT'
  | 'VOTER_ID'
  | 'DRIVING_LICENSE'
  | 'NATIONAL_ID' 
  | 'TRAVEL_PERMIT'
  | 'VEHICLE_RC'
  | 'GENERIC_ID'
  | 'UNKNOWN'
  | string;

export type VerificationStatus = 
  | 'PENDING' 
  | 'PROCESSING' 
  | 'COMPLETED' 
  | 'PARTIAL'
  | 'FAILED'
  | 'NEEDS_RESCAN';

export type RiskLevel = 
  | 'LOW' 
  | 'MEDIUM' 
  | 'HIGH' 
  | 'CRITICAL'
  | 'INSUFFICIENT_EVIDENCE'
  | 'NOT_APPLICABLE';

export type DecisionOutcome = 
  | 'APPROVED' 
  | 'REJECTED' 
  | 'MANUAL_REVIEW';

export type CardStatus = 
  | 'pass' 
  | 'fail' 
  | 'match' 
  | 'mismatch' 
  | 'unavailable' 
  | 'inconclusive';

export interface QualityMetrics {
  score: number; // 0.0 - 1.0
  glare: number; // 0.0 - 1.0
  blur: number; // 0.0 - 1.0
  resolution: string;
  illumination: 'OPTIMAL' | 'ADEQUATE' | 'LOW' | 'IRREGULAR';
  status?: CardStatus;
  issues?: string[];
}

export interface PreprocessingInfo {
  normalized: boolean;
  deskew_angle: number; // degrees
  color_space: string;
  resolution_dpi: number;
  pipeline_steps?: string[];
}

export interface OcrResult {
  engine: string;
  confidence: number; // 0.0 - 1.0
  language: string;
  raw_text: string;
  status?: CardStatus;
  mrz?: {
    raw: string;
    parsed: Record<string, string>;
    valid: boolean;
  };
}

export interface FieldMetadata {
  value: string;
  confidence?: number;
  validation_status?: 'VALID' | 'DISCREPANCY' | 'UNVERIFIED' | 'UNAVAILABLE';
}

export interface ExtractedFields {
  document_number: string;
  first_name: string;
  last_name: string;
  full_name: string;
  date_of_birth: string;
  expiry_date: string;
  issue_date?: string;
  gender?: string;
  nationality?: string;
  issuing_country?: string;
  address?: string;
  _metadata?: Record<string, FieldMetadata>;
  [key: string]: any;
}

export interface DocumentValidation {
  valid_format: boolean;
  checksum_passed: boolean;
  expiry_check: 'VALID' | 'EXPIRED' | 'EXPIRING_SOON' | 'INVALID' | 'UNAVAILABLE';
  security_features_verified: boolean;
  status?: CardStatus;
  issues: string[];
}

export interface RecordCheck {
  database_match: boolean;
  registry_name: string;
  query_status: 'VERIFIED' | 'DISCREPANCY' | 'RECORD_NOT_FOUND' | 'SERVICE_UNAVAILABLE' | 'UNAVAILABLE';
  discrepancy_fields: string[];
  status?: CardStatus;
  remarks?: string;
  match_score?: number;
  looked_up_by?: string;
  registry_record?: any;
  conflicts?: Array<{ field?: string; submitted?: string; registered?: string; description?: string }>;
}

export interface IdentityVerification {
  face_match_confidence: number; // 0.0 - 1.0
  match_status: 'MATCH' | 'MISMATCH' | 'INCONCLUSIVE' | 'UNAVAILABLE';
  liveness_score: number; // 0.0 - 1.0
  liveness_status: 'PASSED' | 'FAILED' | 'SUSPECT' | 'UNAVAILABLE';
  status?: CardStatus;
  notes?: string;
}

export interface BoundingBox {
  x: number;      // percentage (0-100) or pixel
  y: number;      // percentage (0-100) or pixel
  width: number;  // percentage (0-100) or pixel
  height: number; // percentage (0-100) or pixel
  label?: string;
  reason?: string;
  severity?: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | 'INFO';
  confidence?: number;
  id?: string;
  x_min?: number;
  x_max?: number;
  y_min?: number;
  y_max?: number;
}

export interface VisualForensics {
  copy_move_detected: boolean;
  font_anomaly: boolean;
  metadata_tampered: boolean;
  ela_score: number; // Error Level Analysis discrepancy 0.0 - 1.0
  edge_inconsistency: boolean;
  status?: CardStatus;
  anomalies: string[];
  regions?: BoundingBox[];
  bounding_boxes?: BoundingBox[];
}

export interface RiskFactorItem {
  factor: string;
  impact?: string; // e.g. "+30"
  score_delta?: number;
  source?: string;
}

export interface RiskAssessment {
  overall_score: number | null; // 0 - 100 or null if unavailable/unsupported
  level: RiskLevel;
  factors: string[];
  factors_breakdown?: RiskFactorItem[];
}

export interface EvidenceArtifact {
  id: string;
  type: 'DOCUMENT_ORIGINAL' | 'FACE_SELFIE' | 'CROPPED_FACE' | 'ELA_HEATMAP' | 'TAMPER_MASK' | 'OCR_BOUNDS';
  title: string;
  uri: string;
  hash_sha256?: string;
  description?: string;
}

export interface EvidenceFlagItem {
  id: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | 'INFO';
  category: string;
  source: string;
  reason: string;
  confidence: number;
  bounding_box?: BoundingBox;
  detail?: string;
}

export interface AuditTrailEntry {
  timestamp: string;
  step: string;
  status: 'SUCCESS' | 'WARNING' | 'FAILED' | 'INFO' | 'UNAVAILABLE';
  detail: string;
}

export interface EvidencePackage {
  artifacts: EvidenceArtifact[];
  audit_trail: AuditTrailEntry[];
  items?: EvidenceFlagItem[];
}

export interface FinalDecision {
  outcome: DecisionOutcome;
  confidence: number; // 0.0 - 1.0
  rationale: string;
  recommended_actions: string[];
  evaluated_at: string;
}

/**
 * Top-level Backend Verification Response structure
 * Standardized across TRUST-ID OCR & Gemini Scanning
 */
export interface VerificationResponse {
  // Section 4 Standard Fields
  case_id: string;
  processing_status?: string;
  document_type: DocumentType;
  document_type_confidence?: number;
  ocr_status?: string;
  all_extracted_text?: string[];
  field_confidence?: Record<string, number>;
  text_regions?: BoundingBox[];
  image_quality?: number;
  validation_results?: any[];
  gemini_status?: string;
  warnings?: string[];
  error_code?: string | null;

  // Detailed subsystem payloads
  status: VerificationStatus;
  quality: QualityMetrics;
  preprocessing: PreprocessingInfo;
  ocr: OcrResult;
  fields: ExtractedFields;
  document_validation: DocumentValidation;
  record_check: RecordCheck;
  identity: IdentityVerification;
  visual_forensics: VisualForensics;
  risk: RiskAssessment;
  evidence: EvidencePackage;
  decision: FinalDecision;
}

export type ScenarioKey = 
  | 'GENUINE' 
  | 'EXPIRED' 
  | 'VISUAL_ANOMALY' 
  | 'FACE_MISMATCH' 
  | 'RECORD_MISMATCH'
  | 'UNAVAILABLE_INCONCLUSIVE'
  | 'PIPELINE_ERROR';

export interface ScenarioPreset {
  id: ScenarioKey;
  label: string;
  document_type: DocumentType;
  outcome: DecisionOutcome;
  description: string;
  data: VerificationResponse;
}

export type AdjudicationAction = 'APPROVE' | 'REJECT' | 'REQUEST_REUPLOAD';

export interface AdjudicationRecord {
  action: AdjudicationAction;
  timestamp: string;
  examinerId: string;
  notes: string;
  signatureHash: string;
}
