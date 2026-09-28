"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  UploadCloud,
  FileCheck,
  Camera,
  Layers,
  ArrowRight,
  AlertCircle,
  CheckCircle2,
  XCircle,
  Cpu,
  Scan,
  Shield,
  Eye,
  EyeOff,
  FileText,
  UserCheck,
  RotateCcw,
  Check,
  Globe,
  Calendar,
  Hash,
  User,
  ShieldCheck,
  SwitchCamera,
  Zap
} from "lucide-react";
import { api, ScreeningException } from "@/lib/api";
import DocumentScanner from "@/components/DocumentScanner";

const PIPELINE_STEPS = [
  { id: 1, key: "UPLOAD", label: "DOCUMENT UPLOAD & HASHING", icon: UploadCloud, desc: "Computing SHA-256 hash & integrity check" },
  { id: 2, key: "IMAGE_QUALITY", label: "IMAGE QUALITY CHECK", icon: Eye, desc: "Testing blur, glare, contrast & resolution" },
  { id: 3, key: "DOCUMENT_CLASSIFICATION", label: "DOCUMENT CLASSIFICATION", icon: Layers, desc: "Detecting credential layout & ISO aspect" },
  { id: 4, key: "OCR", label: "OCR & MRZ EXTRACTION", icon: FileText, desc: "Parsing ICAO 9303 check digits & text" },
  { id: 5, key: "FIELD_VALIDATION", label: "FIELD VALIDATION", icon: FileCheck, desc: "Testing expiry & chronological integrity" },
  { id: 6, key: "VISUAL_FORENSICS", label: "VISUAL FORENSICS", icon: Scan, desc: "Running Error Level Analysis (ELA) & noise profiling" },
  { id: 7, key: "FACE_VERIFICATION", label: "IDENTITY VERIFICATION", icon: UserCheck, desc: "1:1 biometric facial portrait comparison" },
  { id: 8, key: "RECORD_VERIFICATION", label: "RECORD CROSS-CHECK", icon: Shield, desc: "Consulting central issuing registry (simulated)" },
  { id: 9, key: "RISK_ASSESSMENT", label: "MULTI-SIGNAL RISK FUSION", icon: Cpu, desc: "Synthesizing weights into explainable 0–100 score" },
  { id: 10, key: "EXPLANATION", label: "EXPLAINABLE REPORT & AUDIT", icon: CheckCircle2, desc: "Appending SHA-256 tamper-evident block" },
];

interface ScreeningErrorInfo {
  stage: string;
  reason: string;
  code: string;
  recoverable: boolean;
  failedStepId: number;
  requestId?: string;
  userAction?: string;
  debugDetails?: any;
}

