import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { 
  ShieldAlert, 
  ArrowRight,
  ShieldCheck,
  UserCheck,
  Award,
  AlertTriangle,
  Info
} from 'lucide-react';
import { getCaseResult, switchMockScenario } from '../services/api';
import { VerificationResponse } from '../types';
import { formatAuditTimestamp } from '../utils/formatters';
import { DocumentEvidenceViewer } from '../components/DocumentEvidenceViewer';
import { GlobalScenarioBar } from '../components/GlobalScenarioBar';

export const EvidencePage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const caseId = searchParams.get('caseId') || 'TR-2026-7092-FOR';

  const [data, setData] = useState<VerificationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedBoxId, setSelectedBoxId] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    getCaseResult(caseId).then((res) => {
      if (mounted && res) {
        setData(res);
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
    setSearchParams({ caseId: updated.case_id });
  };

  if (loading || !data) {
    return (
      <div className="p-16 text-center font-sans text-[#5f6368] text-xs">
        <div className="w-8 h-8 border-2 border-[#1a73e8] border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        Loading forensic evidence package for {caseId}...
      </div>
    );
  }

  const evidenceItems = data.evidence.items || [];
  const primaryDocArtifact = data.evidence.artifacts.find(a => a.type === 'DOCUMENT_ORIGINAL');

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
              Forensic Evidence
            </span>
            <span className="text-[#dadce0]">•</span>
            <span className="text-[#5f6368] text-xs font-medium">Case: {data.case_id}</span>
          </div>
          <h1 className="text-2xl font-bold text-[#202124] mt-1 tracking-tight">
            Visual Forensics & Evidence Package
          </h1>
          <p className="text-xs text-[#5f6368] mt-0.5">
            Spatial anomaly inspection and localized image tampering evidence
          </p>
        </div>

        <div className="flex items-center space-x-2.5">
          <button
            type="button"
            onClick={() => navigate(`/result?caseId=${data.case_id}`)}
            className="px-4 py-2 rounded-full border border-[#dadce0] hover:bg-[#f8fafd] text-[#3c4043] text-xs font-medium flex items-center space-x-1.5 transition-colors"
          >
            <Award className="w-3.5 h-3.5 text-[#1a73e8]" />
            <span>Verification Result</span>
          </button>
          <button
            type="button"
            onClick={() => navigate(`/human-review?caseId=${data.case_id}`)}
            className="px-5 py-2 rounded-full bg-[#1a73e8] hover:bg-[#1557d0] text-white font-medium text-xs flex items-center space-x-1.5 shadow-sm transition-all"
          >
            <UserCheck className="w-3.5 h-3.5" />
            <span>Adjudicate Case</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Two-Column Forensic Matrix */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        {/* Left: Document Inspection Viewer */}
        <div className="lg:col-span-7 space-y-4">
          <DocumentEvidenceViewer
            documentUri={primaryDocArtifact?.uri}
            documentType={data.document_type}
            visualForensics={data.visual_forensics}
            evidenceItems={evidenceItems}
            selectedBoxId={selectedBoxId}
            onSelectBox={setSelectedBoxId}
          />

          {/* ELA & Algorithm Metrics Card */}
          <div className="bg-white border border-[#dadce0] rounded-2xl p-5 shadow-xs space-y-3">
            <div className="flex items-center justify-between text-xs pb-2 border-b border-[#f1f3f4]">
              <span className="font-semibold text-[#202124]">Surface Analysis Algorithms</span>
              <span className="text-[#5f6368]">Multi-Scale DCT & Residual Analysis</span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div className="p-2.5 rounded-xl bg-[#f8fafd] border border-[#e0e2e6]">
                <span className="text-[#5f6368] text-[11px] block">ELA Residue</span>
                <span className={`font-bold text-sm ${data.visual_forensics.ela_score > 0.5 ? 'text-[#d93025]' : 'text-[#137333]'}`}>
                  {data.visual_forensics.ela_score.toFixed(3)}
                </span>
              </div>
              <div className="p-2.5 rounded-xl bg-[#f8fafd] border border-[#e0e2e6]">
                <span className="text-[#5f6368] text-[11px] block">Copy-Move</span>
                <span className={`font-bold text-sm ${data.visual_forensics.copy_move_detected ? 'text-[#d93025]' : 'text-[#137333]'}`}>
                  {data.visual_forensics.copy_move_detected ? 'Detected' : 'Clear'}
                </span>
              </div>
              <div className="p-2.5 rounded-xl bg-[#f8fafd] border border-[#e0e2e6]">
                <span className="text-[#5f6368] text-[11px] block">Font Baseline</span>
                <span className={`font-bold text-sm ${data.visual_forensics.font_anomaly ? 'text-[#d93025]' : 'text-[#137333]'}`}>
                  {data.visual_forensics.font_anomaly ? 'Anomaly' : 'Consistent'}
                </span>
              </div>
              <div className="p-2.5 rounded-xl bg-[#f8fafd] border border-[#e0e2e6]">
                <span className="text-[#5f6368] text-[11px] block">EXIF / Metadata</span>
                <span className={`font-bold text-sm ${data.visual_forensics.metadata_tampered ? 'text-[#d93025]' : 'text-[#137333]'}`}>
                  {data.visual_forensics.metadata_tampered ? 'Tampered' : 'Intact'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Right: "Why Flagged?" Evidence Panel */}
        <div className="lg:col-span-5 bg-white border border-[#dadce0] rounded-2xl p-5 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-[#f1f3f4]">
            <div className="flex items-center space-x-2">
              <ShieldAlert className="w-4 h-4 text-[#d93025]" />
              <h2 className="text-sm font-bold text-[#202124]">
                Flagged Signals & Forensic Reasons
              </h2>
            </div>
            <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-[#f1f3f4] text-[#5f6368]">
              {evidenceItems.length} reasons logged
            </span>
          </div>

          {/* List of Flagged Items */}
          {evidenceItems.length > 0 ? (
            <div className="space-y-3">
              {evidenceItems.map((item, idx) => {
                const isSelected = selectedBoxId === String(idx);

                let severityStyle = 'bg-[#fce8e6] text-[#c5221f] border-[#fad2cf]';
                if (item.severity === 'MEDIUM' || item.severity === 'LOW') {
                  severityStyle = 'bg-[#fef7e0] text-[#b06000] border-[#feefc3]';
                } else if (item.severity === 'INFO') {
                  severityStyle = 'bg-[#f1f3f4] text-[#5f6368] border-[#dadce0]';
                }

                return (
                  <div
                    key={idx}
                    onClick={() => setSelectedBoxId(isSelected ? null : String(idx))}
                    className={`p-3.5 rounded-2xl border transition-all cursor-pointer ${
                      isSelected
                        ? 'bg-[#e8f0fe]/40 border-[#1a73e8] ring-2 ring-[#e8f0fe] shadow-xs'
                        : 'bg-[#f8fafd] border-[#e0e2e6] hover:border-[#bdc1c6]'
                    }`}
                  >
                    <div className="flex items-center justify-between text-xs">
                      <span className={`px-2 py-0.5 rounded-full border text-[10px] font-semibold ${severityStyle}`}>
                        {item.severity}
                      </span>
                      <span className="text-xs text-[#5f6368]">
                        Conf: {(item.confidence * 100).toFixed(0)}%
                      </span>
                    </div>

                    <div className="mt-2 text-xs font-medium text-[#202124]">
                      {item.reason}
                    </div>

                    {item.detail && (
                      <p className="text-[11px] text-[#5f6368] mt-1">
                        {item.detail}
                      </p>
                    )}

                    <div className="mt-2 pt-2 border-t border-[#e0e2e6] flex items-center justify-between text-[11px] text-[#5f6368]">
                      <span>Category: {item.category}</span>
                      <span className="text-[#1a73e8]">Click to highlight</span>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="p-8 text-center text-[#5f6368] text-xs">
              <ShieldCheck className="w-8 h-8 text-[#1e8e3e] mx-auto mb-2" />
              <span>Zero anomaly signals flagged. Document surface and security typography verified intact.</span>
            </div>
          )}

          {/* Audit Chain Verification Note */}
          <div className="p-3 rounded-xl bg-[#f8fafd] border border-[#e0e2e6] text-xs text-[#5f6368] flex items-start space-x-2">
            <Info className="w-4 h-4 text-[#1a73e8] shrink-0 mt-0.5" />
            <span>All localized evidence items are cryptographically bound to the SHA-256 audit ledger.</span>
          </div>
        </div>

      </div>

    </div>
  );
};
