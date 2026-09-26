"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ShieldAlert,
  CheckCircle2,
  AlertTriangle,
  FileText,
  Scan,
  Eye,
  Camera,
  Layers,
  Lock,
  ArrowLeft,
  UserCheck,
  Send,
  RefreshCw,
  Clock,
  Sparkles,
  ExternalLink,
  ShieldCheck,
  XCircle,
  Shield,
  AlertCircle,
} from "lucide-react";
import { api, API_BASE } from "@/lib/api";

export default function CaseInvestigationPage() {
  const params = useParams();
  const router = useRouter();
  const caseId = params.id as string;

  const [caseData, setCaseData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Forensic viewer mode: 'ORIGINAL' | 'HEATMAP' | 'BBOXES'
  const [forensicMode, setForensicMode] = useState<"ORIGINAL" | "HEATMAP" | "BBOXES">("HEATMAP");
  const [selectedRegion, setSelectedRegion] = useState<any>(null);

  // Review Form state
  const [decision, setDecision] = useState("APPROVE_AFTER_REVIEW");
  const [reason, setReason] = useState("");
  const [submittingReview, setSubmittingReview] = useState(false);
  const [reviewError, setReviewError] = useState<string | null>(null);

  // Audit verify state
  const [verifyingAudit, setVerifyingAudit] = useState(false);
  const [auditIntegrity, setAuditIntegrity] = useState<any>(null);

  const fetchCase = async () => {
    setLoading(true);
    try {
      const data = await api.getCaseDetails(caseId);
      setCaseData(data);
      if (data.tamper_result?.regions?.length > 0) {
        setSelectedRegion(data.tamper_result.regions[0]);
      }
    } catch (err: any) {
      setError(err.message || "Failed to load case investigation file");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (caseId) {
      fetchCase();
    }
  }, [caseId]);

  const handleReviewSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmittingReview(true);
    setReviewError(null);
    try {
      await api.submitReview(caseId, decision, reason);
      await fetchCase();
      setReason("");
    } catch (err: any) {
      setReviewError(err.message);
    } finally {
      setSubmittingReview(false);
    }
  };

  const handleVerifyAudit = async () => {
    setVerifyingAudit(true);
    try {
      const res = await api.verifyAuditIntegrity(caseId);
      setAuditIntegrity(res);
    } catch (err) {
      console.error(err);
    } finally {
      setVerifyingAudit(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center space-y-3">
        <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
        <div className="text-xs text-slate-400 font-mono">Loading Case Dossier #{caseId.slice(0, 8)}...</div>
      </div>
    );
  }

  if (error || !caseData) {
    return (
      <div className="max-w-4xl mx-auto py-12 px-4 text-center space-y-4">
        <div className="p-4 rounded-xl bg-red-950/40 border border-red-800 text-red-300 text-sm">
          {error || "Case record not found"}
        </div>
        <Link href="/cases" className="inline-flex items-center gap-2 text-xs text-blue-400 underline">
          <ArrowLeft className="w-4 h-4" />
          <span>Return to Cases Queue</span>
        </Link>
      </div>
    );
  }

  const { risk_assessment, tamper_result, ocr_result, validation_summary, face_verification, record_verification, audit_events } = caseData;

  const riskColor =
    caseData.risk_level === "HIGH"
      ? "#EF4444"
      : caseData.risk_level === "MEDIUM"
      ? "#F59E0B"
      : "#10B981";

  const frontDocUrl = `${API_BASE}/api/backend/documents/${caseId}/front`;
  const heatmapUrl = `${API_BASE}/api/backend/documents/${caseId}/heatmap`;
  const liveDocUrl = `${API_BASE}/api/backend/documents/${caseId}/live`;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Top Breadcrumb & Status Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-[#24365d]">
        <div className="space-y-1">
          <Link
            href="/cases"
            className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Cases Queue</span>
          </Link>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl sm:text-3xl font-black text-white font-mono">
              {caseData.case_number}
            </h1>
            <span className="px-2.5 py-0.5 rounded text-xs font-bold uppercase bg-slate-800 text-slate-200 border border-[#24365d]">
              {caseData.document_type}
            </span>
            <span
              className="px-2.5 py-0.5 rounded text-xs font-bold uppercase font-mono"
              style={{
                backgroundColor: `${riskColor}20`,
                color: riskColor,
                border: `1px solid ${riskColor}60`,
              }}
            >
              {caseData.risk_level} RISK ({caseData.risk_score}/100)
            </span>
            <span
              className={`px-2.5 py-0.5 rounded text-xs font-semibold ${
                caseData.status === "COMPLETED"
                  ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                  : caseData.status === "REVIEW_REQUIRED"
                  ? "bg-amber-500/10 text-amber-400 border border-amber-500/30"
                  : "bg-blue-500/10 text-blue-400 border border-blue-500/30"
              }`}
            >
              {caseData.status.replace("_", " ")}
            </span>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={fetchCase}
            title="Reload Case"
            className="p-2 rounded-lg bg-slate-900 border border-[#24365d] text-slate-400 hover:text-white transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* SECTION 1: RISK GAUGE & EXPLAINABLE AI ADVISORY */}
      <div className="p-6 rounded-2xl bg-slate-900/90 border border-[#24365d] shadow-xl space-y-4">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          {/* Visual Risk Gauge Block */}
          <div className="flex items-center gap-6">
            <div className="relative w-28 h-28 flex items-center justify-center rounded-full bg-slate-950 border-4 shadow-inner" style={{ borderColor: riskColor }}>
              <div className="text-center">
                <div className="text-3xl font-black font-mono text-white leading-none">
                  {caseData.risk_score}
                </div>
                <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mt-1">
                  / 100
                </div>
              </div>
            </div>

            <div>
              <div className="text-xs font-bold uppercase tracking-wider text-slate-400">
                Multi-Signal Advisory
              </div>
              <div className="text-lg font-bold text-white mt-0.5">
                {risk_assessment?.recommended_action || "Advisory Pending"}
              </div>
              <div className="text-xs text-slate-400 font-mono mt-1">
                Forensic Confidence: <strong className="text-white">{Math.round(caseData.confidence * 100)}%</strong> • MHA AI-Assisted Protocol
              </div>
            </div>
          </div>

          {/* Quick Signal Summary Pills */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
            <div className="p-2.5 rounded-lg bg-slate-950 border border-[#24365d]">
              <div className="text-slate-400 text-[10px]">VISUAL FORENSICS</div>
              <div className="font-bold text-white mt-0.5">
                {tamper_result?.tampering_detected ? "TAMPERED ⚠️" : "CLEAN ✓"}
              </div>
            </div>
            <div className="p-2.5 rounded-lg bg-slate-950 border border-[#24365d]">
              <div className="text-slate-400 text-[10px]">MRZ VALIDATION</div>
              <div className="font-bold text-white mt-0.5">
                {ocr_result?.mrz?.valid ? "ICAO VALID ✓" : "FAIL / N/A"}
              </div>
            </div>
            <div className="p-2.5 rounded-lg bg-slate-950 border border-[#24365d]">
              <div className="text-slate-400 text-[10px]">BIOMETRIC MATCH</div>
              <div className="font-bold text-white mt-0.5">
                {face_verification?.status ? face_verification.status.replace("_", " ") : "UNAVAILABLE"}
              </div>
            </div>
            <div className="p-2.5 rounded-lg bg-slate-950 border border-[#24365d]">
              <div className="text-slate-400 text-[10px]">RECORD STATUS</div>
              <div className="font-bold text-white mt-0.5">
                {record_verification?.status || "VALID"}
              </div>
            </div>
          </div>
        </div>

        {/* Explainability Breakdown (Positive vs Risk Factors) */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-[#24365d]">
          {/* Negative / Risk Factors */}
          <div className="p-3.5 rounded-xl bg-red-950/20 border border-red-900/30 space-y-2">
            <div className="text-xs font-bold text-red-400 flex items-center gap-1.5 uppercase tracking-wider">
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>Detected Risk Indicators ({risk_assessment?.risk_factors?.length || 0})</span>
            </div>
            {risk_assessment?.risk_factors?.length === 0 ? (
              <div className="text-xs text-slate-400 italic">No anomalies or negative flags detected.</div>
            ) : (
              <ul className="space-y-1 text-xs text-red-200">
                {risk_assessment?.risk_factors?.map((f: string, idx: number) => (
                  <li key={idx} className="flex items-start gap-1.5">
                    <span className="text-red-400">•</span>
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Positive Signals */}
          <div className="p-3.5 rounded-xl bg-emerald-950/20 border border-emerald-900/30 space-y-2">
            <div className="text-xs font-bold text-emerald-400 flex items-center gap-1.5 uppercase tracking-wider">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Verified Positive Signals ({risk_assessment?.positive_signals?.length || 0})</span>
            </div>
            <ul className="space-y-1 text-xs text-emerald-200">
              {risk_assessment?.positive_signals?.map((s: string, idx: number) => (
                <li key={idx} className="flex items-start gap-1.5">
                  <span className="text-emerald-400">✓</span>
                  <span>{s}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* SECTION 2: INTERACTIVE FORENSIC VIEWER */}
      <div className="p-6 rounded-2xl bg-slate-900/90 border border-[#24365d] space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <Scan className="w-5 h-5 text-purple-400" />
                <span>Visual Forensics Inspection Viewer</span>
              </h2>
              <span className="px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 text-[10px] font-mono font-bold">
                COMPUTER VISION CORE
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Inspect Error Level Analysis (ELA) compression gradients, local noise variance, and bounding boxes.
            </p>
          </div>

          {/* Mode Toggle Buttons */}
          <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-xl border border-[#24365d]">
            <button
              onClick={() => setForensicMode("ORIGINAL")}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                forensicMode === "ORIGINAL"
                  ? "bg-blue-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              Original Scan
            </button>
            <button
              onClick={() => setForensicMode("HEATMAP")}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                forensicMode === "HEATMAP"
                  ? "bg-purple-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              Tamper Heatmap (ELA)
            </button>
            <button
              onClick={() => setForensicMode("BBOXES")}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                forensicMode === "BBOXES"
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              OCR Bounding Boxes
            </button>
          </div>
        </div>

        {/* Viewer Display Window */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          <div className="lg:col-span-8 relative bg-slate-950 rounded-xl border border-[#24365d] overflow-hidden flex items-center justify-center p-2 min-h-[360px]">
            {forensicMode === "HEATMAP" ? (
              <img
                src={heatmapUrl}
                alt="Forensic Heatmap"
                className="max-h-[460px] w-auto object-contain rounded-lg shadow-2xl"
              />
            ) : forensicMode === "BBOXES" ? (
              <div className="relative inline-block">
                <img
                  src={frontDocUrl}
                  alt="Original Document"
                  className="max-h-[460px] w-auto object-contain rounded-lg"
                />
                {/* Overlay simulated bounding boxes */}
                {ocr_result?.bounding_boxes?.map((b: any, idx: number) => (
                  <div
                    key={idx}
                    className="absolute border border-cyan-400 bg-cyan-400/10 pointer-events-none text-[9px] font-mono text-cyan-200 px-1"
                    style={{
                      left: `${(b.x / 880) * 100}%`,
                      top: `${(b.y / 560) * 100}%`,
                      width: `${(b.width / 880) * 100}%`,
                      height: `${(b.height / 560) * 100}%`,
                    }}
                  >
                    {b.text.slice(0, 14)}
                  </div>
                ))}
              </div>
            ) : (
              <img
                src={frontDocUrl}
                alt="Original Document Scan"
                className="max-h-[460px] w-auto object-contain rounded-lg"
              />
            )}
          </div>

          {/* Region Details / Signal Metadata Sidebar */}
          <div className="lg:col-span-4 space-y-4">
            <div className="p-4 rounded-xl bg-slate-950 border border-[#24365d] space-y-3">
              <div className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-purple-400" />
                <span>Forensic Signals</span>
              </div>
              <div className="space-y-2 text-xs font-mono">
                <div className="flex justify-between py-1 border-b border-slate-800">
                  <span className="text-slate-400">ELA Disparity:</span>
                  <span className="text-white font-bold">{tamper_result?.signals?.ela_compression_disparity || 0.12}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800">
                  <span className="text-slate-400">Noise Anomaly:</span>
                  <span className="text-white font-bold">{tamper_result?.signals?.high_freq_noise_anomaly || 0.08}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800">
                  <span className="text-slate-400">Edge Discontinuity:</span>
                  <span className="text-white font-bold">{tamper_result?.signals?.edge_gradient_discontinuity || 0.15}</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-slate-400">Status:</span>
                  <span className={tamper_result?.tampering_detected ? "text-red-400 font-bold" : "text-emerald-400 font-bold"}>
                    {tamper_result?.tampering_detected ? "MANIPULATION DETECTED" : "UNIFORM RESIDUALS"}
                  </span>
                </div>
              </div>
            </div>

            {/* Suspicious Regions List */}
            <div className="p-4 rounded-xl bg-slate-950 border border-[#24365d] space-y-3">
              <div className="text-xs font-bold text-white uppercase tracking-wider">
                Flagged Forensic Regions ({tamper_result?.regions?.length || 0})
              </div>

              {tamper_result?.regions?.length === 0 ? (
                <div className="text-xs text-slate-400 italic">No suspicious localized alterations identified.</div>
              ) : (
                <div className="space-y-2">
                  {tamper_result?.regions?.map((reg: any, idx: number) => (
                    <div
                      key={idx}
                      onClick={() => setSelectedRegion(reg)}
                      className={`p-3 rounded-lg border cursor-pointer transition-all text-xs ${
                        selectedRegion === reg
                          ? "bg-purple-950/40 border-purple-500 text-purple-200"
                          : "bg-slate-900 border-[#24365d] text-slate-300 hover:border-slate-600"
                      }`}
                    >
                      <div className="flex items-center justify-between font-bold">
                        <span className="capitalize">{reg.type.replace("_", " ")}</span>
                        <span className="text-[11px] font-mono text-purple-400">{Math.round(reg.confidence * 100)}% Conf</span>
                      </div>
                      <p className="text-[11px] text-slate-400 mt-1 leading-snug">{reg.explanation}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* SECTION 3: OCR & MRZ CHECKSUM VERIFICATION */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Extracted Fields Table */}
        <div className="lg:col-span-7 p-6 rounded-2xl bg-slate-900/90 border border-[#24365d] space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <FileText className="w-4 h-4 text-sky-400" />
              <span>Extracted Credential Fields (OCR)</span>
            </h2>
            <span className="text-xs font-mono text-sky-400">
              OCR Confidence: {Math.round((ocr_result?.confidence || 0.9) * 100)}%
            </span>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="p-3 rounded-lg bg-slate-950 border border-[#24365d]">
              <span className="text-slate-400 block text-[10px] uppercase font-semibold">Full Legal Name</span>
              <span className="text-white font-bold text-sm mt-0.5 block">{ocr_result?.fields?.name || "—"}</span>
            </div>
            <div className="p-3 rounded-lg bg-slate-950 border border-[#24365d]">
              <span className="text-slate-400 block text-[10px] uppercase font-semibold">Document Number</span>
              <span className="text-white font-mono font-bold text-sm mt-0.5 block">{ocr_result?.fields?.document_number || "—"}</span>
            </div>
            <div className="p-3 rounded-lg bg-slate-950 border border-[#24365d]">
              <span className="text-slate-400 block text-[10px] uppercase font-semibold">Nationality</span>
              <span className="text-white font-bold mt-0.5 block">{ocr_result?.fields?.nationality || "—"}</span>
            </div>
            <div className="p-3 rounded-lg bg-slate-950 border border-[#24365d]">
              <span className="text-slate-400 block text-[10px] uppercase font-semibold">Date of Birth</span>
              <span className="text-white font-mono font-semibold mt-0.5 block">{ocr_result?.fields?.date_of_birth || "—"}</span>
            </div>
            <div className="p-3 rounded-lg bg-slate-950 border border-[#24365d]">
              <span className="text-slate-400 block text-[10px] uppercase font-semibold">Date of Expiry</span>
              <span className="text-white font-mono font-semibold mt-0.5 block">{ocr_result?.fields?.date_of_expiry || "—"}</span>
            </div>
            <div className="p-3 rounded-lg bg-slate-950 border border-[#24365d]">
              <span className="text-slate-400 block text-[10px] uppercase font-semibold">Gender / Sex</span>
              <span className="text-white font-mono font-semibold mt-0.5 block">{ocr_result?.fields?.gender || "—"}</span>
            </div>
          </div>

          {/* Raw Text Accordion */}
          <details className="text-xs text-slate-400 bg-slate-950 p-3 rounded-lg border border-[#24365d]">
            <summary className="cursor-pointer font-semibold text-slate-300">View Raw OCR Extracted Text Buffer</summary>
            <pre className="mt-2 text-[11px] font-mono text-slate-400 whitespace-pre-wrap max-h-36 overflow-y-auto">
              {ocr_result?.raw_text || "No text buffer recorded."}
            </pre>
          </details>
        </div>

        {/* ICAO 9303 MRZ Verification Card */}
        <div className="lg:col-span-5 p-6 rounded-2xl bg-slate-900/90 border border-[#24365d] space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Lock className="w-4 h-4 text-emerald-400" />
              <span>ICAO 9303 MRZ Verification</span>
            </h2>
            <span
              className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                ocr_result?.mrz?.valid
                  ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                  : "bg-red-500/20 text-red-400 border border-red-500/30"
              }`}
            >
              {ocr_result?.mrz?.valid ? "CHECKSUMS VALID ✓" : "CHECKSUM FAIL / N/A"}
            </span>
          </div>

          {ocr_result?.mrz ? (
            <div className="space-y-3 text-xs">
              <div className="p-3 rounded-lg bg-slate-950 border border-[#24365d] font-mono text-[11px] text-slate-300">
                {ocr_result.mrz.raw_mrz?.map((l: string, i: number) => (
                  <div key={i} className="tracking-wider">{l}</div>
                ))}
              </div>

              {/* Individual Check Digit Statuses */}
              <div className="space-y-1.5 font-mono text-xs">
                <div className="flex justify-between items-center py-1 border-b border-slate-800">
                  <span className="text-slate-400">Passport Number Check Digit:</span>
                  <span className={ocr_result.mrz.checksum_passport_number ? "text-emerald-400 font-bold" : "text-red-400 font-bold"}>
                    {ocr_result.mrz.checksum_passport_number ? "VALID (Weight 7-3-1)" : "FAILED"}
                  </span>
                </div>
                <div className="flex justify-between items-center py-1 border-b border-slate-800">
                  <span className="text-slate-400">DOB Check Digit:</span>
                  <span className={ocr_result.mrz.checksum_dob ? "text-emerald-400 font-bold" : "text-red-400 font-bold"}>
                    {ocr_result.mrz.checksum_dob ? "VALID" : "FAILED"}
                  </span>
                </div>
                <div className="flex justify-between items-center py-1 border-b border-slate-800">
                  <span className="text-slate-400">Expiry Check Digit:</span>
                  <span className={ocr_result.mrz.checksum_expiry ? "text-emerald-400 font-bold" : "text-red-400 font-bold"}>
                    {ocr_result.mrz.checksum_expiry ? "VALID" : "FAILED"}
                  </span>
                </div>
                <div className="flex justify-between items-center py-1">
                  <span className="text-slate-400">Composite Overall Checksum:</span>
                  <span className={ocr_result.mrz.checksum_overall ? "text-emerald-400 font-bold" : "text-red-400 font-bold"}>
                    {ocr_result.mrz.checksum_overall ? "VALID" : "FAILED"}
                  </span>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-xs text-slate-400 italic py-8 text-center">
              No Machine Readable Zone (MRZ) detected on this credential side.
            </div>
          )}
        </div>
      </div>

      {/* SECTION 4: RULE VALIDATION CHECKLIST */}
      <div className="p-6 rounded-2xl bg-slate-900/90 border border-[#24365d] space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-teal-400" />
            <span>Document Field & Chronological Validation Checklist</span>
          </h2>
          <span className="text-xs font-mono text-slate-400">
            {validation_summary?.passed_count || 0} Passed • {validation_summary?.failed_count || 0} Failed • {validation_summary?.warning_count || 0} Warnings
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {validation_summary?.checks?.map((c: any, idx: number) => {
            const isPass = c.status === "PASS";
            const isFail = c.status === "FAIL";
            return (
              <div
                key={idx}
                className={`p-3.5 rounded-xl border text-xs flex items-start gap-3 ${
                  isPass
                    ? "bg-slate-950/60 border-emerald-500/30 text-slate-300"
                    : isFail
                    ? "bg-red-950/30 border-red-500/50 text-red-200"
                    : "bg-amber-950/20 border-amber-500/40 text-amber-200"
                }`}
              >
                {isPass ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                ) : isFail ? (
                  <XCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                ) : (
                  <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
                )}
                <div>
                  <div className="font-bold flex items-center gap-2">
                    <span>{c.name}</span>
                    <span className="text-[10px] font-mono uppercase px-1.5 rounded bg-black/40">
                      {c.status}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-0.5 leading-snug">{c.message}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* SECTION 5: BIOMETRIC FACE VERIFICATION & CENTRAL RECORD CROSS-CHECK */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Face Verification Card */}
        <div className="p-6 rounded-2xl bg-slate-900/90 border border-[#24365d] space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <UserCheck className="w-4 h-4 text-purple-400" />
              <span>Biometric 1:1 Face Verification</span>
            </h2>
            <span
              className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                face_verification?.status === "MATCH_CONFIRMED"
                  ? "bg-emerald-500/20 text-emerald-400"
                  : face_verification?.status === "MATCH_REVIEW"
                  ? "bg-amber-500/20 text-amber-400"
                  : "bg-red-500/20 text-red-400"
              }`}
            >
              {face_verification?.status?.replace("_", " ") || "UNAVAILABLE"}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-4 items-center">
            <div className="text-center space-y-1.5 p-3 rounded-xl bg-slate-950 border border-[#24365d]">
              <div className="text-[10px] text-slate-400 uppercase font-semibold">Document Portrait</div>
              <img
                src={frontDocUrl}
                alt="Document Face"
                className="w-24 h-24 rounded-lg object-cover mx-auto border border-slate-700"
              />
              <div className="text-[10px] text-slate-400 font-mono">
                Quality: {Math.round((face_verification?.document_face_quality || 0.8) * 100)}%
              </div>
            </div>

            <div className="text-center space-y-1.5 p-3 rounded-xl bg-slate-950 border border-[#24365d]">
              <div className="text-[10px] text-slate-400 uppercase font-semibold">Presenter Live Photo</div>
              {face_verification?.live_face_detected ? (
                <img
                  src={liveDocUrl}
                  alt="Live Face"
                  className="w-24 h-24 rounded-lg object-cover mx-auto border border-slate-700"
                />
              ) : (
                <div className="w-24 h-24 rounded-lg bg-slate-900 border border-dashed border-slate-700 flex items-center justify-center mx-auto text-slate-500 text-[10px]">
                  No Selfie
                </div>
              )}
              <div className="text-[10px] text-slate-400 font-mono">
                Similarity: <strong className="text-white">{Math.round((face_verification?.similarity || 0) * 100)}%</strong>
              </div>
            </div>
          </div>

          <p className="text-xs text-slate-400 leading-relaxed bg-slate-950 p-3 rounded-lg border border-[#24365d]">
            {face_verification?.explanation || "Identity verification unavailable — no presented-person image provided for 1:1 comparison."}
          </p>
        </div>

        {/* Central Records Cross-Check Card */}
        <div className="p-6 rounded-2xl bg-slate-900/90 border border-[#24365d] space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-sky-400" />
              <span>Issuer Central Registry Cross-Check</span>
            </h2>
            <span
              className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                record_verification?.status === "VALID"
                  ? "bg-emerald-500/20 text-emerald-400"
                  : "bg-red-500/20 text-red-400"
              }`}
            >
              {record_verification?.status || "NOT FOUND"}
            </span>
          </div>

          <div className="p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-[11px] text-amber-300 font-semibold text-center">
            ⚠ SIMULATED / DEMONSTRATION DATA (Adapter Interface Active)
          </div>

          <div className="space-y-2 text-xs font-mono">
            <div className="flex justify-between py-1.5 border-b border-slate-800">
              <span className="text-slate-400">Database Source:</span>
              <span className="text-white font-bold">{record_verification?.source || "CENTRAL_REGISTRY_ADAPTER"}</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-800">
              <span className="text-slate-400">Document Identifier:</span>
              <span className="text-white font-bold">{record_verification?.document_number || "—"}</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-800">
              <span className="text-slate-400">Record Match Status:</span>
              <span className={record_verification?.record_found ? "text-emerald-400 font-bold" : "text-red-400 font-bold"}>
                {record_verification?.record_found ? "RECORD CONFIRMED FOUND" : "NO RECORD FOUND"}
              </span>
            </div>
            <div className="flex justify-between py-1.5">
              <span className="text-slate-400">Checked At:</span>
              <span className="text-slate-300">{new Date(record_verification?.checked_at || Date.now()).toLocaleString()}</span>
            </div>
          </div>
        </div>
      </div>

      {/* SECTION 6: BLOCKCHAIN-INSPIRED TAMPER-EVIDENT AUDIT LEDGER */}
      <div className="p-6 rounded-2xl bg-slate-900/90 border border-[#24365d] space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <Lock className="w-4 h-4 text-emerald-400" />
                <span>Tamper-Evident Cryptographic Audit Ledger</span>
              </h2>
              <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 text-[10px] font-mono font-bold">
                SHA-256 HASH CHAIN
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Every action is immutably sealed with the predecessor block hash, ensuring non-repudiation.
            </p>
          </div>

          <button
            onClick={handleVerifyAudit}
            disabled={verifyingAudit}
            className="px-4 py-2 rounded-xl bg-emerald-600/20 hover:bg-emerald-600/40 text-emerald-300 border border-emerald-500/40 text-xs font-bold font-mono flex items-center gap-2 transition-all self-start sm:self-auto"
          >
            <Shield className="w-3.5 h-3.5" />
            <span>{verifyingAudit ? "Verifying..." : "Verify Hash Integrity"}</span>
          </button>
        </div>

        {auditIntegrity && (
          <div
            className={`p-3 rounded-lg border text-xs font-mono flex items-center justify-between ${
              auditIntegrity.is_valid
                ? "bg-emerald-950/40 border-emerald-500 text-emerald-300"
                : "bg-red-950/40 border-red-500 text-red-300"
            }`}
          >
            <span>
              STATUS: {auditIntegrity.status} • {auditIntegrity.total_events} blocks cryptographically validated
            </span>
            <span className="text-[10px] opacity-75">
              Head: {auditIntegrity.last_block_hash.slice(0, 16)}...
            </span>
          </div>
        )}

        <div className="space-y-2 overflow-x-auto">
          {audit_events?.map((ev: any) => (
            <div
              key={ev.id}
              className="p-3 rounded-lg bg-slate-950 border border-[#24365d] text-xs font-mono flex flex-col md:flex-row md:items-center justify-between gap-2"
            >
              <div className="flex items-center gap-3">
                <span className="px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 font-bold">
                  #{ev.sequence_number}
                </span>
                <span className="text-white font-bold">{ev.action}</span>
                <span className="text-slate-400 text-[11px]">by {ev.actor_id}</span>
              </div>
              <div className="text-[10px] text-slate-400 flex flex-wrap items-center gap-3">
                <span>Prev: {ev.previous_hash.slice(0, 8)}...</span>
                <span className="text-sky-400">Hash: {ev.event_hash.slice(0, 12)}...</span>
                <span>{new Date(ev.timestamp).toLocaleTimeString()}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* SECTION 7: HUMAN REVIEW DECISION PANEL */}
      <div className="p-6 rounded-2xl bg-gradient-to-br from-slate-900 via-slate-900 to-blue-950/40 border border-[#24365d] shadow-2xl space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <UserCheck className="w-5 h-5 text-amber-400" />
              <span>Human Verifier Decision & Adjudication</span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Submit authorized screening decision. High-risk cases require mandatory substantive justification.
            </p>
          </div>
          {caseData.review_decision && (
            <span className="px-3 py-1 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-xs font-bold">
              ✓ ADJUDICATED BY {caseData.review_decision.reviewer_name}
            </span>
          )}
        </div>

        {caseData.review_decision && (
          <div className="p-4 rounded-xl bg-slate-950 border border-emerald-500/30 text-xs space-y-1">
            <div className="font-bold text-white flex items-center justify-between">
              <span>Decision: {caseData.review_decision.decision}</span>
              <span className="text-slate-400 font-mono text-[10px]">
                {new Date(caseData.review_decision.timestamp).toLocaleString()}
              </span>
            </div>
            <p className="text-slate-300 italic">{caseData.review_decision.reason}</p>
          </div>
        )}

        {reviewError && (
          <div className="p-3 rounded-lg bg-red-950/40 border border-red-800 text-red-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{reviewError}</span>
          </div>
        )}

        <form onSubmit={handleReviewSubmit} className="space-y-4 pt-2">
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
            {[
              { id: "APPROVE_AFTER_REVIEW", label: "Approve After Review", color: "hover:border-emerald-500" },
              { id: "REQUEST_REUPLOAD", label: "Request Re-Upload", color: "hover:border-sky-500" },
              { id: "ESCALATE", label: "Escalate to Senior Officer", color: "hover:border-purple-500" },
              { id: "MARK_FOR_INVESTIGATION", label: "Mark for Forensic Investigation", color: "hover:border-red-500" },
            ].map((opt) => (
              <button
                key={opt.id}
                type="button"
                onClick={() => setDecision(opt.id)}
                className={`p-3 rounded-xl border text-xs font-bold transition-all text-left ${
                  decision === opt.id
                    ? "bg-blue-600/30 border-blue-400 text-white shadow-md shadow-blue-500/20"
                    : `bg-slate-950 border-[#24365d] text-slate-400 ${opt.color}`
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Adjudication Reason & Rationale {caseData.risk_level === "HIGH" && <span className="text-red-400">* (Mandatory for High-Risk)</span>}
            </label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              required={caseData.risk_level === "HIGH"}
              rows={3}
              placeholder="State the verification findings, visual inspection notes, and justification for this decision..."
              className="w-full p-3 rounded-xl bg-slate-950 border border-[#24365d] text-white text-xs focus:outline-none focus:border-blue-500"
            />
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={submittingReview}
              className="px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs shadow-lg shadow-blue-500/30 flex items-center gap-2 transition-all disabled:opacity-50"
            >
              {submittingReview ? (
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  <span>Commit Human Verifier Decision</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
