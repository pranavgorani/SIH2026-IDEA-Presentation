"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  UploadCloud,
  FileCheck,
  Camera,
  Layers,
  ArrowRight,
  AlertCircle,
  CheckCircle2,
  Cpu,
  Scan,
  Shield,
  Eye,
  FileText,
  UserCheck,
} from "lucide-react";
import { api } from "@/lib/api";

const PIPELINE_STEPS = [
  { id: 1, label: "DOCUMENT RECEIVED", icon: UploadCloud, desc: "Computing SHA-256 hash & integrity check" },
  { id: 2, label: "IMAGE QUALITY CHECK", icon: Eye, desc: "Testing blur, glare, contrast & resolution" },
  { id: 3, label: "DOCUMENT CLASSIFICATION", icon: Layers, desc: "Detecting credential layout & ISO aspect" },
  { id: 4, label: "OCR & MRZ EXTRACTION", icon: FileText, desc: "Parsing ICAO 9303 check digits & text" },
  { id: 5, label: "FIELD VALIDATION", icon: FileCheck, desc: "Testing expiry & chronological integrity" },
  { id: 6, label: "VISUAL FORENSICS", icon: Scan, desc: "Running Error Level Analysis (ELA) & noise profiling" },
  { id: 7, label: "IDENTITY VERIFICATION", icon: UserCheck, desc: "1:1 biometric facial portrait comparison" },
  { id: 8, label: "RECORD CROSS-CHECK", icon: Shield, desc: "Consulting central issuing registry (simulated)" },
  { id: 9, label: "MULTI-SIGNAL RISK FUSION", icon: Cpu, desc: "Synthesizing weights into explainable 0–100 score" },
  { id: 10, label: "EXPLAINABLE REPORT & AUDIT", icon: CheckCircle2, desc: "Appending SHA-256 tamper-evident block" },
];

