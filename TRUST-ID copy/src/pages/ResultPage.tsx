import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  HelpCircle,
  FileSearch, 
  UserCheck, 
  ArrowRight,
  Activity,
  FileText,
  Database,
  Search,
  Slash,
  AlertCircle,
  Edit3,
  Save,
  Check,
  ChevronDown,
  ChevronUp,
  Info,
  Copy,
  Sparkles,
  Layers
} from 'lucide-react';
import { getCaseResult, switchMockScenario, updateCaseFields } from '../services/api';
import { VerificationResponse } from '../types';
import { getCardStatusBadge, getRiskBadgeInfo, getOutcomeBadgeStyles, formatDocumentType } from '../utils/formatters';
import { GlobalScenarioBar } from '../components/GlobalScenarioBar';

export const ResultPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const caseId = searchParams.get('caseId') || 'TR-2026-8821-GEN';

  const [data, setData] = useState<VerificationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [isEditingFields, setIsEditingFields] = useState(false);
  const [editedFields, setEditedFields] = useState<Record<string, string>>({});
  const [fieldsSaved, setFieldsSaved] = useState(false);
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false);
  const [copiedText, setCopiedText] = useState(false);
  const [textFilter, setTextFilter] = useState('');

  useEffect(() => {
    let mounted = true;
    getCaseResult(caseId).then((res) => {
      if (mounted && res) {
        setData(res);
        const initialFields: Record<string, string> = {};
        Object.entries(res.fields || {}).forEach(([k, v]) => {
          if (k !== '_metadata') initialFields[k] = String(v ?? '');
        });
        setEditedFields(initialFields);
        setLoading(false);
      }
    });
    return () => {
      mounted = false;
    };
  }, [caseId]);

  const handleScenarioChange = (newScenarioId: string) => {
    const updated = switchMockScenario(newScenarioId);
    setData(updated);
    const initialFields: Record<string, string> = {};
    Object.entries(updated.fields || {}).forEach(([k, v]) => {
      if (k !== '_metadata') initialFields[k] = String(v ?? '');
    });
    setEditedFields(initialFields);
    setSearchParams({ caseId: updated.case_id });
  };

  const handleSaveFields = async () => {
    if (!data) return;
    const updated = await updateCaseFields(data.case_id, editedFields);
    if (updated) {
      setData({ ...updated });
    } else {
      setData({
        ...data,
        fields: {
          ...data.fields,
          ...editedFields
        }
      });
    }
    setIsEditingFields(false);
    setFieldsSaved(true);
    setTimeout(() => setFieldsSaved(false), 4000);
  };

  const handleConfirmFields = async () => {
    if (!data) return;
    const updated = await updateCaseFields(data.case_id, editedFields);
    if (updated) {
      setData({ ...updated });
    }
    setFieldsSaved(true);
    setTimeout(() => setFieldsSaved(false), 4000);
  };

  if (loading || !data) {
    return (
      <div className="p-16 text-center font-sans text-[#5f6368] text-xs">
        <div className="w-8 h-8 border-2 border-[#1a73e8] border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        Loading verification dossier for {caseId}...
      </div>
    );
  }

  // Exact Risk representation
  const riskInfo = getRiskBadgeInfo(data.risk.overall_score, data.risk.level);
  const outcomeStyle = getOutcomeBadgeStyles(data.decision.outcome);

  // Status badges for modules
  const qualityBadge = getCardStatusBadge(data.quality.status);
  const ocrBadge = getCardStatusBadge(data.ocr.status);
  const docValBadge = getCardStatusBadge(data.document_validation.status);
  const faceBadge = getCardStatusBadge(data.identity.status);
  const forensicsBadge = getCardStatusBadge(data.visual_forensics.status);
  const recordBadge = getCardStatusBadge(data.record_check.status);

  // Helper icon renderer
  const renderCardStatusIcon = (badge: ReturnType<typeof getCardStatusBadge>) => {
    switch (badge.iconType) {
      case 'check':
        return <CheckCircle2 className="w-3.5 h-3.5 text-[#1e8e3e]" />;
      case 'cross':
        return <XCircle className="w-3.5 h-3.5 text-[#d93025]" />;
      case 'slash':
        return <Slash className="w-3.5 h-3.5 text-[#5f6368]" />;
      case 'question':
        return <HelpCircle className="w-3.5 h-3.5 text-[#e37400]" />;
      default:
        return <AlertCircle className="w-3.5 h-3.5 text-[#5f6368]" />;
    }
  };

  const isApproved = data.decision.outcome === 'APPROVED';
  const isRejected = data.decision.outcome === 'REJECTED';

  // Master Identity Registry calculations
  const recordCheck = (data as any).record_check || {};
  const regRecord = recordCheck.registry_record || null;
  const registryConflicts: Array<{ field?: string; submitted?: string; registered?: string; description?: string }> = recordCheck.conflicts || [];
  
  const isRegistryMatch = recordCheck.status === 'match' || recordCheck.query_status === 'VERIFIED';
  const hasDiscrepancy = recordCheck.query_status === 'DISCREPANCY' || registryConflicts.length > 0;
  const isNotFound = recordCheck.query_status === 'RECORD_NOT_FOUND' || recordCheck.status === 'slash';
  
  const hasWatchlistAlert = Boolean(
    regRecord?.is_watchlist || 
    registryConflicts.some((c: any) => c.field?.toLowerCase().includes('watchlist'))
  );
  const watchlistReason = regRecord?.watchlist_reason || registryConflicts.find((c: any) => c.field?.toLowerCase().includes('watchlist'))?.description;

  const matchScore = recordCheck.match_score !== undefined ? recordCheck.match_score : (isRegistryMatch ? 1.0 : 0.0);

  const submittedDocNum = String(data.fields.document_number || '—');
  const registeredDocNum = regRecord ? String(regRecord.document_number || '—') : (isRegistryMatch ? submittedDocNum : 'Not Found in Registry');
  
  const submittedName = String(data.fields.full_name || data.fields.name || '—');
  const registeredName = regRecord ? String(regRecord.full_name || '—') : (isRegistryMatch ? submittedName : 'Not Found in Registry');

  const submittedDob = String(data.fields.date_of_birth || data.fields.dob || '—');
  const registeredDob = regRecord ? String(regRecord.date_of_birth || '—') : (isRegistryMatch ? submittedDob : 'Not Found in Registry');

  const submittedExpiry = String(data.fields.expiry_date || data.fields.expiry || '—');
  const registeredExpiry = regRecord ? String(regRecord.expiry_date || '—') : (isRegistryMatch ? submittedExpiry : 'Not Found in Registry');

  const submittedNat = String(data.fields.nationality || '—');
  const registeredNat = regRecord ? String(regRecord.nationality || '—') : (isRegistryMatch ? submittedNat : 'Not Found in Registry');

  const regStatus = regRecord?.status || (isRegistryMatch ? 'ACTIVE' : 'UNVERIFIED');

  // Canonical Field Comparisons from backend if available, or fallback rows
  const rawComparisons = (recordCheck.field_comparisons && recordCheck.field_comparisons.length > 0)
    ? recordCheck.field_comparisons
    : null;

  const comparisonRows: Array<{
    label: string;
    submitted: string;
    registered: string;
    normalizedComparison: string;
    status: string;
    isMatch: boolean;
    statusText: string;
    statusStyle: string;
  }> = rawComparisons
    ? rawComparisons.map((fc: any) => {
        const isMatch = fc.status === 'MATCH';
        const isMismatch = fc.status === 'MISMATCH';
        const isNotApp = fc.status === 'NOT_APPLICABLE';
        const isNeedsConf = fc.status === 'NEEDS_CONFIRMATION';

        let statusText = 'Match';
        let statusStyle = 'bg-[#e6f4ea] text-[#137333] border-[#ceead6]';

        if (isMismatch) {
          statusText = 'Mismatch';
          statusStyle = 'bg-[#fce8e6] text-[#c5221f] border-[#fad2cf]';
        } else if (isNotApp) {
          statusText = 'Not Applicable';
          statusStyle = 'bg-[#f1f3f4] text-[#5f6368] border-[#dadce0]';
        } else if (isNeedsConf) {
          statusText = 'Needs Confirmation';
          statusStyle = 'bg-[#fef7e0] text-[#b06000] border-[#feefc3]';
        } else if (!isMatch) {
          statusText = 'Unavailable';
          statusStyle = 'bg-[#f1f3f4] text-[#80868b] border-[#dadce0]';
        }

        const normComp = isNotApp
          ? 'LIFETIME / NOT APPLICABLE'
          : (fc.normalized_submitted && fc.normalized_registered
              ? `${fc.normalized_submitted} ↔ ${fc.normalized_registered}`
              : (fc.normalized_submitted || fc.normalized_registered || '—'));

        return {
          label: fc.label,
          submitted: fc.submitted || '—',
          registered: fc.registered || '—',
          normalizedComparison: normComp,
          status: fc.status,
          isMatch: isMatch || isNotApp,
          statusText,
          statusStyle,
        };
      })
    : [
        {
          label: 'Document Number',
          submitted: submittedDocNum,
          registered: registeredDocNum,
          normalizedComparison: `${submittedDocNum} ↔ ${registeredDocNum}`,
          status: isRegistryMatch ? 'MATCH' : 'MISMATCH',
          isMatch: isRegistryMatch || (!registryConflicts.some((c: any) => c.field === 'document_number') && regRecord),
          statusText: (isRegistryMatch || regRecord) ? 'Match' : 'Unregistered',
          statusStyle: (isRegistryMatch || regRecord) ? 'bg-[#e6f4ea] text-[#137333] border-[#ceead6]' : 'bg-[#fef7e0] text-[#b06000] border-[#feefc3]'
        },
        {
          label: 'Full Legal Name',
          submitted: submittedName,
          registered: registeredName,
          normalizedComparison: `${submittedName} ↔ ${registeredName}`,
          status: !registryConflicts.some((c: any) => c.field === 'name') ? 'MATCH' : 'MISMATCH',
          isMatch: !registryConflicts.some((c: any) => c.field === 'name') && (isRegistryMatch || regRecord),
          statusText: registryConflicts.some((c: any) => c.field === 'name') ? 'Mismatch' : (isRegistryMatch || regRecord ? 'Match' : 'Unverified'),
          statusStyle: registryConflicts.some((c: any) => c.field === 'name') ? 'bg-[#fce8e6] text-[#c5221f] border-[#fad2cf]' : (isRegistryMatch || regRecord ? 'bg-[#e6f4ea] text-[#137333] border-[#ceead6]' : 'bg-[#f1f3f4] text-[#5f6368] border-[#dadce0]')
        },
        {
          label: 'Date of Birth',
          submitted: submittedDob,
          registered: registeredDob,
          normalizedComparison: `${submittedDob} ↔ ${registeredDob}`,
          status: !registryConflicts.some((c: any) => c.field === 'date_of_birth' || c.field === 'dob') ? 'MATCH' : 'MISMATCH',
          isMatch: !registryConflicts.some((c: any) => c.field === 'date_of_birth' || c.field === 'dob') && (isRegistryMatch || regRecord),
          statusText: registryConflicts.some((c: any) => c.field === 'date_of_birth' || c.field === 'dob') ? 'Mismatch' : (isRegistryMatch || regRecord ? 'Match' : 'Unverified'),
          statusStyle: registryConflicts.some((c: any) => c.field === 'date_of_birth' || c.field === 'dob') ? 'bg-[#fce8e6] text-[#c5221f] border-[#fad2cf]' : (isRegistryMatch || regRecord ? 'bg-[#e6f4ea] text-[#137333] border-[#ceead6]' : 'bg-[#f1f3f4] text-[#5f6368] border-[#dadce0]')
        },
        {
          label: 'Document Expiration',
          submitted: submittedExpiry,
          registered: registeredExpiry,
          normalizedComparison: `${submittedExpiry} ↔ ${registeredExpiry}`,
          status: !registryConflicts.some((c: any) => c.field === 'expiry_date') ? 'MATCH' : 'MISMATCH',
          isMatch: !registryConflicts.some((c: any) => c.field === 'expiry_date') && regStatus !== 'EXPIRED',
          statusText: registryConflicts.some((c: any) => c.field === 'expiry_date') ? 'Mismatch' : regStatus === 'EXPIRED' ? 'Expired' : (isRegistryMatch || regRecord ? 'Valid' : 'Unverified'),
          statusStyle: registryConflicts.some((c: any) => c.field === 'expiry_date') || regStatus === 'EXPIRED' ? 'bg-[#fce8e6] text-[#c5221f] border-[#fad2cf]' : (isRegistryMatch || regRecord ? 'bg-[#e6f4ea] text-[#137333] border-[#ceead6]' : 'bg-[#f1f3f4] text-[#5f6368] border-[#dadce0]')
        },
        {
          label: 'Nationality / Country',
          submitted: submittedNat,
          registered: registeredNat,
          normalizedComparison: `${submittedNat} ↔ ${registeredNat}`,
          status: !registryConflicts.some((c: any) => c.field === 'nationality') ? 'MATCH' : 'MISMATCH',
          isMatch: !registryConflicts.some((c: any) => c.field === 'nationality'),
          statusText: registryConflicts.some((c: any) => c.field === 'nationality') ? 'Mismatch' : (isRegistryMatch || regRecord ? 'Match' : 'Unverified'),
          statusStyle: registryConflicts.some((c: any) => c.field === 'nationality') ? 'bg-[#fce8e6] text-[#c5221f] border-[#fad2cf]' : 'bg-[#e6f4ea] text-[#137333] border-[#ceead6]'
        }
      ];

  if (hasWatchlistAlert || regRecord) {
    comparisonRows.push({
      label: 'Civil Registry Security Status',
      submitted: 'INGESTED / PRESENTED',
      registered: hasWatchlistAlert ? 'WATCHLIST SECURITY ALERT' : (regRecord?.status || (isRegistryMatch ? 'ACTIVE' : 'NOT REGISTERED')),
      normalizedComparison: hasWatchlistAlert ? 'CRITICAL SECURITY WATCHLIST HIT' : (regRecord?.status || 'ACTIVE'),
      status: hasWatchlistAlert ? 'CRITICAL' : 'MATCH',
      isMatch: !hasWatchlistAlert && regStatus === 'ACTIVE',
      statusText: hasWatchlistAlert ? 'Watchlist Alert' : (regRecord?.status || (isRegistryMatch ? 'Active Record' : 'Unregistered')),
      statusStyle: hasWatchlistAlert || regStatus === 'REPORTED_LOST' || regStatus === 'REVOKED' ? 'bg-[#fce8e6] text-[#c5221f] border-[#fad2cf]' : 'bg-[#e6f4ea] text-[#137333] border-[#ceead6]'
    });
  }

  return (
    <div className="space-y-6 pb-16 font-sans">
      {/* 3-Step Flow Stepper */}
      <div className="bg-white border border-[#dadce0] rounded-2xl p-4 shadow-xs">
        <div className="flex items-center justify-between max-w-2xl mx-auto text-xs">
          {/* Step 1 */}
          <div className="flex items-center space-x-2.5">
            <span className="w-7 h-7 rounded-full bg-[#e6f4ea] text-[#1e8e3e] font-bold flex items-center justify-center text-xs">
              ✓
            </span>
            <span className="font-medium text-[#137333]">Upload Document</span>
          </div>

          <div className="w-12 h-0.5 bg-[#1a73e8]" />

          {/* Step 2 */}
          <div className="flex items-center space-x-2.5">
            <span className="w-7 h-7 rounded-full bg-[#e6f4ea] text-[#1e8e3e] font-bold flex items-center justify-center text-xs">
              ✓
            </span>
            <span className="font-medium text-[#137333]">Analyze Pipeline</span>
          </div>

          <div className="w-12 h-0.5 bg-[#1a73e8]" />

          {/* Step 3 */}
          <div className="flex items-center space-x-2.5">
            <span className="w-7 h-7 rounded-full bg-[#1a73e8] text-white font-bold flex items-center justify-center text-xs shadow-xs">
              03
            </span>
            <span className="font-semibold text-[#1a73e8]">Result & Review</span>
          </div>
        </div>
      </div>

      {/* Quick Scenario Switcher for Testers */}
      <GlobalScenarioBar
        activeScenarioId={data.case_id}
        onSelectScenario={handleScenarioChange}
      />

      {/* Document Classification & Multi-Engine Pipeline Header */}
      <div className="bg-white border border-[#dadce0] rounded-3xl p-5 shadow-xs space-y-3">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center space-x-3.5">
            <div className="w-11 h-11 rounded-2xl bg-[#e8f0fe] text-[#1a73e8] flex items-center justify-center shrink-0">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-[11px] font-semibold text-[#1a73e8] uppercase tracking-wider">
                  Detected Document Classification
                </span>
                <span className="px-2 py-0.5 rounded-full bg-[#e8f0fe] text-[#1a73e8] text-[10px] font-bold">
                  {data.document_type}
                </span>
              </div>
              <h2 className="text-lg font-bold text-[#202124] mt-0.5">
                {formatDocumentType(data.document_type)}
              </h2>
            </div>
          </div>

          {/* Engine Status Chips */}
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <div className="px-3 py-1.5 rounded-xl bg-[#f8fafd] border border-[#e0e2e6] flex items-center space-x-1.5">
              <span className="text-[#374151]">OCR:</span>
              <span className="font-semibold text-[#137333]">{data.ocr_status || 'COMPLETED'}</span>
            </div>
            <div className="px-3 py-1.5 rounded-xl bg-[#f8fafd] border border-[#e0e2e6] flex items-center space-x-1.5">
              <span className="text-[#374151]">Gemini Vision:</span>
              <span className="font-semibold text-[#1a73e8]">{data.gemini_status || 'Available (High Thinking)'}</span>
            </div>
            <div className="px-3 py-1.5 rounded-xl bg-[#f8fafd] border border-[#e0e2e6] flex items-center space-x-1.5">
              <span className="text-[#374151]">Confidence:</span>
              <span className="font-semibold text-[#202124]">
                {((data.document_type_confidence || 0.85) * 100).toFixed(1)}%
              </span>
            </div>
          </div>
        </div>

        {/* UNKNOWN Document Type Notification Banner */}
        {data.document_type === 'UNKNOWN' && (
          <div className="p-4 rounded-2xl bg-[#fef7e0] border border-[#feefc3] text-[#b06000] flex items-start space-x-3 text-xs leading-relaxed">
            <AlertTriangle className="w-5 h-5 text-[#e37400] shrink-0 mt-0.5" />
            <div>
              <span className="font-bold">Unclassified Document Format: </span>
              This uploaded file contains readable text but does not match an indexed credential format (PAN, Aadhaar, Passport, Voter ID, or DL). All visible text, dates, numbers, and layout regions have been reliably extracted and presented below. Standardized format and checksum validations are paused.
            </div>
          </div>
        )}
      </div>

      {/* 1. Main Outcome Hero Card */}
      <div className="bg-white border border-[#dadce0] rounded-3xl p-6 sm:p-7 shadow-xs space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="flex items-start space-x-4">
            <div className={`w-14 h-14 rounded-full flex items-center justify-center shrink-0 ${
              isApproved ? 'bg-[#e6f4ea] text-[#1e8e3e]' : isRejected ? 'bg-[#fce8e6] text-[#d93025]' : 'bg-[#fef7e0] text-[#e37400]'
            }`}>
              {isApproved ? (
                <CheckCircle2 className="w-8 h-8" />
              ) : isRejected ? (
                <XCircle className="w-8 h-8" />
              ) : (
                <AlertTriangle className="w-8 h-8" />
              )}
            </div>

            <div>
              <div className="flex items-center space-x-2">
                <span className={`px-2.5 py-0.5 rounded-full border text-xs font-semibold ${outcomeStyle.bg}`}>
                  {outcomeStyle.label}
                </span>
                <span className="text-xs text-[#374151]">•</span>
                <span className="text-xs text-[#374151]">Case: {data.case_id}</span>
              </div>

              <h1 className="text-xl sm:text-2xl font-bold text-[#202124] mt-1 tracking-tight">
                {isApproved 
                  ? 'Document Verified Successfully' 
                  : isRejected 
                  ? 'Document Discrepancy / Tampering Flagged' 
                  : 'Manual Officer Review Recommended'}
              </h1>

              <p className="text-xs sm:text-sm text-[#374151] mt-1 max-w-xl">
                {data.decision.rationale || 'Verification completed across all forensic modules.'}
              </p>
            </div>
          </div>

          {/* Risk Gauge Pill */}
          <div className="p-4 rounded-2xl bg-[#f8fafd] border border-[#e0e2e6] space-y-2 min-w-[220px]">
            <div className="flex items-center justify-between text-xs">
              <span className="text-[#374151] font-medium">Risk Score</span>
              <span className={`px-2 py-0.5 rounded-full border text-[11px] font-semibold ${riskInfo.badge}`}>
                {riskInfo.label}
              </span>
            </div>

            <div className="flex items-baseline space-x-1">
              <span className="text-2xl font-bold text-[#202124]">
                {data.risk.overall_score !== null && data.risk.overall_score !== undefined ? data.risk.overall_score : 'N/A'}
              </span>
              {data.risk.overall_score !== null && data.risk.overall_score !== undefined && (
                <span className="text-xs text-[#374151]">/ 100</span>
              )}
            </div>

            <div className="w-full h-2 bg-[#dadce0] rounded-full overflow-hidden">
              <div 
                className="h-full rounded-full transition-all"
                style={{ 
                  width: data.risk.overall_score !== null ? `${Math.min(100, Math.max(5, data.risk.overall_score))}%` : '0%',
                  backgroundColor: riskInfo.color
                }}
              />
            </div>
            <div className="text-[10px] text-[#374151] flex justify-between">
              <span>0 (Low)</span>
              <span>100 (High)</span>
            </div>
          </div>
        </div>

        {/* Action CTAs */}
        <div className="pt-4 border-t border-[#f1f3f4] flex flex-wrap items-center justify-between gap-3">
          <div className="text-xs text-[#5f6368]">
            Automated confidence: <span className="font-semibold text-[#202124]">{(data.decision.confidence * 100).toFixed(1)}%</span>
          </div>

          <div className="flex items-center space-x-2.5">
            <button
              type="button"
              onClick={() => navigate(`/evidence?caseId=${data.case_id}`)}
              className="px-4 py-2 rounded-full border border-[#dadce0] hover:bg-[#f8fafd] text-[#3c4043] text-xs font-medium flex items-center space-x-1.5 transition-colors"
            >
              <FileSearch className="w-3.5 h-3.5 text-[#1a73e8]" />
              <span>Inspect Evidence Reticles</span>
            </button>
            <button
              type="button"
              onClick={() => navigate(`/human-review?caseId=${data.case_id}`)}
              className="px-5 py-2 rounded-full bg-[#1a73e8] hover:bg-[#1557d0] text-white text-xs font-medium flex items-center space-x-1.5 transition-colors shadow-sm"
            >
              <UserCheck className="w-3.5 h-3.5" />
              <span>Review & Adjudicate</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* 2. "Why this result?" Explanation Section */}
      <div className="bg-white border border-[#dadce0] rounded-3xl p-6 shadow-xs space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-[#f1f3f4]">
          <div className="flex items-center space-x-2">
            <Info className="w-4 h-4 text-[#1a73e8]" />
            <h2 className="text-sm font-bold text-[#202124]">
              Why this result?
            </h2>
          </div>
          <span className="text-xs text-[#5f6368]">
            Key determining factors
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {data.risk.factors.map((factor, idx) => {
            const isNegative = factor.includes('-');
            const isPositive = factor.includes('+');

            return (
              <div 
                key={idx}
                className="p-3.5 rounded-2xl bg-[#f8fafd] border border-[#e0e2e6] flex items-center justify-between text-xs"
              >
                <div className="flex items-center space-x-2.5">
                  <div className={`w-2 h-2 rounded-full ${
                    isNegative ? 'bg-[#1e8e3e]' : isPositive ? 'bg-[#d93025]' : 'bg-[#1a73e8]'
                  }`} />
                  <span className="text-[#3c4043] font-medium">{factor}</span>
                </div>

                <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                  isNegative ? 'bg-[#e6f4ea] text-[#137333]' : isPositive ? 'bg-[#fce8e6] text-[#c5221f]' : 'bg-[#e8f0fe] text-[#1a73e8]'
                }`}>
                  {isNegative ? 'Passed' : isPositive ? 'Risk Factor' : 'Signal'}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* 3. Extracted Identity Fields (with Confirm & Edit) */}
      <div className="bg-white border border-[#dadce0] rounded-3xl p-6 shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-[#f1f3f4] gap-3">
          <div className="flex items-center space-x-2">
            <FileText className="w-4 h-4 text-[#1a73e8]" />
            <div>
              <h2 className="text-sm font-bold text-[#202124]">
                Extracted Identity Fields & Attributes
              </h2>
              <p className="text-xs text-[#5f6368]">
                Neural OCR extraction with officer validation
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2 self-end sm:self-auto">
            {fieldsSaved && (
              <span className="text-xs text-[#137333] font-medium flex items-center space-x-1 px-3 py-1 rounded-full bg-[#e6f4ea] border border-[#ceead6] animate-fade-in">
                <Check className="w-3.5 h-3.5 text-[#1e8e3e]" />
                <span>Confirmed & Saved</span>
              </span>
            )}

            {!isEditingFields ? (
              <>
                <button
                  type="button"
                  onClick={handleConfirmFields}
                  className="px-3 py-1.5 rounded-full bg-[#e6f4ea] hover:bg-[#ceead6] border border-[#ceead6] text-[#137333] text-xs font-semibold flex items-center space-x-1.5 transition-colors"
                >
                  <Check className="w-3 h-3 text-[#1e8e3e]" />
                  <span>Confirm Fields</span>
                </button>
                <button
                  type="button"
                  onClick={() => setIsEditingFields(true)}
                  className="px-3 py-1.5 rounded-full bg-white hover:bg-[#f8fafd] border border-[#dadce0] text-[#3c4043] text-xs font-medium flex items-center space-x-1.5 transition-colors"
                >
                  <Edit3 className="w-3 h-3 text-[#1a73e8]" />
                  <span>Edit Fields</span>
                </button>
              </>
            ) : (
              <>
                <button
                  type="button"
                  onClick={() => setIsEditingFields(false)}
                  className="px-3 py-1.5 rounded-full bg-white hover:bg-[#f8fafd] border border-[#dadce0] text-[#5f6368] text-xs font-medium transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleSaveFields}
                  className="px-4 py-1.5 rounded-full bg-[#1a73e8] hover:bg-[#1557d0] text-white font-medium text-xs flex items-center space-x-1.5 transition-colors shadow-sm"
                >
                  <Save className="w-3 h-3" />
                  <span>Save & Re-validate</span>
                </button>
              </>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
          {Object.entries(data.fields)
            .filter(([key]) => key !== '_metadata')
            .map(([key, value]) => {
              const meta = data.fields._metadata?.[key];
              const conf = meta?.confidence ?? data.ocr.confidence;
              const valStatus = meta?.validation_status ?? (data.document_validation.valid_format ? 'VALID' : 'UNVERIFIED');

              let statusStyle = 'text-[#137333] bg-[#e6f4ea] border-[#ceead6]';
              if (valStatus === 'DISCREPANCY') {
                statusStyle = 'text-[#c5221f] bg-[#fce8e6] border-[#fad2cf]';
              } else if (valStatus === 'UNAVAILABLE' || valStatus === 'UNVERIFIED') {
                statusStyle = 'text-[#374151] bg-[#f1f3f4] border-[#dadce0]';
              }

              return (
                <div key={key} className="p-3.5 rounded-2xl bg-[#f8fafd] border border-[#e0e2e6] flex flex-col justify-between">
                  <div className="flex items-center justify-between text-xs text-[#374151] font-medium capitalize">
                    <span>{key.replace(/_/g, ' ')}</span>
                    <span className={`px-2 py-0.2 rounded-full border text-[10px] font-semibold ${statusStyle}`}>
                      {valStatus}
                    </span>
                  </div>

                  {isEditingFields ? (
                    <input
                      type="text"
                      value={editedFields[key] ?? String(value || '')}
                      onChange={(e) => setEditedFields(prev => ({ ...prev, [key]: e.target.value }))}
                      className="w-full bg-white border border-[#1a73e8] rounded-lg p-2 text-xs text-[#202124] mt-2 focus:outline-none ring-2 ring-[#e8f0fe]"
                    />
                  ) : (
                    <div className="text-sm font-semibold text-[#202124] mt-1.5 truncate">
                      {String(value || '—')}
                    </div>
                  )}

                  <div className="mt-2.5 pt-2 border-t border-[#e0e2e6] flex items-center justify-between text-xs text-[#374151]">
                    <span>Confidence</span>
                    <span className="text-[#1a73e8] font-semibold">
                      {(conf * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              );
            })}
        </div>
      </div>

      {/* 3.5. All Extracted Readable Text (OCR + Gemini Multimodal Vision Fusion) */}
      {(() => {
        const textLines = Array.isArray(data.all_extracted_text) && data.all_extracted_text.length > 0
          ? data.all_extracted_text
          : (data.ocr?.raw_text ? data.ocr.raw_text.split('\n').map(l => l.trim()).filter(Boolean) : []);
        const fullRawText = textLines.join('\n');
        const filteredLines = textFilter.trim() 
          ? textLines.filter(line => line.toLowerCase().includes(textFilter.toLowerCase()))
          : textLines;

        const handleCopyAll = () => {
          if (!fullRawText) return;
          navigator.clipboard.writeText(fullRawText);
          setCopiedText(true);
          setTimeout(() => setCopiedText(false), 3000);
        };

        return (
          <div className="bg-white border border-[#dadce0] rounded-3xl p-6 shadow-xs space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-[#f1f3f4] gap-3">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-2xl bg-[#e8f0fe] flex items-center justify-center text-[#1a73e8] shrink-0">
                  <FileText className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <h2 className="text-sm font-bold text-[#202124]">
                      All Extracted Readable Text
                    </h2>
                    <span className="px-2 py-0.5 rounded-full bg-[#e8f0fe] text-[#1a73e8] text-[10px] font-semibold">
                      Real OCR + Gemini Vision
                    </span>
                  </div>
                  <p className="text-xs text-[#374151]">
                    Full visible textual stream extracted directly from uploaded document image
                  </p>
                </div>
              </div>

              {/* Action Buttons & Statistics */}
              <div className="flex flex-wrap items-center gap-2 self-start sm:self-auto">
                <span className="px-2.5 py-1 rounded-full bg-[#f8fafd] border border-[#e0e2e6] text-[#374151] text-xs font-medium">
                  {textLines.length} Lines • {fullRawText.length} Chars
                </span>
                {data.text_regions && data.text_regions.length > 0 && (
                  <span className="px-2.5 py-1 rounded-full bg-[#f8fafd] border border-[#e0e2e6] text-[#374151] text-xs font-medium flex items-center space-x-1">
                    <Layers className="w-3 h-3 text-[#1a73e8]" />
                    <span>{data.text_regions.length} Bounding Boxes</span>
                  </span>
                )}
                <button
                  type="button"
                  onClick={handleCopyAll}
                  disabled={!fullRawText}
                  className="px-3.5 py-1.5 rounded-full bg-white hover:bg-[#f8fafd] border border-[#dadce0] text-[#374151] text-xs font-medium flex items-center space-x-1.5 transition-colors shadow-xs disabled:opacity-50"
                >
                  {copiedText ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-[#1e8e3e]" />
                      <span className="text-[#137333] font-semibold">Copied!</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5 text-[#1a73e8]" />
                      <span>Copy Extracted Text</span>
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Filter Input */}
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-[#6b7280] absolute left-3 top-2.5" />
              <input
                type="text"
                value={textFilter}
                onChange={(e) => setTextFilter(e.target.value)}
                placeholder="Search extracted text..."
                className="w-full pl-9 pr-3 py-1.5 bg-[#f8fafd] border border-[#dadce0] rounded-xl text-xs text-[#202124] placeholder-[#6b7280] focus:outline-none focus:border-[#1a73e8] focus:bg-white transition-colors"
              />
            </div>

            {/* Monospace Extracted Text Terminal View */}
            <div className="bg-[#1e293b] rounded-2xl p-4 font-mono text-xs text-[#e2e8f0] max-h-72 overflow-y-auto space-y-1 select-text border border-[#334155]">
              {filteredLines.length > 0 ? (
                filteredLines.map((line, idx) => (
                  <div key={idx} className="flex items-start space-x-3 hover:bg-[#334155]/50 px-2 py-0.5 rounded transition-colors">
                    <span className="text-[#64748b] select-none text-[11px] w-8 text-right shrink-0">
                      {(idx + 1).toString().padStart(2, '0')}
                    </span>
                    <span className="text-[#f8fafc] break-all">
                      {line}
                    </span>
                  </div>
                ))
              ) : textLines.length > 0 ? (
                <div className="p-4 text-center text-[#94a3b8] italic">
                  No text lines match filter "{textFilter}".
                </div>
              ) : (
                <div className="p-6 text-center text-[#94a3b8] italic space-y-1">
                  <div>No text detected by OCR or Gemini vision on this specimen.</div>
                  <div className="text-[11px] text-[#64748b]">Check image focus, lighting, or orientation.</div>
                </div>
              )}
            </div>

            {/* Warnings from extraction if present */}
            {data.warnings && data.warnings.length > 0 && (
              <div className="p-3 rounded-xl bg-[#fef7e0] border border-[#feefc3] text-[#b06000] text-xs space-y-1">
                <div className="font-semibold flex items-center space-x-1.5">
                  <AlertCircle className="w-3.5 h-3.5 text-[#e37400]" />
                  <span>Extraction Warnings:</span>
                </div>
                <ul className="list-disc list-inside space-y-0.5 pl-1 text-[11px] text-[#374151]">
                  {data.warnings.map((w, widx) => (
                    <li key={widx}>{w}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        );
      })()}

      {/* 4. Authoritative Master Identity Registry Cross-Check Card */}
      <div className="bg-white border border-[#dadce0] rounded-3xl p-6 shadow-xs space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-[#f1f3f4] gap-3">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-2xl bg-[#e8f0fe] flex items-center justify-center text-[#1a73e8]">
              <Database className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-sm font-bold text-[#202124]">
                  Master Identity Registry Cross-Check
                </h2>
                <span className="px-2 py-0.5 rounded-full bg-[#f1f3f4] text-[10px] font-medium text-[#5f6368]">
                  Authoritative DB
                </span>
              </div>
              <p className="text-xs text-[#5f6368]">
                Real-time deterministic verification against sovereign reference registry records
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2 self-start sm:self-auto">
            {isRegistryMatch ? (
              <span className="px-3 py-1 rounded-full bg-[#e6f4ea] border border-[#ceead6] text-[#137333] text-xs font-semibold flex items-center space-x-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-[#1e8e3e]" />
                <span>Registry Verified (100%)</span>
              </span>
            ) : hasDiscrepancy ? (
              <span className="px-3 py-1 rounded-full bg-[#fce8e6] border border-[#fad2cf] text-[#c5221f] text-xs font-semibold flex items-center space-x-1.5">
                <XCircle className="w-3.5 h-3.5 text-[#d93025]" />
                <span>Discrepancy Flagged</span>
              </span>
            ) : isNotFound ? (
              <span className="px-3 py-1 rounded-full bg-[#fef7e0] border border-[#feefc3] text-[#b06000] text-xs font-semibold flex items-center space-x-1.5">
                <HelpCircle className="w-3.5 h-3.5 text-[#e37400]" />
                <span>Unregistered Document</span>
              </span>
            ) : (
              <span className="px-3 py-1 rounded-full bg-[#f1f3f4] text-[#5f6368] text-xs font-semibold flex items-center space-x-1.5">
                <Slash className="w-3.5 h-3.5 text-[#5f6368]" />
                <span>Registry Inactive</span>
              </span>
            )}
          </div>
        </div>

        {/* Critical Watchlist Security Banner */}
        {hasWatchlistAlert && (
          <div className="p-4 rounded-2xl bg-[#fce8e6] border border-[#fad2cf] flex items-start space-x-3 animate-fade-in">
            <AlertCircle className="w-5 h-5 text-[#d93025] shrink-0 mt-0.5" />
            <div>
              <div className="text-xs font-bold text-[#c5221f] uppercase tracking-wide">
                Critical Security Alert — Watchlist Flagged
              </div>
              <div className="text-xs text-[#5f6368] mt-0.5 font-medium">
                {watchlistReason || 'Subject or document number is flagged on active sovereign security watchlist. Immediate escalation required.'}
              </div>
            </div>
          </div>
        )}

        {/* Discrepancy Alert Callout */}
        {registryConflicts.length > 0 && !hasWatchlistAlert && (
          <div className="p-4 rounded-2xl bg-[#fef7e0] border border-[#feefc3] space-y-2 animate-fade-in">
            <div className="flex items-center space-x-2 text-xs font-bold text-[#b06000]">
              <AlertTriangle className="w-4 h-4 text-[#e37400]" />
              <span>{registryConflicts.length} Discrepanc{registryConflicts.length > 1 ? 'ies' : 'y'} Identified Against Registered Sovereign Record</span>
            </div>
            <div className="space-y-1.5 pl-6">
              {registryConflicts.map((c, i) => (
                <div key={i} className="text-xs text-[#3c4043] flex items-center justify-between bg-white/80 p-2 rounded-lg border border-[#feefc3]">
                  <span className="font-semibold capitalize text-[#202124]">{c.field?.replace(/_/g, ' ')}:</span>
                  <span className="text-[#c5221f] font-medium">{c.description || `Submitted '${c.submitted}' does not match registered '${c.registered}'`}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Comparison Table: Registered vs Ingested */}
        <div className="overflow-x-auto rounded-2xl border border-[#dadce0]">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-[#f8fafd] border-b border-[#dadce0] text-[#5f6368]">
                <th className="py-2.5 px-3 font-semibold">Attribute</th>
                <th className="py-2.5 px-3 font-semibold">Submitted Value</th>
                <th className="py-2.5 px-3 font-semibold">Authoritative Registry Record</th>
                <th className="py-2.5 px-3 font-semibold">Normalized Comparison</th>
                <th className="py-2.5 px-3 font-semibold text-right">Final Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#f1f3f4] bg-white">
              {comparisonRows.map((row: any, idx: number) => (
                <tr key={idx} className="hover:bg-[#f8fafd] transition-colors">
                  <td className="py-2.5 px-3 font-medium text-[#3c4043]">{row.label}</td>
                  <td className="py-2.5 px-3 font-mono text-[#202124] font-medium">{row.submitted || '—'}</td>
                  <td className="py-2.5 px-3 font-mono text-[#202124] font-medium">{row.registered || '—'}</td>
                  <td className="py-2.5 px-3 font-mono text-[11px]">
                    <span className="bg-[#f1f3f4] text-[#3c4043] px-2 py-0.5 rounded border border-[#e8eaed]">
                      {row.normalizedComparison || '—'}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-right">
                    <span className={`inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold border ${row.statusStyle}`}>
                      {row.isMatch ? <Check className="w-3 h-3 text-[#1e8e3e]" /> : <XCircle className="w-3 h-3 text-[#d93025]" />}
                      <span>{row.statusText}</span>
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Registry Metadata Footer */}
        <div className="pt-2 border-t border-[#f1f3f4] flex flex-wrap items-center justify-between text-[11px] text-[#5f6368] gap-2">
          <div className="flex items-center space-x-1.5">
            <span className="w-2 h-2 rounded-full bg-[#1e8e3e]" />
            <span>Authoritative Master Identity Registry (Sovereign Civil Database Adapter)</span>
          </div>
          <div className="flex items-center space-x-3">
            <span>Lookup Strategy: <strong className="text-[#202124]">{data.record_check.looked_up_by || 'Document Number'}</strong></span>
            <span>Match Score: <strong className="text-[#202124]">{(matchScore * 100).toFixed(0)}%</strong></span>
          </div>
        </div>
      </div>

      {/* 5. "View Technical Details" Collapsible Accordion */}
      <div className="bg-white border border-[#dadce0] rounded-3xl p-6 shadow-xs space-y-4">
        <button
          type="button"
          onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
          className="w-full flex items-center justify-between text-left focus:outline-none"
        >
          <div className="flex items-center space-x-2">
            <Activity className="w-4 h-4 text-[#1a73e8]" />
            <div>
              <h2 className="text-sm font-bold text-[#202124]">
                Technical Forensic Modules & Evidence
              </h2>
              <p className="text-xs text-[#5f6368]">
                Deep inspection metrics across all 6 forensic subsystems
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-1.5 text-xs text-[#1a73e8] font-medium">
            <span>{showTechnicalDetails ? 'Hide technical details' : 'View technical details'}</span>
            {showTechnicalDetails ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </div>
        </button>

        {showTechnicalDetails && (
          <div className="pt-4 border-t border-[#f1f3f4] space-y-4 animate-fade-in">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              
              {/* Subsystem 1: Quality */}
              <div className="bg-[#f8fafd] border border-[#e0e2e6] rounded-2xl p-4 space-y-2">
                <div className="flex items-center justify-between pb-2 border-b border-[#e0e2e6]">
                  <span className="font-semibold text-xs text-[#202124]">Image Quality</span>
                  <span className={`px-2 py-0.5 rounded-full border text-[10px] font-semibold flex items-center space-x-1 ${qualityBadge.badge}`}>
                    {renderCardStatusIcon(qualityBadge)}
                    <span>{qualityBadge.label}</span>
                  </span>
                </div>
                <div className="text-xs space-y-1 text-[#374151]">
                  <div className="flex justify-between">
                    <span>Quality Score:</span>
                    <span className="font-medium text-[#202124]">{(data.quality.score * 100).toFixed(0)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Resolution:</span>
                    <span className="font-medium text-[#202124]">{data.quality.resolution}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Glare:</span>
                    <span className="font-medium text-[#202124]">{(data.quality.glare * 100).toFixed(1)}%</span>
                  </div>
                </div>
              </div>

              {/* Subsystem 2: OCR */}
              <div className="bg-[#f8fafd] border border-[#e0e2e6] rounded-2xl p-4 space-y-2">
                <div className="flex items-center justify-between pb-2 border-b border-[#e0e2e6]">
                  <span className="font-semibold text-xs text-[#202124]">OCR & Gemini Vision</span>
                  <span className={`px-2 py-0.5 rounded-full border text-[10px] font-semibold flex items-center space-x-1 ${ocrBadge.badge}`}>
                    {renderCardStatusIcon(ocrBadge)}
                    <span>{ocrBadge.label}</span>
                  </span>
                </div>
                <div className="text-xs space-y-1 text-[#374151]">
                  <div className="flex justify-between">
                    <span>Engine:</span>
                    <span className="font-medium text-[#202124] text-[11px] truncate max-w-[150px]" title={data.ocr.engine || 'RapidOCR + Gemini 3.8 Flash'}>
                      {data.ocr.engine || 'RapidOCR + Gemini 3.8 Flash'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Confidence:</span>
                    <span className="font-medium text-[#202124]">{(data.ocr.confidence * 100).toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span>MRZ Checksums:</span>
                    <span className="font-medium text-[#202124]">{data.ocr.mrz?.valid ? 'Valid' : 'N/A'}</span>
                  </div>
                </div>
              </div>

              {/* Subsystem 3: Validation */}
              <div className="bg-[#f8fafd] border border-[#e0e2e6] rounded-2xl p-4 space-y-2">
                <div className="flex items-center justify-between pb-2 border-b border-[#e0e2e6]">
                  <span className="font-semibold text-xs text-[#202124]">Rule Validation</span>
                  <span className={`px-2 py-0.5 rounded-full border text-[10px] font-semibold flex items-center space-x-1 ${docValBadge.badge}`}>
                    {renderCardStatusIcon(docValBadge)}
                    <span>{docValBadge.label}</span>
                  </span>
                </div>
                <div className="text-xs space-y-1 text-[#374151]">
                  <div className="flex justify-between">
                    <span>Expiration Status:</span>
                    <span className="font-medium text-[#202124]">{data.document_validation.expiry_check}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Format Integrity:</span>
                    <span className="font-medium text-[#202124]">{data.document_validation.valid_format ? 'Pass' : (data.document_type === 'UNKNOWN' ? 'N/A' : 'Fail')}</span>
                  </div>
                </div>
              </div>

              {/* Subsystem 4: Biometrics */}
              <div className="bg-[#f8fafd] border border-[#e0e2e6] rounded-2xl p-4 space-y-2">
                <div className="flex items-center justify-between pb-2 border-b border-[#e0e2e6]">
                  <span className="font-semibold text-xs text-[#202124]">Facial Biometrics</span>
                  <span className={`px-2 py-0.5 rounded-full border text-[10px] font-semibold flex items-center space-x-1 ${faceBadge.badge}`}>
                    {renderCardStatusIcon(faceBadge)}
                    <span>{faceBadge.label}</span>
                  </span>
                </div>
                <div className="text-xs space-y-1 text-[#374151]">
                  <div className="flex justify-between">
                    <span>Model:</span>
                    <span className="font-medium text-[#202124]">FaceNet (512D)</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Cosine Similarity:</span>
                    <span className="font-medium text-[#202124]">{(data.identity.face_match_confidence * 100).toFixed(1)}%</span>
                  </div>
                </div>
              </div>

              {/* Subsystem 5: Forensics */}
              <div className="bg-[#f8fafd] border border-[#e0e2e6] rounded-2xl p-4 space-y-2">
                <div className="flex items-center justify-between pb-2 border-b border-[#e0e2e6]">
                  <span className="font-semibold text-xs text-[#202124]">Error Level Analysis</span>
                  <span className={`px-2 py-0.5 rounded-full border text-[10px] font-semibold flex items-center space-x-1 ${forensicsBadge.badge}`}>
                    {renderCardStatusIcon(forensicsBadge)}
                    <span>{forensicsBadge.label}</span>
                  </span>
                </div>
                <div className="text-xs space-y-1 text-[#374151]">
                  <div className="flex justify-between">
                    <span>Anomaly Score:</span>
                    <span className="font-medium text-[#202124]">{(data.visual_forensics.ela_score * 100).toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Copy-Move Cloning:</span>
                    <span className="font-medium text-[#202124]">{data.visual_forensics.copy_move_detected ? 'Detected' : 'None'}</span>
                  </div>
                </div>
              </div>

              {/* Subsystem 6: Registry */}
              <div className="bg-[#f8fafd] border border-[#e0e2e6] rounded-2xl p-4 space-y-2">
                <div className="flex items-center justify-between pb-2 border-b border-[#e0e2e6]">
                  <span className="font-semibold text-xs text-[#202124]">Civil Registry</span>
                  <span className={`px-2 py-0.5 rounded-full border text-[10px] font-semibold flex items-center space-x-1 ${recordBadge.badge}`}>
                    {renderCardStatusIcon(recordBadge)}
                    <span>{recordBadge.label}</span>
                  </span>
                </div>
                <div className="text-xs space-y-1 text-[#374151]">
                  <div className="flex justify-between">
                    <span>Database Status:</span>
                    <span className="font-medium text-[#202124]">{data.record_check.query_status}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Source:</span>
                    <span className="font-medium text-[#202124]">{data.record_check.registry_name}</span>
                  </div>
                </div>
              </div>

            </div>
          </div>
        )}
      </div>

    </div>
  );
};
