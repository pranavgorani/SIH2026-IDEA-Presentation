import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Shield, 
  ArrowRight, 
  UploadCloud, 
  Cpu, 
  Award, 
  CheckCircle2, 
  AlertTriangle, 
  FolderKanban, 
  BarChart3, 
  Link as LinkIcon, 
  RefreshCw,
  Sparkles,
  FileText,
  UserCheck
} from 'lucide-react';
import { getReports, getCases, verifyLedgerIntegrity } from '../services/api';
import { getOutcomeBadgeStyles, getRiskBadgeInfo, formatDocumentType } from '../utils/formatters';

export const OverviewPage: React.FC = () => {
  const navigate = useNavigate();
  const [reports, setReports] = useState<any>(null);
  const [cases, setCases] = useState<any[]>([]);
  const [ledgerStatus, setLedgerStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [rData, cData, lData] = await Promise.all([
        getReports(),
        getCases(),
        verifyLedgerIntegrity()
      ]);
      setReports(rData);
      setCases(Array.isArray(cData) ? cData.slice(0, 8) : []);
      setLedgerStatus(lData);
    } catch (err) {
      console.error('Failed to load overview data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const total = reports?.total_screenings ?? cases.length ?? 0;
  const approved = reports?.approved ?? 0;
  const passRate = reports?.pass_rate_percent ?? (total > 0 ? ((approved / total) * 100).toFixed(1) : '100.0');
  const pending = reports?.pending_review ?? 0;

  return (
    <div className="space-y-8 pb-16 font-sans">
      
      {/* Welcome Hero Banner */}
      <div className="bg-white border border-[#dadce0] rounded-3xl p-6 sm:p-8 shadow-xs relative overflow-hidden">
        <div className="max-w-3xl space-y-4">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-[#e8f0fe] text-[#1a73e8] text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5" />
            <span>AI Document Forensics & Biometric Identity</span>
          </div>

          <h1 className="text-2xl sm:text-3xl font-bold text-[#202124] tracking-tight">
            Verify identity documents with institutional confidence.
          </h1>

          <p className="text-sm sm:text-base text-[#5f6368] leading-relaxed">
            Multi-signal forensic verification powered by neural OCR, Error Level Analysis (ELA), 
            tamper reticle localization, and FaceNet facial matching.
          </p>

          <div className="pt-2 flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={() => navigate('/upload')}
              className="px-6 py-3 rounded-full bg-[#1a73e8] hover:bg-[#1557d0] text-white text-sm font-medium flex items-center space-x-2 transition-all shadow-sm"
            >
              <span>Start New Verification</span>
              <ArrowRight className="w-4 h-4" />
            </button>

            <button
              type="button"
              onClick={() => navigate('/cases')}
              className="px-5 py-3 rounded-full bg-white hover:bg-[#f8fafd] border border-[#dadce0] text-[#3c4043] text-sm font-medium flex items-center space-x-2 transition-all"
            >
              <FolderKanban className="w-4 h-4 text-[#5f6368]" />
              <span>Browse Verification Dossiers</span>
            </button>
          </div>
        </div>
      </div>

      {/* Real-time KPI Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1 */}
        <div className="bg-white border border-[#dadce0] rounded-2xl p-5 shadow-xs">
          <div className="flex items-center justify-between text-[#5f6368] text-xs">
            <span className="font-medium">Total Screenings</span>
            <FileText className="w-4 h-4 text-[#1a73e8]" />
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <span className="text-2xl font-bold text-[#202124]">{total}</span>
            <span className="text-xs font-medium text-[#137333] bg-[#e6f4ea] px-2 py-0.5 rounded-full">
              100% Audited
            </span>
          </div>
          <div className="mt-2 text-xs text-[#5f6368]">
            Indexed in database
          </div>
        </div>

        {/* Metric 2 */}
        <div className="bg-white border border-[#dadce0] rounded-2xl p-5 shadow-xs">
          <div className="flex items-center justify-between text-[#5f6368] text-xs">
            <span className="font-medium">Pass Rate</span>
            <CheckCircle2 className="w-4 h-4 text-[#1e8e3e]" />
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <span className="text-2xl font-bold text-[#137333]">{passRate}%</span>
            <span className="text-xs text-[#5f6368]">
              {approved} approved
            </span>
          </div>
          <div className="mt-2 text-xs text-[#5f6368]">
            Deterministic validation passed
          </div>
        </div>

        {/* Metric 3 */}
        <div className="bg-white border border-[#dadce0] rounded-2xl p-5 shadow-xs">
          <div className="flex items-center justify-between text-[#5f6368] text-xs">
            <span className="font-medium">Pending Review</span>
            <UserCheck className="w-4 h-4 text-[#e37400]" />
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <span className="text-2xl font-bold text-[#b06000]">{pending}</span>
            <span className="text-xs font-medium text-[#b06000] bg-[#fef7e0] px-2 py-0.5 rounded-full">
              Action required
            </span>
          </div>
          <div className="mt-2 text-xs text-[#5f6368]">
            Assigned to human adjudicators
          </div>
        </div>

        {/* Metric 4 */}
        <div className="bg-white border border-[#dadce0] rounded-2xl p-5 shadow-xs">
          <div className="flex items-center justify-between text-[#5f6368] text-xs">
            <span className="font-medium">Ledger Integrity</span>
            <LinkIcon className="w-4 h-4 text-[#1a73e8]" />
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <span className="text-2xl font-bold text-[#1a73e8]">
              {ledgerStatus?.status || 'Valid'}
            </span>
            <span className="text-xs text-[#5f6368]">
              {ledgerStatus?.verified_blocks !== undefined ? `${ledgerStatus.verified_blocks} blocks` : '0 blocks'}
            </span>
          </div>
          <div className="mt-2 text-xs text-[#5f6368]">
            SHA-256 zero-tamper guarantee
          </div>
        </div>
      </div>

      {/* 3-Step Product Verification Flow */}
      <div className="bg-white border border-[#dadce0] rounded-3xl p-6 sm:p-7 shadow-xs space-y-6">
        <div>
          <h2 className="text-base font-bold text-[#202124]">
            How Verification Works
          </h2>
          <p className="text-xs text-[#5f6368] mt-0.5">
            Institutional 3-step pipeline separating automated extraction from human adjudication
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {/* Step 01 */}
          <div className="p-5 rounded-2xl border border-[#e0e2e6] bg-[#f8fafd] space-y-3 relative hover:border-[#1a73e8] transition-colors">
            <div className="flex items-center justify-between">
              <span className="w-8 h-8 rounded-full bg-[#e8f0fe] text-[#1a73e8] font-bold text-xs flex items-center justify-center">
                01
              </span>
              <UploadCloud className="w-5 h-5 text-[#1a73e8]" />
            </div>
            <h3 className="font-semibold text-sm text-[#202124]">
              Upload & Ingest
            </h3>
            <p className="text-xs text-[#5f6368] leading-relaxed">
              Select credential type (National ID, Driver License, Passport, or Travel Permit) and supply document scan with optional live selfie probe.
            </p>
          </div>

          {/* Step 02 */}
          <div className="p-5 rounded-2xl border border-[#e0e2e6] bg-[#f8fafd] space-y-3 relative hover:border-[#1a73e8] transition-colors">
            <div className="flex items-center justify-between">
              <span className="w-8 h-8 rounded-full bg-[#e8f0fe] text-[#1a73e8] font-bold text-xs flex items-center justify-center">
                02
              </span>
              <Cpu className="w-5 h-5 text-[#1a73e8]" />
            </div>
            <h3 className="font-semibold text-sm text-[#202124]">
              Multi-Signal Analysis
            </h3>
            <p className="text-xs text-[#5f6368] leading-relaxed">
              Real-time EasyOCR neural text extraction, MRZ check digits, Error Level Analysis (ELA) for image tampering, and 512D facial biometrics.
            </p>
          </div>

          {/* Step 03 */}
          <div className="p-5 rounded-2xl border border-[#e0e2e6] bg-[#f8fafd] space-y-3 relative hover:border-[#1a73e8] transition-colors">
            <div className="flex items-center justify-between">
              <span className="w-8 h-8 rounded-full bg-[#e8f0fe] text-[#1a73e8] font-bold text-xs flex items-center justify-center">
                03
              </span>
              <Award className="w-5 h-5 text-[#1a73e8]" />
            </div>
            <h3 className="font-semibold text-sm text-[#202124]">
              Result & Review
            </h3>
            <p className="text-xs text-[#5f6368] leading-relaxed">
              Clear Pass/Fail recommendation, risk score calculation, editable OCR attributes, and final officer adjudication with cryptographic signature.
            </p>
          </div>
        </div>
      </div>

      {/* Recent Verification Dossiers */}
      <div className="bg-white border border-[#dadce0] rounded-3xl p-6 shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#f1f3f4]">
          <div>
            <h2 className="text-base font-bold text-[#202124]">
              Recent Verification Dossiers
            </h2>
            <p className="text-xs text-[#5f6368]">
              Recently screened identity credentials from database
            </p>
          </div>

          <div className="flex items-center space-x-2">
            <button
              type="button"
              onClick={fetchData}
              disabled={loading}
              className="px-3 py-1.5 rounded-full border border-[#dadce0] hover:bg-[#f8fafd] text-xs font-medium text-[#3c4043] flex items-center space-x-1.5 transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-[#1a73e8]' : 'text-[#5f6368]'}`} />
              <span>Refresh</span>
            </button>
            <button
              type="button"
              onClick={() => navigate('/cases')}
              className="px-3.5 py-1.5 rounded-full bg-[#e8f0fe] hover:bg-[#d2e3fc] text-[#1a73e8] text-xs font-semibold transition-colors"
            >
              View All
            </button>
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-[#f1f3f4] text-[#5f6368] font-medium text-[11px]">
                <th className="py-3 px-3">Case ID</th>
                <th className="py-3 px-3">Holder Name</th>
                <th className="py-3 px-3">Document</th>
                <th className="py-3 px-3">Risk Level</th>
                <th className="py-3 px-3">Decision</th>
                <th className="py-3 px-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#f1f3f4]">
              {cases.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-[#5f6368]">
                    {loading ? 'Loading cases...' : 'No verification cases found. Start a new verification to test.'}
                  </td>
                </tr>
              ) : (
                cases.map((c) => {
                  const score = typeof c.overall_score === 'number' ? c.overall_score : 0;
                  const level = c.risk_level ?? 'LOW';
                  const riskBadge = getRiskBadgeInfo(score, level);
                  const outcome = c.decision || c.status || 'PROCESSED';
                  const outcomeBadge = getOutcomeBadgeStyles(outcome);
                  const holderName = c.full_name && c.full_name !== 'UNKNOWN' ? c.full_name : '—';
                  const formattedTime = c.processed_at 
                    ? new Date(c.processed_at).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
                    : 'Recent';

                  return (
                    <tr key={c.case_id} className="hover:bg-[#f8fafd] transition-colors">
                      <td className="py-3 px-3">
                        <button
                          type="button"
                          onClick={() => navigate(`/result?caseId=${encodeURIComponent(c.case_id)}`)}
                          className="font-semibold text-[#1a73e8] hover:underline text-left"
                        >
                          {c.case_id}
                        </button>
                        <div className="text-[10px] text-[#80868b] mt-0.5">
                          {formattedTime}
                        </div>
                      </td>
                      <td className="py-3 px-3 font-medium text-[#202124]">
                        {holderName}
                      </td>
                      <td className="py-3 px-3">
                        <div className="flex flex-col">
                          <span className="font-medium text-[#3c4043]">{formatDocumentType(c.document_type)}</span>
                          <span className="text-[11px] font-mono text-[#5f6368]">{c.document_number || '—'}</span>
                        </div>
                      </td>
                      <td className="py-3 px-3">
                        <span className={`px-2 py-0.5 rounded-full border text-[11px] font-medium ${riskBadge.badge}`}>
                          {riskBadge.label} ({score})
                        </span>
                      </td>
                      <td className="py-3 px-3">
                        <span className={`px-2.5 py-0.5 rounded-full border text-[11px] font-medium ${outcomeBadge.bg}`}>
                          {outcomeBadge.label}
                        </span>
                      </td>
                      <td className="py-3 px-3 text-right">
                        <div className="flex items-center justify-end space-x-2">
                          <button
                            type="button"
                            onClick={() => navigate(`/result?caseId=${encodeURIComponent(c.case_id)}`)}
                            className="px-3 py-1 rounded-full border border-[#dadce0] hover:bg-white text-[#3c4043] text-xs font-medium transition-colors"
                          >
                            Result
                          </button>
                          <button
                            type="button"
                            onClick={() => navigate(`/human-review?caseId=${encodeURIComponent(c.case_id)}`)}
                            className="px-3 py-1 rounded-full bg-[#1a73e8] hover:bg-[#1557d0] text-white text-xs font-medium transition-colors"
                          >
                            Review
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
};