export default function ScreeningPage() {
  const router = useRouter();

  const [frontFile, setFrontFile] = useState<File | null>(null);
  const [backFile, setBackFile] = useState<File | null>(null);
  const [liveFile, setLiveFile] = useState<File | null>(null);
  const [docTypeHint, setDocTypeHint] = useState("AUTO_DETECT");
  const [notes, setNotes] = useState("");

  const [frontPreview, setFrontPreview] = useState<string | null>(null);
  const [livePreview, setLivePreview] = useState<string | null>(null);

  const [isProcessing, setIsProcessing] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [screenResult, setScreenResult] = useState<any>(null);

  const handleFrontSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setFrontFile(file);
      setFrontPreview(URL.createObjectURL(file));
      setError(null);
    }
  };

  const handleLiveSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setLiveFile(file);
      setLivePreview(URL.createObjectURL(file));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!frontFile) {
      setError("Please upload the primary document front image.");
      return;
    }

    setIsProcessing(true);
    setCurrentStep(1);
    setError(null);

    // Simulate stepped pipeline UI progress while request executes
    const interval = setInterval(() => {
      setCurrentStep((prev) => (prev < 9 ? prev + 1 : prev));
    }, 450);

    try {
      const formData = new FormData();
      formData.append("file", frontFile);
      if (backFile) formData.append("back_file", backFile);
      if (liveFile) formData.append("live_person_file", liveFile);
      formData.append("document_type_hint", docTypeHint);
      if (notes) formData.append("notes", notes);

      const res = await api.screenDocument(formData);
      clearInterval(interval);
      setCurrentStep(10);
      setScreenResult(res);
    } catch (err: any) {
      clearInterval(interval);
      setError(err.message || "Document screening failed");
      setIsProcessing(false);
    }
  };

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
          Upload credential scans and optional presenter portraits for instant multi-signal analysis.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-950/40 border border-red-800/60 text-red-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Main Upload / Processing Container */}
      {!isProcessing && !screenResult ? (
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
            {/* Primary Document Upload Area */}
            <div className="md:col-span-7 space-y-4">
              <div className="p-6 rounded-2xl bg-slate-900/90 border border-[#24365d] space-y-4">
                <div className="flex items-center justify-between">
                  <label className="text-sm font-bold text-white flex items-center gap-2">
                    <Scan className="w-4 h-4 text-blue-400" />
                    <span>Primary Document Front Scan *</span>
                  </label>
                  <span className="text-[11px] text-slate-400">PNG, JPG, WEBP, PDF (Max 25MB)</span>
                </div>

                <div className="relative border-2 border-dashed border-[#24365d] hover:border-blue-500/60 rounded-xl p-8 text-center bg-slate-950/40 transition-colors">
                  {frontPreview ? (
                    <div className="space-y-3">
                      <img
                        src={frontPreview}
                        alt="Front Preview"
                        className="max-h-60 mx-auto rounded-lg border border-[#24365d] object-contain shadow-lg"
                      />
                      <div className="text-xs text-emerald-400 font-semibold flex items-center justify-center gap-1">
                        <CheckCircle2 className="w-4 h-4" />
                        <span>Ready: {frontFile?.name}</span>
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <div className="w-12 h-12 rounded-xl bg-blue-600/10 text-blue-400 border border-blue-500/20 flex items-center justify-center mx-auto">
                        <UploadCloud className="w-6 h-6" />
                      </div>
                      <div className="text-xs text-slate-300 font-semibold">
                        Drag and drop credential image, or{" "}
                        <span className="text-blue-400 underline">browse device</span>
                      </div>
                      <p className="text-[11px] text-slate-500">
                        Supports Passports, Visas, National IDs, Driving Licences & Travel Authorizations
                      </p>
                    </div>
                  )}

                  <input
                    type="file"
                    accept="image/*,application/pdf"
                    onChange={handleFrontSelect}
                    className="absolute inset-0 opacity-0 cursor-pointer"
                  />
                </div>

                {/* Optional Back Side */}
                <div className="pt-2">
                  <label className="text-xs font-semibold text-slate-300 block mb-1">
                    Optional Credential Reverse / Back Side
                  </label>
                  <input
                    type="file"
                    accept="image/*,application/pdf"
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

                <div className="relative border border-dashed border-[#24365d] hover:border-purple-500/60 rounded-xl p-4 text-center bg-slate-950/40 transition-colors">
                  {livePreview ? (
                    <div className="space-y-2">
                      <img
                        src={livePreview}
                        alt="Live Portrait"
                        className="max-h-36 mx-auto rounded-lg border border-[#24365d] object-contain"
                      />
                      <div className="text-[11px] text-purple-300 font-semibold">
                        Photo Loaded: {liveFile?.name}
                      </div>
                    </div>
                  ) : (
                    <div className="py-4 space-y-1">
                      <Camera className="w-8 h-8 text-slate-500 mx-auto" />
                      <div className="text-xs text-slate-300 font-semibold">
                        Upload selfie or camera capture
                      </div>
                      <p className="text-[10px] text-slate-500">
                        Enables 1:1 facial biometric matching against document portrait
                      </p>
                    </div>
                  )}

                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleLiveSelect}
                    className="absolute inset-0 opacity-0 cursor-pointer"
                  />
                </div>
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
      ) : isProcessing && !screenResult ? (
        /* Real-Time Processing Pipeline Animation */
        <div className="p-8 rounded-2xl bg-slate-900/95 border border-[#24365d] shadow-2xl space-y-6">
          <div className="text-center space-y-2">
            <div className="w-12 h-12 rounded-xl bg-blue-600/20 text-blue-400 border border-blue-500/30 flex items-center justify-center mx-auto animate-pulse">
              <Cpu className="w-6 h-6 animate-spin" />
            </div>
            <h2 className="text-xl font-bold text-white">AI Screening Pipeline Active</h2>
            <p className="text-xs text-slate-400">
              Executing multi-signal forensic inspection, ICAO check digits & biometric cross-checks...
            </p>
          </div>

          <div className="space-y-3 max-w-xl mx-auto pt-4">
            {PIPELINE_STEPS.map((step) => {
              const Icon = step.icon;
              const isDone = currentStep > step.id;
              const isCurrent = currentStep === step.id;
              return (
                <div
                  key={step.id}
                  className={`p-3 rounded-lg border transition-all flex items-center justify-between text-xs ${
                    isDone
                      ? "bg-slate-950/80 border-emerald-500/30 text-emerald-400"
                      : isCurrent
                      ? "bg-blue-950/40 border-blue-500 text-blue-300 shadow-md shadow-blue-500/10 scale-[1.01]"
                      : "bg-slate-950/20 border-[#1c2c4d] text-slate-500"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon className={`w-4 h-4 ${isCurrent ? "animate-pulse text-blue-400" : ""}`} />
                    <div>
                      <div className="font-bold tracking-wide">
                        {step.id}. {step.label}
                      </div>
                      <div className="text-[10px] text-slate-400">{step.desc}</div>
                    </div>
                  </div>
                  <div>
                    {isDone ? (
                      <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded">
                        DONE
                      </span>
                    ) : isCurrent ? (
                      <div className="w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
                    ) : (
                      <span className="text-[10px] font-mono text-slate-600">PENDING</span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ) : (
        /* Screening Result Summary Card */
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
                {Math.round(screenResult.confidence * 100)}%
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

          <div className="flex justify-end gap-3 pt-4">
            <button
              onClick={() => {
                setScreenResult(null);
                setIsProcessing(false);
                setFrontFile(null);
                setFrontPreview(null);
                setLiveFile(null);
                setLivePreview(null);
              }}
              className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
            >
              Screen Another Document
            </button>
            <button
              onClick={() => router.push(`/cases/${screenResult.case_id}`)}
              className="px-5 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs"
            >
              Examine Forensic Heatmap & Fields →
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
