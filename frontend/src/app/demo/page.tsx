"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Play,
  Loader2,
  ArrowRight,
  Sparkles,
  Info,
  CheckCircle2,
  FileText,
  Scan,
  RefreshCw,
  Eye,
  Camera,
  Layers,
  Database
} from "lucide-react";
import { runDemoPreset } from "@/lib/api";

interface DemoCase {
  id: string;
  title: string;
  docType: string;
  riskTier: "LOW" | "MEDIUM" | "HIGH";
  description: string;
  attackVector: string;
  expectedSignals: string[];
  hasLivePerson: boolean;
}

const DEMO_CASES: DemoCase[] = [
  {
    id: "CASE-001",
    title: "Genuine International Passport",
    docType: "PASSPORT",
    riskTier: "LOW",
    description: "Standard compliant ICAO Document 9303 TD3 machine-readable travel document. Authentic guilloche pattern, clean compression, matching MRZ checksums.",
    attackVector: "None (Benchmark Control)",
    expectedSignals: ["MRZ 7-3-1 Checksum Passed", "No ELA Anomalies Detected", "Issuer Record Confirmed in Mock Registry", "Eligible for Standard Verification"],
    hasLivePerson: true
  },
  {
    id: "CASE-002",
    title: "National Identity Card (Minor Glare)",
    docType: "NATIONAL_ID",
    riskTier: "MEDIUM",
    description: "Authentic national identity document captured under sub-optimal lighting conditions with mild optical specular reflection.",
    attackVector: "Surface Reflection / Optical Glare",
    expectedSignals: ["Image Quality Score: 78 (Minor Glare)", "OCR Confidence: 89%", "Visual Validation Passed", "Human Review Recommended"],
    hasLivePerson: true
  },
  {
    id: "CASE-003",
    title: "Forged Schengen Visa (Spliced Stamps)",
    docType: "VISA",
    riskTier: "HIGH",
    description: "Counterfeit travel visa bearing fabricated consular stamps, invalid issuing authority code, and unverified central registration record.",
    attackVector: "Consular Stamp Forgery & Unregistered Serial",
    expectedSignals: ["Central Record: NOT FOUND", "Issuer Authority Check Failed", "High Risk Anomaly Alert", "Mandatory Human Review Enforced"],
    hasLivePerson: false
  },
  {
    id: "CASE-004",
    title: "Expired Travel Passport",
    docType: "PASSPORT",
    riskTier: "HIGH",
    description: "Valid physical format and authentic security printing, but past statutory expiration date by more than 18 months.",
    attackVector: "Expired Credential Presentation",
    expectedSignals: ["Expiry Validation Check Failed", "Chronological Rule Violation", "Safety Score Floor Activated", "Mandatory Human Review Enforced"],
    hasLivePerson: true
  },
  {
    id: "CASE-005",
    title: "Spliced Portrait Photo Replacement",
    docType: "PASSPORT",
    riskTier: "HIGH",
    description: "Photographic identity card where original subject portrait has been replaced with a digitally spliced face patch, creating localized ELA and noise discontinuity.",
    attackVector: "Digital Image Splicing / Photo Substitution",
    expectedSignals: ["ELA Compression Discontinuity (>85%)", "Local Noise Variance Spike", "Suspicious Region Bounding Box Located", "Forensic Heatmap Alert"],
    hasLivePerson: true
  },
  {
    id: "CASE-006",
    title: "Altered Date of Birth & Issue Date",
    docType: "DRIVING_LICENSE",
    riskTier: "HIGH",
    description: "Driving license with digitally altered typography in the Date of Birth field to artificially change driver eligibility age.",
    attackVector: "Typography Inpainting & OCR Inconsistency",
    expectedSignals: ["Possible Text Manipulation Detected", "Edge Inconsistency in Text Boundary", "Visual vs Rule Mismatch", "Evidence Logged to Hash Chain"],
    hasLivePerson: false
  },
  {
    id: "CASE-007",
    title: "Biometric Impersonation / Face Mismatch",
    docType: "PASSPORT",
    riskTier: "HIGH",
    description: "Genuine physical passport presented by an individual whose live camera selfie does not match the document portrait.",
    attackVector: "Imposter Presentation Attack / Identity Fraud",
    expectedSignals: ["Biometric Distance > Threshold", "Similarity: 0.18 (Below 0.60)", "Identity Verification Flagged", "Mandatory Human Review Enforced"],
    hasLivePerson: true
  },
  {
    id: "CASE-008",
    title: "Severe Motion Blur & Low Resolution",
    docType: "PASSPORT",
    riskTier: "MEDIUM",
    description: "Mobile scan affected by severe camera shake and insufficient pixel resolution below the ISO standard for forensic screening.",
    attackVector: "Degraded Image Quality (Unreadable)",
    expectedSignals: ["Quality Score < 40 (Severe Blur)", "Insufficient Quality Safeguard Triggered", "NOT Fraudulently Flagged", "Re-upload Recommended"],
    hasLivePerson: false
  }
];

