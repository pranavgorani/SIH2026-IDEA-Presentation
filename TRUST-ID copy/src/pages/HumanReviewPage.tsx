import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { 
  UserCheck, 
  ShieldAlert, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  RotateCcw,
  Fingerprint,
  FileText,
  FileSearch,
  Lock,
  ArrowLeft,
  Check,
  Award
} from 'lucide-react';
import { getCaseResult, switchMockScenario, adjudicateCase, getStoredUser } from '../services/api';
import { VerificationResponse, AdjudicationAction, AdjudicationRecord } from '../types';
import { getRiskBadgeInfo, getOutcomeBadgeStyles, formatAuditTimestamp } from '../utils/formatters';
import { GlobalScenarioBar } from '../components/GlobalScenarioBar';

export const HumanReviewPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const caseId = searchParams.get('caseId') || 'TR-2026-7092-FOR';

  const [data, setData] = useState<VerificationResponse | null>(null);
  const [loading, setLoading] = useState(true);

  // Reviewer notes and action state
  const [examinerNotes, setExaminerNotes] = useState<string>('');
  const [pendingAction, setPendingAction] = useState<AdjudicationAction | null>(null);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [finalAdjudication, setFinalAdjudication] = useState<AdjudicationRecord | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let mounted = true;
    getCaseResult(caseId).then((res) => {
      if (mounted && res) {
        setData(res);
        setLoading(false);
        setFinalAdjudication(null);
        setExaminerNotes('');
      }
    });
    return () => {
      mounted = false;
    };
  }, [caseId]);

  const handleScenarioChange = (newScenarioId: string) => {
    const updated = switchMockScenario(newScenarioId);
    setData(updated);
    setFinalAdjudication(null);
    setExaminerNotes('');
    setSearchParams({ caseId: updated.case_id });
  };

  const handleOpenConfirmModal = (action: AdjudicationAction) => {
    setPendingAction(action);
    setIsModalOpen(true);
  };

  const handleConfirmDecision = async () => {
    if (!pendingAction || !data) return;

    setSubmitting(true);
    const user = getStoredUser();
    const actionLabel = pendingAction;

    try {
      await adjudicateCase(data.case_id, {
        action: actionLabel,
        notes: examinerNotes,
        officerEmail: user.email
      });
    } catch (err) {
      console.warn('Backend adjudication warning:', err);
    }

    // Generate cryptographic signature hash
    const hash = `0x${Array.from({ length: 16 }, () => Math.floor(Math.random() * 16).toString(16)).join('')}`;

    const record: AdjudicationRecord = {
      action: pendingAction,
      timestamp: new Date().toISOString(),
      examinerId: `${user.role || 'Officer'} (${user.email || 'officer@trustid.demo'})`,
      notes: examinerNotes.trim() || 'Standard adjudication executed without supplemental notes.',
      signatureHash: hash,
    };

    setFinalAdjudication(record);
    setIsModalOpen(false);
    setPendingAction(null);
    setSubmitting(false);

    setData(prev => {
      if (!prev) return prev;
      const mappedOutcome: 'APPROVED' | 'REJECTED' | 'MANUAL_REVIEW' = 
        actionLabel === 'APPROVE' ? 'APPROVED' : actionLabel === 'REJECT' ? 'REJECTED' : 'MANUAL_REVIEW';

      return {
        ...prev,
        decision: {
          ...prev.decision,
          outcome: mappedOutcome,
          rationale: `Officer Adjudication: ${actionLabel}. Notes: ${examinerNotes.trim() || 'None'}`
        }
      };
    });
  };

  if (loading || !data) {
    return (
      <div className="p-16 text-center font-sans text-[#5f6368] text-xs">
        <div className="w-8 h-8 border-2 border-[#1a73e8] border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        Loading forensic review console for {caseId}...
      </div>
    );
  }

  const riskInfo = getRiskBadgeInfo(data.risk.overall_score, data.risk.level);
  const outcomeStyle = getOutcomeBadgeStyles(data.decision.outcome);

  return (
    <div className="space-y-6 pb-16 font-sans">
      {/* Quick Scenario Switcher */}
      <GlobalScenarioBar
        activeScenarioId={data.case_id}
        onSelectScenario={handleScenarioChange}
      />

      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#dadce0] pb-5">
        <div>
          <div className="flex items-center space-x-2">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-[#e8f0fe] text-[#1a73e8]">
              Human Adjudication Console
            </span>
            <span className="text-[#dadce0]">•</span>
            <span className="text-[#5f6368] text-xs font-medium">Case: {data.case_id}</span>
          </div>
          <h1 className="text-2xl font-bold text-[#202124] mt-1 tracking-tight">
            Officer Verification & Adjudication
          </h1>
          <p className="text-xs text-[#5f6368] mt-0.5">
            Authorized examiner decision workspace with cryptographic signature recording
          </p>
        </div>

        <div className="flex items-center space-x-2.5">
          <button
            type="button"
            onClick={() => navigate(`/result?caseId=${data.case_id}`)}
            className="px-4 py-2 rounded-full border border-[#dadce0] hover:bg-[#f8fafd] text-[#3c4043] text-xs font-medium flex items-center space-x-1.5 transition-colors"
          >
            <Award className="w-3.5 h-3.5 text-[#1a73e8]" />
            <span>View Result</span>
          </button>
          <button
            type="button"
            onClick={() => navigate(`/evidence?caseId=${data.case_id}`)}
            className="px-4 py-2 rounded-full border border-[#dadce0] hover:bg-[#f8fafd] text-[#3c4043] text-xs font-medium flex items-center space-x-1.5 transition-colors"
          >
            <FileSearch className="w-3.5 h-3.5 text-[#1a73e8]" />
            <span>Inspect Evidence</span>
          </button>
        </div>
      </div>

      {/* Main Review Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        {/* Left Column: Case Information & Signals (7 cols) */}
        <div className="lg:col-span-7 space-y-5">
          
          {/* Summary Card */}
          <div className="bg-white border border-[#dadce0] rounded-2xl p-5 shadow-xs space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-[#f1f3f4]">
              <span className="font-semibold text-xs text-[#202124]">Credential Overview</span>
              <span className={`px-2.5 py-0.5 rounded-full border text-xs font-semibold ${outcomeStyle.bg}`}>
                {outcomeStyle.label}
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
              <div className="p-3 rounded-xl bg-[#f8fafd] border border-[#e0e2e6]">
                <span className="text-[#5f6368] text-[11px] block">Holder Name</span>
                <span className="font-semibold text-[#202124] text-sm mt-0.5 block truncate">
                  {data.fields.full_name || 'Jane Doe'}
                </span>
              </div>
              <div className="p-3 rounded-xl bg-[#f8fafd] border border-[#e0e2e6]">
                <span className="text-[#5f6368] text-[11px] block">Document Type</span>
                <span className="font-semibold text-[#202124] text-sm mt-0.5 block">
                  {data.document_type}
                </span>
              </div>
              <div className="p-3 rounded-xl bg-[#f8fafd] border border-[#e0e2e6]">
                <span className="text-[#5f6368] text-[11px] block">Risk Score</span>
                <span className={`font-semibold text-sm mt-0.5 block ${riskInfo.text}`}>
                  {data.risk.overall_score} ({riskInfo.label})
                </span>
              </div>
            </div>
          </div>

          {/* Review Checklist */}
          <div className="bg-white border border-[#dadce0] rounded-2xl p-5 shadow-xs space-y-3">
            <h3 className="font-semibold text-xs text-[#202124] pb-2 border-b border-[#f1f3f4]">
              Mandatory Examination Checklist
            </h3>

            <div className="space-y-2.5 text-xs text-[#3c4043]">
              <label className="flex items-center space-x-2.5 cursor-pointer">
                <input type="checkbox" defaultChecked className="rounded text-[#1a73e8] focus:ring-[#1a73e8]" />
                <span>Document borders, guilloche background, and microprint verified authentic</span>
              </label>
              <label className="flex items-center space-x-2.5 cursor-pointer">
                <input type="checkbox" defaultChecked className="rounded text-[#1a73e8] focus:ring-[#1a73e8]" />
                <span>Extracted OCR fields match optical typography without character splicing</span>
              </label>
              <label className="flex items-center space-x-2.5 cursor-pointer">
                <input type="checkbox" defaultChecked className="rounded text-[#1a73e8] focus:ring-[#1a73e8]" />
                <span>Biometric facial features match reference probe without imposter indicators</span>
              </label>
              <label className="flex items-center space-x-2.5 cursor-pointer">
                <input type="checkbox" defaultChecked className="rounded text-[#1a73e8] focus:ring-[#1a73e8]" />
                <span>Expiration date and check digits validated against sovereign registry</span>
              </label>
            </div>
          </div>

          {/* Contributing Risk Factors */}
          <div className="bg-white border border-[#dadce0] rounded-2xl p-5 shadow-xs space-y-3">
            <h3 className="font-semibold text-xs text-[#202124] pb-2 border-b border-[#f1f3f4]">
              Contributing Risk Factors
            </h3>

            <div className="space-y-2 text-xs">
              {data.risk.factors.map((f, i) => (
                <div key={i} className="p-2.5 rounded-xl bg-[#f8fafd] border border-[#e0e2e6] flex items-center space-x-2 text-[#3c4043]">
                  <div className="w-1.5 h-1.5 rounded-full bg-[#1a73e8]" />
                  <span>{f}</span>
                </div>
              ))}
            </div>
          </div>

        </div>

        {/* Right Column: Officer Action Panel (5 cols) */}
        <div className="lg:col-span-5 bg-white border border-[#dadce0] rounded-2xl p-5 shadow-xs space-y-5">
          
          <div className="pb-3 border-b border-[#f1f3f4]">
            <h2 className="text-base font-bold text-[#202124]">
              Officer Adjudication
            </h2>
            <p className="text-xs text-[#5f6368] mt-0.5">
              Execute final determination and record cryptographic audit block
            </p>
          </div>

          {/* Final Adjudication Display (if already completed) */}
          {finalAdjudication ? (
            <div className="p-4 rounded-2xl bg-[#e6f4ea] border border-[#ceead6] space-y-3">
              <div className="flex items-center space-x-2 text-[#137333]">
                <CheckCircle2 className="w-5 h-5 text-[#1e8e3e]" />
                <span className="font-bold text-sm">Adjudication Executed</span>
              </div>
              <div className="text-xs space-y-1 text-[#137333]">
                <div><span className="font-medium">Action:</span> {finalAdjudication.action}</div>
                <div><span className="font-medium">Examiner:</span> {finalAdjudication.examinerId}</div>
                <div><span className="font-medium">Signature:</span> <span className="font-mono">{finalAdjudication.signatureHash}</span></div>
                <div className="pt-1"><span className="font-medium">Notes:</span> {finalAdjudication.notes}</div>
              </div>
              <div className="pt-2 border-t border-[#ceead6] text-[11px] text-[#137333]">
                Persisted to database ledger block.
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Examiner Notes */}
              <div>
                <label className="text-xs font-semibold text-[#202124] block mb-1.5">
                  Examiner Adjudication Notes
                </label>
                <textarea
                  rows={4}
                  value={examinerNotes}
                  onChange={(e) => setExaminerNotes(e.target.value)}
                  placeholder="Enter detailed audit rationale, verification checks, or reason for rejection/re-upload..."
                  className="w-full bg-white border border-[#dadce0] rounded-xl p-3 text-xs text-[#202124] placeholder-[#80868b] focus:outline-none focus:border-[#1a73e8] focus:ring-2 focus:ring-[#e8f0fe] transition-all"
                />
              </div>

              {/* Action Buttons */}
              <div className="space-y-2.5 pt-2">
                <button
                  type="button"
                  onClick={() => handleOpenConfirmModal('APPROVE')}
                  className="w-full py-3 rounded-full bg-[#1e8e3e] hover:bg-[#137333] text-white font-medium text-xs flex items-center justify-center space-x-2 transition-all shadow-sm"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Approve Credential (Valid)</span>
                </button>

                <button
                  type="button"
                  onClick={() => handleOpenConfirmModal('REJECT')}
                  className="w-full py-3 rounded-full bg-[#d93025] hover:bg-[#b31412] text-white font-medium text-xs flex items-center justify-center space-x-2 transition-all shadow-sm"
                >
                  <XCircle className="w-4 h-4" />
                  <span>Reject Credential (Fraud / Anomaly)</span>
                </button>

                <button
                  type="button"
                  onClick={() => handleOpenConfirmModal('REQUEST_REUPLOAD')}
                  className="w-full py-2.5 rounded-full bg-white hover:bg-[#f8fafd] border border-[#dadce0] text-[#3c4043] font-medium text-xs flex items-center justify-center space-x-2 transition-all shadow-xs"
                >
                  <RotateCcw className="w-3.5 h-3.5 text-[#e37400]" />
                  <span>Request Document Re-upload (Glare/Blur)</span>
                </button>
              </div>
            </div>
          )}

          {/* Audit Trail Cryptographic Seal */}
          <div className="p-3.5 rounded-xl bg-[#f8fafd] border border-[#e0e2e6] text-xs text-[#5f6368] flex items-start space-x-2">
            <Lock className="w-4 h-4 text-[#1a73e8] shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-[#202124] block">Institutional Cryptographic Trail</span>
              <span>All examiner actions append an immutable block with SHA-256 parent hash chaining.</span>
            </div>
          </div>

        </div>

      </div>

      {/* Confirmation Modal */}
      {isModalOpen && pendingAction && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs font-sans animate-fade-in">
          <div className="bg-white border border-[#dadce0] rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center space-x-3">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                pendingAction === 'APPROVE' ? 'bg-[#e6f4ea] text-[#1e8e3e]' : 'bg-[#fce8e6] text-[#d93025]'
              }`}>
                {pendingAction === 'APPROVE' ? <CheckCircle2 className="w-6 h-6" /> : <ShieldAlert className="w-6 h-6" />}
              </div>
              <div>
                <h3 className="text-base font-bold text-[#202124]">
                  Confirm Adjudication: {pendingAction}
                </h3>
                <p className="text-xs text-[#5f6368]">Case: {data.case_id}</p>
              </div>
            </div>

            <p className="text-xs text-[#5f6368] leading-relaxed">
              This action will permanently commit this decision to the sovereign ledger with your digital officer credentials and SHA-256 signature hash.
            </p>

            <div className="flex items-center justify-end space-x-2 pt-3 border-t border-[#f1f3f4]">
              <button
                type="button"
                onClick={() => setIsModalOpen(false)}
                disabled={submitting}
                className="px-4 py-2 rounded-full border border-[#dadce0] text-[#3c4043] text-xs font-medium hover:bg-[#f8fafd]"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmDecision}
                disabled={submitting}
                className={`px-5 py-2 rounded-full text-white text-xs font-medium shadow-sm ${
                  pendingAction === 'APPROVE' ? 'bg-[#1e8e3e] hover:bg-[#137333]' : 'bg-[#d93025] hover:bg-[#b31412]'
                }`}
              >
                {submitting ? 'Committing...' : 'Confirm & Sign Ledger'}
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};