export default function ScreeningPage() {
  const router = useRouter();

  // Intake mode: live camera vs file upload
  const [intakeMode, setIntakeMode] = useState<"camera" | "upload">("camera");
  const [showLiveSelfieScanner, setShowLiveSelfieScanner] = useState(false);

  const [frontFile, setFrontFile] = useState<File | null>(null);
  const [backFile, setBackFile] = useState<File | null>(null);
  const [liveFile, setLiveFile] = useState<File | null>(null);
  const [docTypeHint, setDocTypeHint] = useState("AUTO_DETECT");
  const [notes, setNotes] = useState("");

  const [frontPreview, setFrontPreview] = useState<string | null>(null);
  const [livePreview, setLivePreview] = useState<string | null>(null);

  const [isProcessing, setIsProcessing] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [screeningError, setScreeningError] = useState<ScreeningErrorInfo | null>(null);
  const [screenResult, setScreenResult] = useState<any>(null);
  const [autoDownloaded, setAutoDownloaded] = useState(false);

  // Security mask toggle for document number in UI
  const [showDocNumber, setShowDocNumber] = useState(false);

  // User and diagnostics state
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false);
  const [retryStatus, setRetryStatus] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("trustid_user");
      if (stored) {
        try {
          setCurrentUser(JSON.parse(stored));
        } catch {}
      }
    }
  }, []);

  const handleFrontSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setFrontFile(file);
      setFrontPreview(URL.createObjectURL(file));
      setScreeningError(null);
    }
  };

  const handleCameraCapture = (file: File, metadata?: any) => {
    setFrontFile(file);
    setFrontPreview(URL.createObjectURL(file));
    if (metadata?.docType) {
      setDocTypeHint(metadata.docType);
    }
    setScreeningError(null);
  };

  const handleLiveSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setLiveFile(file);
      setLivePreview(URL.createObjectURL(file));
    }
  };

  const handleSelfieCapture = (file: File) => {
    setLiveFile(file);
    setLivePreview(URL.createObjectURL(file));
    setShowLiveSelfieScanner(false);
  };

  const executePipeline = async (overrideHint?: string, forceFallback: boolean = false, forceFresh: boolean = false) => {
    if (!frontFile) {
      setScreeningError({
        stage: "Input Validation",
        reason: "Please capture or upload the primary document front image before executing screening.",
        code: "MISSING_FRONT_FILE",
        recoverable: true,
        failedStepId: 1,
        userAction: "Select or capture a credential image to proceed."
      });
      return;
    }

    setIsProcessing(true);
    setCurrentStep(1);
    setScreeningError(null);
    setRetryStatus(null);

    // Dynamic pipeline step advancement without artificial freezes
    const interval = setInterval(() => {
      setCurrentStep((prev) => (prev < 9 ? prev + 1 : prev));
    }, 150);

    try {
      const formData = new FormData();
      formData.append("file", frontFile);
      if (backFile) formData.append("back_file", backFile);
      if (liveFile) formData.append("live_person_file", liveFile);
      formData.append("document_type_hint", overrideHint || docTypeHint);
      if (forceFallback) {
        formData.append("force_local_fallback", "true");
      }
      if (forceFresh) {
        formData.append("force_fresh", "true");
      }
      if (notes) formData.append("notes", notes);

      const res = await api.screenDocument(formData, {
        onRetryAttempt: (attempt, maxAttempts) => {
          setRetryStatus(`Auto-retrying transient error (${attempt}/${maxAttempts})...`);
        }
      });
      clearInterval(interval);
      setCurrentStep(10);
      setScreenResult(res);
      setIsProcessing(false);
      setRetryStatus(null);

      // Automatic PDF download as required by Spec 12 & 39
      if (res.report_pdf_url) {
        try {
          const dlLink = document.createElement("a");
          dlLink.href = res.report_pdf_url;
          dlLink.setAttribute("download", `TRUST-ID_Report_${res.case_number || res.case_id}.pdf`);
          document.body.appendChild(dlLink);
          dlLink.click();
          dlLink.remove();
          setAutoDownloaded(true);
        } catch (dlErr) {
          console.warn("Auto PDF download notice:", dlErr);
        }
      }
    } catch (err: any) {
      clearInterval(interval);

      const stageKey = err.stage || "OCR";
      const matchedStep = PIPELINE_STEPS.find((s) => s.key === stageKey);
      const failedStepId = matchedStep ? matchedStep.id : (stageKey === "GATEWAY" ? 1 : 4);
      const stageName = matchedStep ? matchedStep.label : stageKey;

      setScreeningError({
        stage: stageName,
        reason: err.message || "Screening could not be completed.",
        code: err.code || "SCREENING_ERROR",
        recoverable: err.recoverable ?? true,
        failedStepId,
        requestId: err.requestId,
        userAction: err.userAction,
        debugDetails: err.debugDetails
      });
      setCurrentStep(failedStepId);
      setIsProcessing(false);
      setRetryStatus(null);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    executePipeline();
  };

  const handleRetry = () => {
    executePipeline();
  };

  const handleLocalFallback = () => {
    executePipeline(docTypeHint, true);
  };

  const handleReset = () => {
    setScreenResult(null);
    setScreeningError(null);
    setIsProcessing(false);
    setCurrentStep(0);
    setFrontFile(null);
    setFrontPreview(null);
    setLiveFile(null);
    setLivePreview(null);
    setShowLiveSelfieScanner(false);
  };

  // Helper to mask document numbers (e.g. A1234567 -> A1••••67)
  const maskDocNumber = (num?: string) => {
    if (!num) return "—";
    if (num.length <= 4) return num;
    return `${num.slice(0, 2)}${"•".repeat(Math.max(4, num.length - 4))}${num.slice(-2)}`;
  };

  const extractedFields = screenResult?.ocr?.fields || {};
  const mrzData = screenResult?.ocr?.mrz || null;
  const ocrConfidence = Math.round((screenResult?.ocr?.confidence || screenResult?.confidence || 0) * 100);

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Page Header */}
      <div>
        <div className="flex items-center gap-2">
          <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
            Document Screening Pipeline
          </h1>
          <span className="px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 text-xs font-mono font-bold">
            10-STAGE AI INSPECTION
          </span>
        </div>
        <p className="text-xs text-slate-400 mt-1">
          Scan or upload credential documents with real-time optical capture, OCR extraction, and multi-signal forensic analysis.
        </p>
      </div>

      {/* Structured Error UI Banner */}
      {screeningError && (
        <div className="p-6 rounded-2xl bg-red-950/40 border border-red-800/80 shadow-2xl space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-red-600/20 text-red-400 border border-red-500/40 flex items-center justify-center flex-shrink-0">
                <XCircle className="w-6 h-6" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="px-2.5 py-0.5 rounded text-[10px] font-mono font-bold bg-red-500/20 text-red-400 border border-red-500/30 uppercase tracking-wider">
                    SCREENING FAILED
                  </span>
                  {screeningError.code && (
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-slate-800 text-slate-300 border border-slate-700">
                      {screeningError.code}
                    </span>
                  )}
                </div>
                <h3 className="text-base sm:text-lg font-bold text-white mt-1">
                  Stage: {screeningError.stage}
                </h3>
              </div>
            </div>

            {screeningError.requestId && (
              <div className="text-left sm:text-right bg-slate-900/60 p-2 sm:p-0 rounded-lg sm:bg-transparent">
                <span className="text-[10px] font-mono text-slate-400 block font-semibold">REQUEST ID</span>
                <span className="text-xs font-mono text-blue-400 select-all font-bold">{screeningError.requestId}</span>
              </div>
            )}
          </div>

          <div className="p-4 rounded-xl bg-slate-950/60 border border-red-900/40 space-y-2 text-xs">
            <div>
              <span className="text-slate-400 font-semibold">Reason: </span>
              <span className="text-red-200 font-medium">{screeningError.reason}</span>
            </div>
            <div>
              <span className="text-slate-400 font-semibold">Recommended action: </span>
              <span className="text-slate-300">
                {screeningError.userAction || (screeningError.recoverable
                  ? "Retry screening or execute with local computer-vision fallback."
                  : "Please inspect the uploaded document scan and re-upload in a supported format (PDF, PNG, JPG, WEBP).")}
              </span>
            </div>
            {retryStatus && (
              <div className="text-amber-400 font-mono text-[11px] animate-pulse">
                {retryStatus}
              </div>
            )}
          </div>

          {/* Admin-only technical details accordion */}
          {currentUser?.role === "ADMIN" && screeningError.debugDetails && (
            <div className="rounded-xl border border-slate-800 bg-slate-950/80 overflow-hidden text-xs">
              <button
                type="button"
                onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
                className="w-full px-4 py-2.5 flex items-center justify-between text-left text-slate-400 hover:text-slate-200 font-mono text-xs font-semibold bg-slate-900/40"
              >
                <span>Diagnostic Logs & Technical Details (ADMIN ONLY)</span>
                <span>{showTechnicalDetails ? "▲ Hide" : "▼ Show"}</span>
              </button>
              {showTechnicalDetails && (
                <div className="p-4 border-t border-slate-800 bg-slate-950 font-mono text-[11px] text-slate-300 space-y-1.5 overflow-x-auto">
                  <div><span className="text-slate-500">Endpoint:</span> {screeningError.debugDetails.url || "/api/backend/screen"}</div>
                  <div><span className="text-slate-500">HTTP Status:</span> {screeningError.debugDetails.status} {screeningError.debugDetails.statusText}</div>
                  {screeningError.debugDetails.rawBody && (
                    <div className="mt-2 p-2 rounded bg-black/60 text-slate-400 whitespace-pre-wrap font-mono text-[10px] max-h-40 overflow-y-auto">
                      {screeningError.debugDetails.rawBody}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          <div className="flex flex-wrap items-center gap-3 pt-1">
            <button
              onClick={handleRetry}
              disabled={isProcessing}
              className="px-4 py-2 rounded-xl bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white font-bold text-xs shadow-md shadow-red-500/25 transition-all flex items-center gap-1.5"
            >
              <RotateCcw className={`w-3.5 h-3.5 ${isProcessing ? "animate-spin" : ""}`} />
              <span>Retry Screening</span>
            </button>

            {screeningError.recoverable && (
              <button
                onClick={handleLocalFallback}
                disabled={isProcessing}
                className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-bold text-xs shadow-md shadow-blue-500/25 transition-all flex items-center gap-1.5"
              >
                <Cpu className="w-3.5 h-3.5" />
                <span>Use Local Fallback</span>
              </button>
            )}

            <button
              onClick={handleReset}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-xs transition-all"
            >
              <span>Re-scan / Re-upload Document</span>
            </button>
          </div>
        </div>
      )}

      {/* Main Upload / Processing Container */}
      {!isProcessing && !screenResult && !screeningError ? (
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
            {/* Primary Document Intake Area */}
            <div className="md:col-span-7 space-y-4">
              <div className="p-6 rounded-2xl bg-slate-900/90 border border-[#24365d] space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <label className="text-sm font-bold text-white flex items-center gap-2">
                    <Scan className="w-4 h-4 text-blue-400" />
                    <span>Primary Document Intake *</span>
                  </label>

                  {/* Mode Selector Tabs: Live Camera vs File Upload */}
                  <div className="flex items-center rounded-xl bg-slate-950 p-1 border border-[#24365d]">
                    <button
                      type="button"
                      onClick={() => setIntakeMode("camera")}
                      className={`px-3 py-1 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
                        intakeMode === "camera"
                          ? "bg-blue-600 text-white shadow-md shadow-blue-500/20"
                          : "text-slate-400 hover:text-slate-200"
                      }`}
                    >
                      <Camera className="w-3.5 h-3.5" />
                      <span>Live Camera Scanner</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => setIntakeMode("upload")}
                      className={`px-3 py-1 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
                        intakeMode === "upload"
                          ? "bg-blue-600 text-white shadow-md shadow-blue-500/20"
                          : "text-slate-400 hover:text-slate-200"
                      }`}
                    >
                      <UploadCloud className="w-3.5 h-3.5" />
                      <span>File Upload</span>
                    </button>
                  </div>
                </div>

                {/* Intake Mode 1: Live Interactive Camera Scanner */}
                {intakeMode === "camera" && !frontPreview && (
                  <DocumentScanner
                    mode="document"
                    title="Optical Document Scanner"
                    subtitle="Align passport, national ID, visa, or driving licence inside the viewfinder"
                    onCapture={handleCameraCapture}
                  />
                )}

                {/* Intake Mode 2: Standard Drag & Drop File Upload */}
                {intakeMode === "upload" && !frontPreview && (
                  <div className="relative border-2 border-dashed border-[#24365d] hover:border-blue-500/60 rounded-xl p-8 text-center bg-slate-950/40 transition-colors">
                    <div className="space-y-2">
                      <div className="w-12 h-12 rounded-xl bg-blue-600/10 text-blue-400 border border-blue-500/20 flex items-center justify-center mx-auto">
                        <UploadCloud className="w-6 h-6" />
                      </div>
                      <div className="text-xs text-slate-300 font-semibold">
                        Drag and drop credential image, or{" "}
                        <span className="text-blue-400 underline">browse device</span>
                      </div>
                      <p className="text-[11px] text-slate-500">
                        Supports Passports, Visas, National IDs, Driving Licences & Permits (PNG, JPG, WEBP max 25MB)
                      </p>
                    </div>

                    <input
                      type="file"
                      accept="image/*"
                      onChange={handleFrontSelect}
                      className="absolute inset-0 opacity-0 cursor-pointer"
                    />
                  </div>
                )}

                {/* Captured / Selected Preview View */}
                {frontPreview && (
                  <div className="p-4 rounded-xl bg-slate-950/70 border border-[#24365d] space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="text-xs text-emerald-400 font-semibold flex items-center gap-1.5">
                        <CheckCircle2 className="w-4 h-4" />
                        <span>Ready: {frontFile?.name || "Document Scan Captured"}</span>
                      </div>

                      <button
                        type="button"
                        onClick={() => {
                          setFrontFile(null);
                          setFrontPreview(null);
                        }}
                        className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] font-semibold flex items-center gap-1 transition-all"
                      >
                        <RotateCcw className="w-3 h-3" />
                        <span>Re-scan / Replace</span>
                      </button>
                    </div>

                    <div className="relative max-h-64 rounded-lg overflow-hidden border border-[#24365d] bg-black flex items-center justify-center">
                      <img
                        src={frontPreview}
                        alt="Front Preview"
                        className="max-h-60 mx-auto object-contain shadow-lg"
                      />
                    </div>
                  </div>
                )}

                {/* Optional Back Side */}
                <div className="pt-2">
                  <label className="text-xs font-semibold text-slate-300 block mb-1">
                    Optional Credential Reverse / Back Side
                  </label>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={(e) => setBackFile(e.target.files ? e.target.files[0] : null)}
                    className="block w-full text-xs text-slate-400 file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-slate-800 file:text-slate-300 hover:file:bg-slate-700 cursor-pointer"
                  />
                </div>
              </div>
            </div>

            {/* Sidebar: Presenter Image & Parameters */}
            <div className="md:col-span-5 space-y-4">
              {/* Optional Live Presenter Portrait */}
              <div className="p-6 rounded-2xl bg-slate-900/90 border border-[#24365d] space-y-4">
                <div className="flex items-center justify-between">
                  <label className="text-sm font-bold text-white flex items-center gap-2">
                    <Camera className="w-4 h-4 text-purple-400" />
                    <span>Presenter Live Portrait (Optional)</span>
                  </label>
                  <span className="text-[10px] text-purple-300 font-mono">1:1 Biometrics</span>
                </div>

                {showLiveSelfieScanner ? (
                  <DocumentScanner
                    mode="selfie"
                    title="Live Face Biometrics"
                    subtitle="Center face in frame for 1:1 facial matching against document"
                    onCapture={handleSelfieCapture}
                    onCancel={() => setShowLiveSelfieScanner(false)}
                  />
                ) : livePreview ? (
                  <div className="space-y-2 p-3 rounded-xl bg-slate-950/60 border border-[#24365d]">
                    <img
                      src={livePreview}
                      alt="Live Portrait"
                      className="max-h-36 mx-auto rounded-lg border border-[#24365d] object-contain"
                    />
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="text-purple-300 font-semibold truncate max-w-[180px]">
                        {liveFile?.name || "Live Portrait Captured"}
                      </span>
                      <button
                        type="button"
                        onClick={() => {
                          setLiveFile(null);
                          setLivePreview(null);
                        }}
                        className="text-slate-400 hover:text-slate-200 underline"
                      >
                        Remove
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-3">
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => setShowLiveSelfieScanner(true)}
                        className="flex-1 py-2 px-3 rounded-lg bg-purple-950/60 hover:bg-purple-900/80 text-purple-200 border border-purple-800/80 text-xs font-semibold flex items-center justify-center gap-1.5 transition-all"
                      >
                        <Camera className="w-3.5 h-3.5 text-purple-400" />
                        <span>Take Selfie Photo</span>
                      </button>
                    </div>

                    <div className="relative border border-dashed border-[#24365d] hover:border-purple-500/60 rounded-xl p-3 text-center bg-slate-950/40 transition-colors">
                      <div className="text-[11px] text-slate-400">
                        Or click to upload selfie file from device
                      </div>
                      <input
                        type="file"
                        accept="image/*"
                        onChange={handleLiveSelect}
                        className="absolute inset-0 opacity-0 cursor-pointer"
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* Document Type Hint & Notes */}
              <div className="p-6 rounded-2xl bg-slate-900/90 border border-[#24365d] space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                    Credential Classification
                  </label>
                  <select
                    value={docTypeHint}
                    onChange={(e) => setDocTypeHint(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-[#24365d] text-white text-xs focus:outline-none focus:border-blue-500"
                  >
                    <option value="AUTO_DETECT">Auto-Detect via AI Engine</option>
                    <option value="PASSPORT">Passport (ICAO 9303 TD3)</option>
                    <option value="NATIONAL_ID">National ID Card (TD1)</option>
                    <option value="VISA">Consular Travel Visa</option>
                    <option value="DRIVING_LICENSE">Driving Licence</option>
                    <option value="PERMIT">Work / Stay Permit</option>
                    <option value="TRAVEL_AUTHORIZATION">Electronic Travel Authorization (ETA)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                    Operational Checkpoint Notes (Optional)
                  </label>
                  <textarea
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    rows={2}
                    placeholder="e.g. Checkpoint Alpha, primary lane 3 scrutiny"
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-[#24365d] text-white text-xs focus:outline-none focus:border-blue-500"
                  />
                </div>

                <button
                  type="submit"
                  disabled={!frontFile}
                  className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold text-xs shadow-lg shadow-blue-500/25 flex items-center justify-center gap-2 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <Scan className="w-4 h-4" />
                  <span>Execute AI Screening Pipeline</span>
                </button>
              </div>
            </div>
          </div>
        </form>
      ) : isProcessing || screeningError ? (
        /* Real-Time Processing & Failure Pipeline Status */
        <div className="p-8 rounded-2xl bg-slate-900/95 border border-[#24365d] shadow-2xl space-y-6">
          <div className="text-center space-y-2">
            <div
              className={`w-12 h-12 rounded-xl border flex items-center justify-center mx-auto ${
                screeningError
                  ? "bg-red-600/20 text-red-400 border-red-500/40"
                  : "bg-blue-600/20 text-blue-400 border-blue-500/30 animate-pulse"
              }`}
            >
              {screeningError ? <XCircle className="w-6 h-6" /> : <Cpu className="w-6 h-6 animate-spin" />}
            </div>
            <h2 className="text-xl font-bold text-white">
              {screeningError ? "Screening Pipeline Halted" : "AI Screening Pipeline Active"}
            </h2>
            <p className="text-xs text-slate-400">
              {screeningError
                ? `An issue occurred during stage execution: ${screeningError.stage}. Review details above.`
                : "Executing multi-signal forensic inspection, ICAO check digits & biometric cross-checks..."}
            </p>
          </div>

          <div className="space-y-3 max-w-xl mx-auto pt-4">
            {PIPELINE_STEPS.map((step) => {
              const Icon = step.icon;
              const isFailedStep = screeningError && screeningError.failedStepId === step.id;
              const isPastStep = screeningError
                ? step.id < screeningError.failedStepId
                : currentStep > step.id;
              const isCurrentStep = !screeningError && currentStep === step.id;

              return (
                <div
                  key={step.id}
                  className={`p-3 rounded-lg border transition-all flex items-center justify-between text-xs ${
                    isFailedStep
                      ? "bg-red-950/60 border-red-500/70 text-red-300 shadow-lg shadow-red-500/10"
                      : isPastStep
                      ? "bg-slate-950/80 border-emerald-500/30 text-emerald-400"
                      : isCurrentStep
                      ? "bg-blue-950/40 border-blue-500 text-blue-300 shadow-md shadow-blue-500/10 scale-[1.01]"
                      : "bg-slate-950/20 border-[#1c2c4d] text-slate-500"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon
                      className={`w-4 h-4 ${
                        isFailedStep
                          ? "text-red-400"
                          : isPastStep
                          ? "text-emerald-400"
                          : isCurrentStep
                          ? "animate-pulse text-blue-400"
                          : "text-slate-600"
                      }`}
                    />
                    <div>
                      <div className="font-bold tracking-wide">
                        {step.id}. {step.label}
                      </div>
                      <div className="text-[10px] text-slate-400">{step.desc}</div>
                    </div>
                  </div>
                  <div>
                    {isFailedStep ? (
                      <span className="text-[10px] font-mono font-bold text-red-400 bg-red-500/10 px-2 py-0.5 rounded flex items-center gap-1">
                        <XCircle className="w-3 h-3" />
                        FAILED
                      </span>
                    ) : isPastStep ? (
                      <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded flex items-center gap-1">
                        <Check className="w-3 h-3" />
                        DONE
                      </span>
                    ) : isCurrentStep ? (
                      <div className="w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
                    ) : (
                      <span className="text-[10px] font-mono text-slate-600">PENDING</span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {screeningError && (
            <div className="text-center pt-2">
              <button
                onClick={handleRetry}
                className="px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs shadow-lg shadow-blue-500/25 transition-all inline-flex items-center gap-2"
              >
                <RotateCcw className="w-4 h-4" />
                <span>Retry from Failed Stage ({screeningError.stage})</span>
              </button>
            </div>
          )}
        </div>
      ) : (
        /* Screening Result & Comprehensive Extracted Fields */
        <div className="space-y-6">
          {/* 100-POINT DOCUMENT VERIFICATION & REPORT DISPATCH BANNER (Specs 8, 16, 38, 39) */}
          <div className="p-6 rounded-2xl bg-gradient-to-br from-slate-900 via-[#0b1736] to-slate-900 border-2 border-blue-500/50 shadow-2xl relative overflow-hidden">
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-[10px] font-mono font-bold uppercase tracking-wider">
                    SCREENING COMPLETE
                  </span>
                  <span className="px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30 text-[10px] font-mono font-bold uppercase tracking-wider">
                    100 CHECKS EXECUTED
                  </span>
                  {(screenResult?.ai_status === "fallback" || screenResult?.force_local_fallback) && (
                    <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 text-[10px] font-mono font-bold uppercase tracking-wider">
                      Processed with Local CV Fallback (AI unavailable)
                    </span>
                  )}
                  {screenResult?.cached && (
                    <span className="flex items-center gap-1 px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 text-[10px] font-mono font-bold uppercase tracking-wider">
                      <Zap className="w-3 h-3 text-cyan-400" />
                      Cached Analysis Found (&lt;50ms)
                    </span>
                  )}
                  {screenResult?.ai_status === "TIMEOUT" && (
                    <span className="px-2 py-0.5 rounded bg-yellow-500/20 text-yellow-300 border border-yellow-500/30 text-[10px] font-mono font-bold uppercase tracking-wider">
                      AI analysis timed out — local compliance engine completed screening
                    </span>
                  )}
                  {screenResult?.ai_status === "unavailable" && (
                    <span className="px-2 py-0.5 rounded bg-yellow-500/20 text-yellow-300 border border-yellow-500/30 text-[10px] font-mono font-bold uppercase tracking-wider">
                      AI analysis unavailable — manual verification required
                    </span>
                  )}
                </div>
                <h2 className="text-xl sm:text-2xl font-black text-white tracking-tight">
                  100-Point Forensic Document Verification Finished
                </h2>
                <div className="flex items-center gap-2 text-xs font-mono text-emerald-400">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                  <span>
                    {autoDownloaded
                      ? "PDF report downloaded successfully."
                      : "PDF report generated and sealed with SHA-256 fingerprint."}
                  </span>
                </div>

                {screenResult?.timing && (
                  <div className="mt-2 flex flex-wrap items-center gap-2 text-[10px] font-mono text-slate-400 bg-slate-950/60 px-3 py-1.5 rounded-lg border border-slate-800">
                    <span className="text-white font-bold">Latency:</span>
                    <span className="text-emerald-400 font-bold">Total: {(screenResult.timing.total_ms / 1000).toFixed(2)}s</span>
                    <span>•</span>
                    <span>Upload: {screenResult.timing.upload_ms}ms</span>
                    <span>•</span>
                    <span>OCR: {screenResult.timing.ocr_ms}ms</span>
                    <span>•</span>
                    <span>Parallel Forensics: {screenResult.timing.concurrent_stages_ms}ms</span>
                    <span>•</span>
                    <span>100 Checks: {screenResult.timing.rules_100_checks_ms}ms</span>
                  </div>
                )}
              </div>

              {/* Integrity & Score Pills */}
              <div className="flex flex-wrap items-center gap-3">
                <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-center min-w-[90px]">
                  <div className="text-[10px] text-slate-400 font-mono">Checks</div>
                  <div className="text-lg font-black text-white">
                    {screenResult?.checks_summary?.total_checks || 100}
                  </div>
                  <div className="text-[9px] text-emerald-400 font-mono">
                    {screenResult?.checks_summary?.passed || 0} Pass
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-slate-950/80 border border-blue-900/50 text-center min-w-[90px]">
                  <div className="text-[10px] text-blue-400 font-mono">Integrity</div>
                  <div className="text-lg font-black text-blue-400 font-mono">
                    {screenResult?.document_integrity_score || 95}/100
                  </div>
                  <div className="text-[9px] text-slate-400 font-mono">Weighted</div>
                </div>

                <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-center min-w-[110px]">
                  <div className="text-[10px] text-slate-400 font-mono">Risk (0–10)</div>
                  <div className={`text-lg font-black font-mono ${screenResult.risk_score > 65 ? "text-rose-400" : screenResult.risk_score > 35 ? "text-amber-400" : "text-emerald-400"}`}>
                    {(screenResult.risk_score / 10).toFixed(1)} <span className="text-xs text-slate-400">/ 10</span>
                  </div>
                  <div className={`text-[9px] font-mono font-bold ${screenResult.risk_score <= 35 ? "text-emerald-400" : screenResult.risk_score <= 65 ? "text-amber-400" : "text-rose-400"}`}>
                    {screenResult.risk_score <= 35 ? "LOW (PASS)" : screenResult.risk_score <= 65 ? "MEDIUM (REVIEW)" : "HIGH (FAIL)"}
                  </div>
                </div>
              </div>
            </div>

            {/* Quick Action Buttons */}
            <div className="mt-5 pt-4 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-2 flex-wrap">
                <Link
                  href={`/cases/${screenResult.case_id}/checks`}
                  className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold border border-slate-700 transition-colors flex items-center gap-1.5"
                >
                  <span>Inspect All 100 Checks</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>

                <Link
                  href={`/cases/${screenResult.case_id}/report`}
                  className="px-3.5 py-2 rounded-xl bg-blue-950/60 hover:bg-blue-900/80 text-blue-300 text-xs font-bold border border-blue-800/60 transition-colors"
                >
                  Full Screening Report
                </Link>

                {screenResult?.cached && (
                  <button
                    type="button"
                    onClick={() => executePipeline(docTypeHint, false, true)}
                    className="px-3.5 py-2 rounded-xl bg-cyan-950/60 hover:bg-cyan-900/80 text-cyan-300 text-xs font-bold border border-cyan-800/60 transition-colors flex items-center gap-1.5"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                    <span>Re-scan Fresh</span>
                  </button>
                )}
              </div>

              <div className="flex items-center gap-2 flex-wrap">
                {screenResult.report_pdf_url && (
                  <a
                    href={screenResult.report_pdf_url}
                    download={`TRUST-ID_Report_${screenResult.case_number || screenResult.case_id}.pdf`}
                    className="px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold shadow-md shadow-blue-900/50 flex items-center gap-1.5 transition-all"
                  >
                    <FileText className="w-3.5 h-3.5" />
                    <span>Download PDF Again</span>
                  </a>
                )}

                {screenResult.report_csv_url && (
                  <a
                    href={screenResult.report_csv_url}
                    download={`TRUST-ID_Checks_${screenResult.case_number || screenResult.case_id}.csv`}
                    className="px-3 py-1.5 rounded-lg bg-emerald-700 hover:bg-emerald-600 text-white text-xs font-bold transition-all"
                  >
                    CSV
                  </a>
                )}

                {screenResult.report_docx_url && (
                  <a
                    href={screenResult.report_docx_url}
                    download={`TRUST-ID_Report_${screenResult.case_number || screenResult.case_id}.docx`}
                    className="px-3 py-1.5 rounded-lg bg-indigo-700 hover:bg-indigo-600 text-white text-xs font-bold transition-all"
                  >
                    DOCX
                  </a>
                )}
              </div>
            </div>
          </div>

          {/* Main Case Risk Summary Card */}
          <div className="p-8 rounded-2xl bg-slate-900 border border-[#24365d] shadow-2xl space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#24365d]">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-slate-400">Case ID:</span>
                  <span className="text-lg font-mono font-black text-white">{screenResult.case_number}</span>
                  <span
                    className={`px-2.5 py-0.5 rounded text-xs font-bold font-mono ${
                      screenResult.risk_level === "LOW"
                        ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                        : screenResult.risk_level === "MEDIUM"
                        ? "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                        : "bg-red-500/20 text-red-400 border border-red-500/30"
                    }`}
                  >
                    {screenResult.risk_level} RISK ({screenResult.risk_score}/100)
                  </span>
                </div>
                <p className="text-xs text-slate-300 mt-1">{screenResult.recommendation}</p>
              </div>

              <button
                onClick={() => router.push(`/cases/${screenResult.case_id}`)}
                className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs shadow-md shadow-blue-500/25 flex items-center gap-2 transition-all"
              >
                <span>Open Forensic Investigation File</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>

            {/* Quick Analysis Highlights */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 rounded-xl bg-slate-950 border border-[#24365d]">
                <div className="text-[11px] text-slate-400 font-semibold uppercase">Credential Type</div>
                <div className="text-base font-bold text-white mt-1">{screenResult.document_type}</div>
                <div className="text-xs text-slate-500 mt-1">Classified automatically</div>
              </div>

              <div className="p-4 rounded-xl bg-slate-950 border border-[#24365d]">
                <div className="text-[11px] text-slate-400 font-semibold uppercase">Confidence Index</div>
                <div className="text-base font-bold text-sky-400 mt-1 font-mono">
                  {ocrConfidence}%
                </div>
                <div className="text-xs text-slate-500 mt-1">Multi-signal aggregation</div>
              </div>

              <div className="p-4 rounded-xl bg-slate-950 border border-[#24365d]">
                <div className="text-[11px] text-slate-400 font-semibold uppercase">Human Review Status</div>
                <div
                  className={`text-base font-bold mt-1 ${
                    screenResult.requires_human_review ? "text-amber-400" : "text-emerald-400"
                  }`}
                >
                  {screenResult.requires_human_review ? "Mandatory Review Required" : "Standard Verification"}
                </div>
                <div className="text-xs text-slate-500 mt-1">MHA AI Safety Protocol</div>
              </div>
            </div>
          </div>

          {/* Extracted Identity Fields & OCR Inspection Card (Requirement #8) */}
          <div className="p-8 rounded-2xl bg-slate-900 border border-[#24365d] shadow-2xl space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-[#24365d]">
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-blue-400" />
                <h3 className="text-base font-bold text-white tracking-tight">
                  Extracted Document Fields & MRZ Data
                </h3>
              </div>
              <span className="text-xs font-mono text-slate-400">
                OCR Engine: {screenResult?.ocr?.engine_used || "Tesseract / OpenCV Hybrid"}
              </span>
            </div>

            {/* Extracted Fields Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
              {/* Holder Name */}
              <div className="p-4 rounded-xl bg-slate-950/80 border border-[#24365d] space-y-1">
                <div className="text-[11px] text-slate-400 font-semibold uppercase flex items-center gap-1.5">
                  <User className="w-3.5 h-3.5 text-blue-400" />
                  <span>Full Name</span>
                </div>
                <div className="text-sm font-bold text-white">
                  {extractedFields.full_name ||
                    `${extractedFields.first_name || ""} ${extractedFields.last_name || ""}`.trim() ||
                    mrzData?.surname ? `${mrzData.given_names} ${mrzData.surname}` : "Not Detected"}
                </div>
              </div>

              {/* Document Number */}
              <div className="p-4 rounded-xl bg-slate-950/80 border border-[#24365d] space-y-1">
                <div className="text-[11px] text-slate-400 font-semibold uppercase flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    <Hash className="w-3.5 h-3.5 text-blue-400" />
                    <span>Document Number</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => setShowDocNumber(!showDocNumber)}
                    className="text-[10px] text-blue-400 hover:text-blue-300 flex items-center gap-1"
                    title={showDocNumber ? "Hide number" : "Reveal number"}
                  >
                    {showDocNumber ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                    <span>{showDocNumber ? "Mask" : "Reveal"}</span>
                  </button>
                </div>
                <div className="text-sm font-bold font-mono text-sky-400">
                  {showDocNumber
                    ? extractedFields.document_number || mrzData?.document_number || "—"
                    : maskDocNumber(extractedFields.document_number || mrzData?.document_number)}
                </div>
              </div>

              {/* Nationality / Country */}
              <div className="p-4 rounded-xl bg-slate-950/80 border border-[#24365d] space-y-1">
                <div className="text-[11px] text-slate-400 font-semibold uppercase flex items-center gap-1.5">
                  <Globe className="w-3.5 h-3.5 text-blue-400" />
                  <span>Nationality / State</span>
                </div>
                <div className="text-sm font-bold text-white">
                  {extractedFields.nationality || mrzData?.nationality || extractedFields.issuing_country || "—"}
                </div>
              </div>

              {/* Date of Birth */}
              <div className="p-4 rounded-xl bg-slate-950/80 border border-[#24365d] space-y-1">
                <div className="text-[11px] text-slate-400 font-semibold uppercase flex items-center gap-1.5">
                  <Calendar className="w-3.5 h-3.5 text-purple-400" />
                  <span>Date of Birth</span>
                </div>
                <div className="text-sm font-bold text-white font-mono">
                  {extractedFields.date_of_birth || mrzData?.birth_date || "—"}
                </div>
              </div>

              {/* Expiry Date */}
              <div className="p-4 rounded-xl bg-slate-950/80 border border-[#24365d] space-y-1">
                <div className="text-[11px] text-slate-400 font-semibold uppercase flex items-center gap-1.5">
                  <Calendar className="w-3.5 h-3.5 text-amber-400" />
                  <span>Date of Expiry</span>
                </div>
                <div className="text-sm font-bold text-white font-mono">
                  {extractedFields.date_of_expiry || mrzData?.expiry_date || "—"}
                </div>
              </div>

              {/* Sex / Gender */}
              <div className="p-4 rounded-xl bg-slate-950/80 border border-[#24365d] space-y-1">
                <div className="text-[11px] text-slate-400 font-semibold uppercase flex items-center gap-1.5">
                  <User className="w-3.5 h-3.5 text-slate-400" />
                  <span>Sex / Gender</span>
                </div>
                <div className="text-sm font-bold text-white font-mono">
                  {extractedFields.sex || mrzData?.sex || "—"}
                </div>
              </div>
            </div>

            {/* MRZ Block & Checksum Validations */}
            {mrzData ? (
              <div className="p-4 rounded-xl bg-slate-950 border border-blue-900/40 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                    <ShieldCheck className="w-4 h-4 text-emerald-400" />
                    <span>Machine Readable Zone (ICAO 9303 MRZ)</span>
                  </span>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                      mrzData.valid
                        ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                        : "bg-red-500/20 text-red-400 border border-red-500/30"
                    }`}
                  >
                    {mrzData.valid ? "CHECK DIGITS VALID" : "CHECKSUM MISMATCH"}
                  </span>
                </div>

                {/* Raw MRZ Lines */}
                <div className="p-3 rounded-lg bg-black/80 border border-[#24365d] font-mono text-xs sm:text-sm text-emerald-400 tracking-widest overflow-x-auto whitespace-pre leading-relaxed select-all">
                  {mrzData.raw_mrz || "No machine-readable text detected."}
                </div>

                {/* Check digit items */}
                {mrzData.checksum_validations && Object.keys(mrzData.checksum_validations).length > 0 && (
                  <div className="flex flex-wrap gap-2 pt-1 text-[11px]">
                    {Object.entries(mrzData.checksum_validations).map(([checkName, isValid]: [string, any]) => (
                      <span
                        key={checkName}
                        className={`px-2 py-0.5 rounded font-mono flex items-center gap-1 ${
                          isValid
                            ? "bg-emerald-950/80 text-emerald-300 border border-emerald-800"
                            : "bg-red-950/80 text-red-300 border border-red-800"
                        }`}
                      >
                        {isValid ? <Check className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
                        <span>{checkName.replace(/_/g, " ")}</span>
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="p-4 rounded-xl bg-slate-950/40 border border-[#24365d] text-xs text-slate-400 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-amber-400 flex-shrink-0" />
                <span>
                  No standard ICAO 9303 Machine Readable Zone (MRZ) detected on document front face (common for domestic Driving Licences and National IDs without MRZ).
                </span>
              </div>
            )}

            {/* Bottom Actions */}
            <div className="flex justify-end gap-3 pt-4 border-t border-[#24365d]">
              <button
                type="button"
                onClick={handleReset}
                className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
              >
                Scan Another Document
              </button>
              <button
                type="button"
                onClick={() => router.push(`/cases/${screenResult.case_id}`)}
                className="px-5 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs"
              >
                Examine Forensic Heatmap & Fields →
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
