"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Shield,
  Layers,
  Cpu,
  Lock,
  Database,
  Eye,
  CheckCircle2,
  FileCheck,
  Server,
  ArrowDown,
  ArrowRight,
  Sparkles,
  Binary,
  Fingerprint,
  Workflow,
  Search,
  AlertOctagon,
  Scale
} from "lucide-react";

export default function ArchitecturePage() {
  const [activeTab, setActiveTab] = useState<"pipeline" | "cybersecurity" | "layers">("pipeline");

  return (
    <div className="space-y-10 max-w-7xl mx-auto pb-20">
      {/* Top Header */}
      <div>
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/30 text-blue-400 text-xs font-mono mb-3">
          <Layers className="w-3.5 h-3.5" />
          Technical Blueprint & SIH Alignment
        </div>
        <h1 className="text-3xl font-bold tracking-tight text-slate-100">
          TRUST-ID System & Security Architecture
        </h1>
        <p className="text-sm text-slate-400 mt-2 max-w-3xl leading-relaxed">
          Comprehensive technical blueprint for Problem Statement <strong className="text-slate-200">SIH26188: AI-Based Fake Identity & Document Screening System</strong>. Demonstrates our 5-layer verification pipeline, explainable multi-signal fusion, and tamper-evident SHA-256 cryptographic audit chain.
        </p>

        {/* View Switcher Tabs */}
        <div className="flex items-center gap-2 mt-6 border-b border-slate-800 pb-3">
          <button
            onClick={() => setActiveTab("pipeline")}
            className={`px-4 py-2 rounded-lg text-xs font-semibold transition-colors flex items-center gap-2 ${
              activeTab === "pipeline"
                ? "bg-blue-600 text-white shadow-lg shadow-blue-500/20"
                : "bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800"
            }`}
          >
            <Workflow className="w-4 h-4" />
            End-to-End Processing Pipeline
          </button>
          <button
            onClick={() => setActiveTab("layers")}
            className={`px-4 py-2 rounded-lg text-xs font-semibold transition-colors flex items-center gap-2 ${
              activeTab === "layers"
                ? "bg-blue-600 text-white shadow-lg shadow-blue-500/20"
                : "bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800"
            }`}
          >
            <Layers className="w-4 h-4" />
            5-Layer Verification Model
          </button>
          <button
            onClick={() => setActiveTab("cybersecurity")}
            className={`px-4 py-2 rounded-lg text-xs font-semibold transition-colors flex items-center gap-2 ${
              activeTab === "cybersecurity"
                ? "bg-blue-600 text-white shadow-lg shadow-blue-500/20"
                : "bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800"
            }`}
          >
            <Lock className="w-4 h-4" />
            Cybersecurity & Defense-in-Depth
          </button>
        </div>
      </div>

      {/* TAB 1: PIPELINE */}
      {activeTab === "pipeline" && (
        <div className="space-y-6">
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 md:p-8">
            <h2 className="text-lg font-semibold text-slate-100 mb-6 flex items-center gap-2">
              <Workflow className="w-5 h-5 text-blue-400" />
              10-Stage Synchronous Screening Orchestration Flow
            </h2>

            {/* Pipeline Step Cards Flow */}
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4 relative">
              {[
                { step: "01", name: "Document Ingestion", desc: "SHA-256 hash calculation, MIME type validation, storage persistence", icon: FileCheck },
                { step: "02", name: "Image Quality Gate", desc: "Laplacian blur, specular glare, contrast & ISO resolution check", icon: Search },
                { step: "03", name: "Classification", desc: "Aspect ratio analysis, keyword extraction, document layout matching", icon: Layers },
                { step: "04", name: "OCR & MRZ Extraction", desc: "ICAO 9303 TD1/TD3 parser, 7-3-1 check digit validation", icon: Binary },
                { step: "05", name: "Field Rule Validation", desc: "Chronological sanity checks (DOB < Issue < Expiry), format regex", icon: CheckCircle2 },
              ].map((s, i) => (
                <div key={i} className="bg-slate-950/80 border border-slate-800/80 rounded-xl p-4 flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-[11px] font-mono text-blue-400 font-bold bg-blue-950/50 px-2 py-0.5 rounded border border-blue-800/40">
                        STAGE {s.step}
                      </span>
                      <s.icon className="w-4 h-4 text-slate-500" />
                    </div>
                    <h3 className="text-xs font-semibold text-slate-200 mb-1">{s.name}</h3>
                    <p className="text-[11px] text-slate-400 leading-relaxed">{s.desc}</p>
                  </div>
                </div>
              ))}
            </div>

            <div className="flex justify-center my-4">
              <div className="px-4 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/30 text-blue-400 text-xs font-mono inline-flex items-center gap-2">
                <ArrowDown className="w-3.5 h-3.5" />
                Parallel Forensic & Biometric Extraction
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-5 gap-4 relative">
              {[
                { step: "06", name: "Visual Forensics", desc: "Error Level Analysis (ELA 95%), localized noise variance, ELA heatmap", icon: Eye },
                { step: "07", name: "1:1 Biometric Match", desc: "Portrait crop vs presented live face, geometric alignment, distance metric", icon: Fingerprint },
                { step: "08", name: "Record Verification", desc: "Simulated Central Issuer Registry check, consular validity confirmation", icon: Database },
                { step: "09", name: "Multi-Signal Fusion", desc: "Weighted risk score calculation (0–100) with safety floor triggers", icon: Scale },
                { step: "10", name: "Explainable XAI & Ledger", desc: "Factor attribution, recommendations, cryptographic SHA-256 block creation", icon: Shield },
              ].map((s, i) => (
                <div key={i} className="bg-slate-950/80 border border-slate-800/80 rounded-xl p-4 flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-[11px] font-mono text-purple-400 font-bold bg-purple-950/50 px-2 py-0.5 rounded border border-purple-800/40">
                        STAGE {s.step}
                      </span>
                      <s.icon className="w-4 h-4 text-slate-500" />
                    </div>
                    <h3 className="text-xs font-semibold text-slate-200 mb-1">{s.name}</h3>
                    <p className="text-[11px] text-slate-400 leading-relaxed">{s.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Interactive Flow Block Diagram */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6">
            <h3 className="text-sm font-semibold text-slate-200 mb-4 flex items-center gap-2">
              <Server className="w-4 h-4 text-blue-400" />
              Runtime Subsystem Topology
            </h3>

            <div className="p-6 bg-slate-950 rounded-xl border border-slate-800/80 font-mono text-xs text-slate-300 leading-loose overflow-x-auto">
              <pre className="text-blue-300">
{`+---------------------------------------------------------------------------------------------------+
|                                 TRUST-ID CLIENT INTERFACE (Next.js 15)                            |
|             Screening Portal  |  Forensic Viewer  |  Verifier Dashboard  |  Audit Explorer        |
+-------------------------------------------------+-------------------------------------------------+
                                                  | HTTPS / REST / JWT
                                                  v
+-------------------------------------------------+-------------------------------------------------+
|                                 FASTAPI API GATEWAY & ORCHESTRATOR                                |
|             Auth & RBAC  |  File Sanitization  |  Async Background Tasks  |  OpenAPI Docs         |
+-------------------------------------------------+-------------------------------------------------+
                                                  |
         +----------------------------------------+----------------------------------------+
         |                                        |                                        |
         v                                        v                                        v
+-----------------------+              +-----------------------+              +-----------------------+
|  DOCUMENT RECOGNITION |              |   VISUAL FORENSICS    |              | BIOMETRIC & REGISTRY  |
| - Layout Classifier   |              | - ELA 95% Analyzer    |              | - Face Cascade Match  |
| - Paddle/EasyOCR Hook |              | - Noise Grid Variance |              | - 1:1 Cosine Distance |
| - ICAO MRZ 7-3-1 Math |              | - Sobel Edge Detector |              | - Mock Central Record |
| - Chronological Rules |              | - Jet Heatmap Engine  |              | - Consular Lookup API |
+-----------------------+              +-----------------------+              +-----------------------+
         |                                        |                                        |
         +----------------------------------------+----------------------------------------+
                                                  |
                                                  v
+-------------------------------------------------+-------------------------------------------------+
|                                  MULTI-SIGNAL RISK FUSION ENGINE                                  |
|   Weights: Validation 15% | Forensics 25% | Biometrics 20% | Record 20% | OCR 10% | Quality 10%   |
|   Safety Floors: Tampering Detected >= 65 | Document Expired >= 65 | Biometric Mismatch >= 70     |
+-------------------------------------------------+-------------------------------------------------+
                                                  |
                                                  v
+-------------------------------------------------+-------------------------------------------------+
|                         EXPLAINABILITY (XAI) & AUDIT LEDGER SUBSYSTEM                             |
|  - Factor Impact Scoring  |  Positive Signal Extraction  |  Tamper-Evident SHA-256 Hash Chain     |
+-------------------------------------------------+-------------------------------------------------+
                                                  |
                         +------------------------+------------------------+
                         |                                                 |
                         v                                                 v
+-------------------------------------------------+       +-----------------------------------------+
|        SQLAlchemy Relational Persistence        |       |        Local / S3 Secure Object Storage |
|  Cases, Documents, OCR, Validations, Decisions  |       |  Original Document Scans & ELA Heatmaps |
+-------------------------------------------------+       +-----------------------------------------+`}
              </pre>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: 5-LAYER MODEL */}
      {activeTab === "layers" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            {[
              {
                num: "1",
                name: "Document Layer",
                focus: "Physical Integrity & Layout",
                tech: "OpenCV, ISO Aspect Check, Bounding Box Heuristics",
                checks: ["Standard dimensional compliance", "Guilloche security pattern presence", "Micro-text layout conformity", "Resolution threshold gating (>150 DPI)"]
              },
              {
                num: "2",
                name: "Forensics Layer",
                focus: "Digital Tampering & Splicing",
                tech: "Error Level Analysis (ELA), Local Noise Variance, Inpainting Detection",
                checks: ["Differential compression artifact detection", "Noise distribution across 64x64 grid", "Discontinuous boundary edge gradients", "Color-mapped suspicious region localization"]
              },
              {
                num: "3",
                name: "Identity Layer",
                focus: "Biometric 1:1 Verification",
                tech: "Face Detection, Geometrical Alignment, Cosine Similarity",
                checks: ["Document portrait extraction & crop", "Presented live camera image alignment", "Feature distance computation", "Non-punitive review threshold categorization"]
              },
              {
                num: "4",
                name: "Records Layer",
                focus: "Issuer Cross-Verification",
                tech: "Modular Verification Provider Adapter Pattern",
                checks: ["Issuing country code authorization", "Central travel document database lookup", "Stolen / Lost Document (SLTD) mock check", "Simulated demo registry integration"]
              },
              {
                num: "5",
                name: "Risk Engine",
                focus: "Explainable Risk Fusion",
                tech: "Multi-Signal Weighted Aggregator + Hard Safety Floors",
                checks: ["0–100 normalized risk score calculation", "Low / Medium / High tier classification", "Mandatory human review routing", "Positive vs risk factor attribution (XAI)"]
              }
            ].map((layer, idx) => (
              <div key={idx} className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 flex flex-col justify-between">
                <div>
                  <div className="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/30 text-blue-400 font-mono font-bold flex items-center justify-center text-sm mb-3">
                    L{layer.num}
                  </div>
                  <h3 className="font-semibold text-slate-100 text-sm mb-1">{layer.name}</h3>
                  <div className="text-[11px] text-blue-400 font-mono mb-2">{layer.focus}</div>
                  <div className="text-[11px] text-slate-400 bg-slate-950/60 border border-slate-800/80 rounded p-2 mb-3">
                    <strong className="text-slate-300">Stack:</strong> {layer.tech}
                  </div>
                  <ul className="space-y-1.5">
                    {layer.checks.map((c, i) => (
                      <li key={i} className="flex items-start gap-1.5 text-[11px] text-slate-400">
                        <CheckCircle2 className="w-3 h-3 text-slate-500 shrink-0 mt-0.5" />
                        <span>{c}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            ))}
          </div>

          {/* Alignment to SIH Reference Document */}
          <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-6">
            <h3 className="text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-amber-400" />
              Direct Alignment with SIH 2026 Reference Presentation (Slide 3 Flowchart)
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed mb-4">
              The SIH 2026 reference presentation requires support for <strong>Passports, Visas, National ID cards, Driving Licences, Permits, and Travel Authorizations</strong> across the operational pipeline: <code>SCAN → DETECT → VALIDATE → SCORE → REVIEW</code>.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-5 gap-3 text-xs">
              <div className="bg-slate-950/60 border border-slate-800 rounded p-3">
                <span className="font-mono text-blue-400 font-bold block mb-1">1. SCAN</span>
                High-resolution drag-and-drop intake supporting front scan, reverse side, and live presenter webcam feed.
              </div>
              <div className="bg-slate-950/60 border border-slate-800 rounded p-3">
                <span className="font-mono text-blue-400 font-bold block mb-1">2. DETECT</span>
                OCR field capture + ICAO 9303 MRZ extraction + automated document type categorization.
              </div>
              <div className="bg-slate-950/60 border border-slate-800 rounded p-3">
                <span className="font-mono text-blue-400 font-bold block mb-1">3. VALIDATE</span>
                Parallel visual forensic inspection (ELA, noise grid) + rule consistency checks + biometric verification.
              </div>
              <div className="bg-slate-950/60 border border-slate-800 rounded p-3">
                <span className="font-mono text-blue-400 font-bold block mb-1">4. SCORE</span>
                Deterministic multi-signal risk fusion producing normalized 0–100 score with explainability factor breakdown.
              </div>
              <div className="bg-slate-950/60 border border-slate-800 rounded p-3">
                <span className="font-mono text-blue-400 font-bold block mb-1">5. REVIEW</span>
                Human-in-the-loop verification workstation with mandatory justification rationale for high-risk flags.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: CYBERSECURITY */}
      {activeTab === "cybersecurity" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5">
              <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center justify-center mb-3">
                <Lock className="w-4 h-4" />
              </div>
              <h3 className="font-semibold text-slate-100 text-sm mb-1">
                Zero-Trust Authentication & RBAC
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed mb-3">
                Cryptographic JSON Web Tokens (JWT) signed via HMAC-SHA256 with granular Role-Based Access Control enforcing strict separation of duties:
              </p>
              <ul className="space-y-1.5 text-[11px] text-slate-400 font-mono">
                <li className="flex items-center gap-2">
                  <span className="text-emerald-400 font-bold">• ADMIN:</span> System thresholds & weights
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-blue-400 font-bold">• VERIFIER:</span> Document screening & adjudication
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-purple-400 font-bold">• INVESTIGATOR:</span> Audit chain & forensic drilldown
                </li>
              </ul>
            </div>

            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5">
              <div className="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/30 text-blue-400 flex items-center justify-center mb-3">
                <Shield className="w-4 h-4" />
              </div>
              <h3 className="font-semibold text-slate-100 text-sm mb-1">
                Tamper-Evident SHA-256 Audit Ledger
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed mb-3">
                Every critical event (case creation, forensic analysis, biometric match, human verification decision) is permanently committed to an immutable cryptographic hash chain:
              </p>
              <div className="p-2.5 bg-slate-950 rounded border border-slate-800 text-[10px] font-mono text-slate-300">
                <code>hash_i = SHA256(case_id + actor_id + action + canonical_iso_ts + hash_(i-1))</code>
              </div>
              <p className="text-[11px] text-slate-500 mt-2">
                Enables instant mathematical verification of audit integrity. Any retrospective database modification immediately invalidates subsequent block hashes.
              </p>
            </div>

            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5">
              <div className="w-8 h-8 rounded-lg bg-purple-500/10 border border-purple-500/30 text-purple-400 flex items-center justify-center mb-3">
                <Scale className="w-4 h-4" />
              </div>
              <h3 className="font-semibold text-slate-100 text-sm mb-1">
                AI Safety & Ethical Safeguards
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed mb-3">
                Strict adherence to Government of India AI Ethics & Ministry of Home Affairs security guidelines:
              </p>
              <ul className="space-y-1.5 text-[11px] text-slate-400">
                <li className="flex items-start gap-1.5">
                  <span className="text-amber-400 font-bold">1.</span>
                  <span><strong>No Autonomous Punitive Decisions:</strong> AI outputs risk indicators only; human verifier retains final legal authority.</span>
                </li>
                <li className="flex items-start gap-1.5">
                  <span className="text-amber-400 font-bold">2.</span>
                  <span><strong>Substantive Rationale Enforcement:</strong> High-risk cases mandate written justification from the human officer.</span>
                </li>
                <li className="flex items-start gap-1.5">
                  <span className="text-amber-400 font-bold">3.</span>
                  <span><strong>Quality Gating:</strong> Degraded/blurry images are marked for re-upload rather than falsely branded as fraudulent.</span>
                </li>
              </ul>
            </div>
          </div>

          {/* Defense in depth diagram */}
          <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-6">
            <h3 className="text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
              <AlertOctagon className="w-4 h-4 text-blue-400" />
              Security Perimeter & Trust Boundaries
            </h3>
            <div className="p-4 bg-slate-950 rounded-lg border border-slate-800/80 font-mono text-[11px] text-slate-400 space-y-2">
              <div><strong className="text-emerald-400">[Perimeter 1 - Ingestion]</strong> Strict multipart MIME validation, 15MB file size limit, sanitized UUID filenames, SHA-256 payload integrity check.</div>
              <div><strong className="text-blue-400">[Perimeter 2 - Execution]</strong> Memory-safe image decoding via OpenCV/Pillow, CPU-bounded Laplacian variance analysis, no external shell execution.</div>
              <div><strong className="text-purple-400">[Perimeter 3 - Persistence]</strong> Metadata stored in relational tables with foreign keys and indexes; document scans segregated into secure storage with strict access tokens.</div>
              <div><strong className="text-amber-400">[Perimeter 4 - Auditability]</strong> Write-once cryptographic event ledger ensuring complete evidentiary non-repudiation in legal proceedings.</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