export default function DemoPage() {
  const router = useRouter();
  const [runningId, setRunningId] = useState<string | null>(null);
  const [executionResult, setExecutionResult] = useState<{
    id: string;
    case_id: string;
    risk_level: string;
    risk_score: number;
  } | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleRunPreset = async (presetId: string) => {
    setRunningId(presetId);
    setExecutionResult(null);
    setErrorMsg(null);

    try {
      const res = await runDemoPreset(presetId);
      setExecutionResult({
        id: presetId,
        case_id: res.case_id,
        risk_level: res.risk_level,
        risk_score: res.risk_score
      });
    } catch (err: unknown) {
      const e = err as Error;
      setErrorMsg(e.message || "Failed to execute synthetic screening demo.");
    } finally {
      setRunningId(null);
    }
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-16">
      {/* Top Banner */}
      <div className="bg-amber-950/40 border border-amber-600/40 rounded-xl p-4 flex items-start gap-3">
        <Info className="w-5 h-5 text-amber-400 mt-0.5 shrink-0" />
        <div className="text-xs text-amber-200/90 leading-relaxed">
          <strong className="text-amber-300 font-semibold uppercase tracking-wider block mb-0.5">
            Synthetic Benchmark Suite — For Hackathon Evaluation Only
          </strong>
          All scenarios execute the <strong>real backend AI pipeline</strong> (Quality Check → Classification → OCR/MRZ → Computer Vision Forensics → Biometric Alignment → Central Registry Adapter → Multi-Signal Risk Engine → SHA-256 Hash Chain). All credentials and names are synthetically generated for privacy compliance.
        </div>
      </div>

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/30 text-blue-400 text-xs font-mono mb-2">
            <Sparkles className="w-3.5 h-3.5" />
            3-Minute Guided SIH Evaluation Flow
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-100">
            Interactive Forensic Test Scenarios
          </h1>
          <p className="text-sm text-slate-400 mt-1 max-w-3xl">
            Select any pre-configured forensic scenario below. The backend orchestrator will ingest the synthetic credential, execute all 10 analysis stages synchronously, and generate a tamper-evident audit trail for your review.
          </p>
        </div>

        <Link
          href="/screen"
          className="inline-flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg text-sm font-medium transition-colors"
        >
          <Scan className="w-4 h-4 text-blue-400" />
          Custom Document Upload
        </Link>
      </div>

      {/* Execution Alert Modal / Toast */}
      {executionResult && (
        <div className="bg-blue-950/50 border border-blue-500/40 rounded-xl p-6 shadow-2xl flex flex-col sm:flex-row items-center justify-between gap-4 animate-in fade-in slide-in-from-top-4">
          <div className="flex items-center gap-4">
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center font-mono font-bold text-lg ${
              executionResult.risk_level === "LOW" ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40" :
              executionResult.risk_level === "MEDIUM" ? "bg-amber-500/20 text-amber-400 border border-amber-500/40" :
              "bg-rose-500/20 text-rose-400 border border-rose-500/40"
            }`}>
              {executionResult.risk_score}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono text-slate-400 uppercase tracking-wider">{executionResult.id} Evaluated</span>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${
                  executionResult.risk_level === "LOW" ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/30" :
                  executionResult.risk_level === "MEDIUM" ? "bg-amber-500/20 text-amber-300 border-amber-500/30" :
                  "bg-rose-500/20 text-rose-300 border-rose-500/30"
                }`}>
                  {executionResult.risk_level} Risk
                </span>
              </div>
              <h3 className="text-base font-semibold text-slate-100 mt-0.5">
                Screening Completed with Tamper-Evident SHA-256 Ledger
              </h3>
            </div>
          </div>

          <div className="flex items-center gap-3 w-full sm:w-auto">
            <button
              onClick={() => router.push(`/cases/${executionResult.case_id}`)}
              className="flex-1 sm:flex-none inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-semibold shadow-lg shadow-blue-500/20 transition-colors"
            >
              Investigate Forensic Case
              <ArrowRight className="w-4 h-4" />
            </button>
            <button
              onClick={() => setExecutionResult(null)}
              className="px-3 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm border border-slate-700"
            >
              Dismiss
            </button>
          </div>
        </div>
      )}

      {errorMsg && (
        <div className="bg-rose-950/40 border border-rose-600/40 rounded-xl p-4 flex items-center gap-3 text-rose-300 text-sm">
          <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Grid of Scenarios */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        {DEMO_CASES.map((item) => {
          const isRunning = runningId === item.id;
          const isCompleted = executionResult?.id === item.id;

          return (
            <div
              key={item.id}
              className={`bg-slate-900/60 border rounded-xl p-5 flex flex-col justify-between transition-all duration-200 hover:border-slate-600 ${
                isCompleted ? "border-blue-500/60 bg-blue-950/20" : "border-slate-800"
              }`}
            >
              <div>
                {/* Header row */}
                <div className="flex items-center justify-between mb-3">
                  <span className="font-mono text-xs font-semibold text-slate-400 bg-slate-800/80 px-2 py-0.5 rounded border border-slate-700">
                    {item.id}
                  </span>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${
                    item.riskTier === "LOW" ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30" :
                    item.riskTier === "MEDIUM" ? "bg-amber-500/10 text-amber-400 border-amber-500/30" :
                    "bg-rose-500/10 text-rose-400 border-rose-500/30"
                  }`}>
                    {item.riskTier} Risk
                  </span>
                </div>

                {/* Title */}
                <h3 className="font-semibold text-slate-100 text-base mb-1.5 leading-snug">
                  {item.title}
                </h3>

                <div className="flex items-center gap-3 text-[11px] text-slate-400 mb-3">
                  <span className="inline-flex items-center gap-1">
                    <FileText className="w-3.5 h-3.5 text-blue-400" />
                    {item.docType}
                  </span>
                  {item.hasLivePerson && (
                    <span className="inline-flex items-center gap-1 text-purple-400">
                      <Camera className="w-3.5 h-3.5" />
                      1:1 Biometrics
                    </span>
                  )}
                </div>

                <p className="text-xs text-slate-400 leading-relaxed mb-4">
                  {item.description}
                </p>

                {/* Attack vector */}
                <div className="mb-4 bg-slate-950/60 border border-slate-800/80 rounded-lg p-2.5">
                  <div className="text-[10px] font-mono uppercase text-slate-500 tracking-wider mb-1">
                    Attack Vector / Condition
                  </div>
                  <div className="text-xs font-medium text-slate-300">
                    {item.attackVector}
                  </div>
                </div>

                {/* Key signals */}
                <div className="space-y-1 mb-5">
                  <div className="text-[10px] font-mono uppercase text-slate-500 tracking-wider mb-1">
                    Target Verification Signals
                  </div>
                  {item.expectedSignals.map((sig, idx) => (
                    <div key={idx} className="flex items-center gap-1.5 text-[11px] text-slate-400">
                      <CheckCircle2 className="w-3 h-3 text-slate-500 shrink-0" />
                      <span className="truncate">{sig}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Action Button */}
              <div className="pt-2">
                {isCompleted ? (
                  <button
                    onClick={() => router.push(`/cases/${executionResult.case_id}`)}
                    className="w-full inline-flex items-center justify-center gap-2 py-2.5 px-3 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold shadow-md shadow-blue-500/20 transition-colors"
                  >
                    <Eye className="w-3.5 h-3.5" />
                    View Case File & Evidence
                  </button>
                ) : (
                  <button
                    onClick={() => handleRunPreset(item.id)}
                    disabled={isRunning || runningId !== null}
                    className="w-full inline-flex items-center justify-center gap-2 py-2.5 px-3 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-200 hover:text-white rounded-lg text-xs font-semibold border border-slate-700 transition-colors"
                  >
                    {isRunning ? (
                      <>
                        <Loader2 className="w-3.5 h-3.5 animate-spin text-blue-400" />
                        Running AI Pipeline...
                      </>
                    ) : (
                      <>
                        <Play className="w-3.5 h-3.5 text-blue-400 fill-blue-400/20" />
                        Run Screening Pipeline
                      </>
                    )}
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
