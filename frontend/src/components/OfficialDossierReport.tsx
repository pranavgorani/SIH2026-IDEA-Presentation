"use client";

import React, { useState } from "react";
import { Printer, Download, FileText, CheckCircle2, AlertTriangle, XCircle, Shield, Copy, Check } from "lucide-react";

export interface DossierReportData {
  caseNumber?: string;
  screeningTime?: string;
  checkpoint?: string;
  officerId?: string;
  decision?: "CLEAR TO ENTER" | "DETAIN / FRAUD ALERT" | "SECONDARY SCRUTINY";
  riskScore?: number;
  totalScreened?: number;
  clearanceRate?: number;
  tamperingIntercepted?: number;
  watchlistApprehensions?: number;
  avgLatency?: string;
  documentSha256?: string;
  resolution?: string;
  traveler: {
    fullName: string;
    documentNo: string;
    nationality: string;
    dob: string;
    gender: string;
    expiryDate: string;
  };
  forensics: {
    mrzStatus: string;
    tamperingAssessment: string;
    biometricMatch: string;
    watchlistStatus: string;
  };
  blockchain: {
    blockIndex: number;
    blockHash: string;
    previousHash: string;
    digitalSignature: string;
  };
  verdictDirective?: string;
  documentImageUrl?: string;
  documentType?: string;
  boundingBoxes?: Array<{
    label: string;
    boxStyle: { top: string; left: string; width: string; height: string };
    color?: string;
  }>;
}

export const DEFAULT_PAN_DOSSIER: DossierReportData = {
  caseNumber: "CASE-20260928-892A14",
  checkpoint: "Indira Gandhi International Airport - Terminal 3 (E-Gate 04)",
  screeningTime: "2026-09-28T13:41:59.172Z",
  officerId: "Officer Sarim Moin (MHA-BOC-409)",
  decision: "DETAIN / FRAUD ALERT",
  riskScore: 100.0,
  totalScreened: 164,
  clearanceRate: 75.6,
  tamperingIntercepted: 32,
  watchlistApprehensions: 8,
  avgLatency: "6.91s",
  documentSha256: "2482cb9e4f04f23be0133a2c98d011f0a8d3b2e71fa0c29f451e09c8b671a532",
  resolution: "800 x 520 px",
  documentType: "PAN_CARD",
  traveler: {
    fullName: "PRANAV MAHESH GORANI",
    documentNo: "EXYPG5811G",
    nationality: "IND",
    dob: "2007-07-20",
    gender: "7",
    expiryDate: "2025-08-01"
  },
  forensics: {
    mrzStatus: "TAMPERED / CHECKSUM MISMATCH",
    tamperingAssessment: "AUTHENTIC SUBSTRATE",
    biometricMatch: "VERIFIED MATCH (98.4%)",
    watchlistStatus: "NEGATIVE CLEARANCE"
  },
  blockchain: {
    blockIndex: 64,
    blockHash: "c302d37e56c1e10843fd955c0f289f23f7f3b93ad3e10431d633ca7022afb420",
    previousHash: "c0a4255f750bd41972f2cd9cd6a2b62f6d7b52909882b04b152182a8998ecb2b",
    digitalSignature: "SIG_MHA_BOC_C302D37E56C1E10843FD955C0F28_1790602919"
  },
  verdictDirective: "IMMEDIATE DETENTION: Trigger border checkpoint security alert. Suspected forged credentials / identity fraud / watchlist match.",
  boundingBoxes: [
    {
      label: "Cardholder Photo",
      boxStyle: { top: "33%", left: "16%", width: "13%", height: "23%" },
      color: "border-cyan-400 bg-cyan-400/10"
    },
    {
      label: "ID Number & Biographics",
      boxStyle: { top: "37%", left: "56%", width: "24%", height: "18%" },
      color: "border-cyan-400 bg-cyan-400/10"
    }
  ]
};

export const DIPLOMATIC_PASSPORT_DOSSIER: DossierReportData = {
  caseNumber: "CASE-20260928-VIP007",
  checkpoint: "Indira Gandhi International Airport - Terminal 3 (VIP Protocol Gate)",
  screeningTime: "2026-09-28T13:45:10.042Z",
  officerId: "Officer Sarim Moin (MHA-BOC-409)",
  decision: "CLEAR TO ENTER",
  riskScore: 2.5,
  totalScreened: 165,
  clearanceRate: 75.8,
  tamperingIntercepted: 32,
  watchlistApprehensions: 8,
  avgLatency: "6.85s",
  documentSha256: "8e92f1b4a3c570912d6e4b8109ca4198f24b896ec05183a218d6bf9073e51a23",
  resolution: "800 x 520 px",
  documentType: "PASSPORT",
  traveler: {
    fullName: "RAHUL SHARMA",
    documentNo: "Z83910245",
    nationality: "IND",
    dob: "1992-08-14",
    gender: "M",
    expiryDate: "2031-05-09"
  },
  forensics: {
    mrzStatus: "VALID / ICAO 9303 COMPLIANT",
    tamperingAssessment: "AUTHENTIC SUBSTRATE",
    biometricMatch: "VERIFIED MATCH (99.2%)",
    watchlistStatus: "NEGATIVE CLEARANCE"
  },
  blockchain: {
    blockIndex: 65,
    blockHash: "e481b092ca83fd1192837bc901aefb2049182371982bca819203810293847aef",
    previousHash: "c302d37e56c1e10843fd955c0f289f23f7f3b93ad3e10431d633ca7022afb420",
    digitalSignature: "SIG_MHA_BOC_E481B092CA83FD1192837BC901AEFB20_1892019482"
  },
  verdictDirective: "Auto-gate clearance approved. Traveler identity and document integrity verified.",
  boundingBoxes: [
    {
      label: "Primary Facial Portrait",
      boxStyle: { top: "32%", left: "14%", width: "16%", height: "34%" },
      color: "border-cyan-400 bg-cyan-400/10"
    },
    {
      label: "Biographic Data Fields",
      boxStyle: { top: "30%", left: "54%", width: "32%", height: "24%" },
      color: "border-amber-400 bg-amber-400/10"
    },
    {
      label: "Machine Readable Zone (ICAO Doc 9303)",
      boxStyle: { top: "72%", left: "10%", width: "80%", height: "22%" },
      color: "border-emerald-400 bg-emerald-400/10"
    }
  ]
};

export default function OfficialDossierReport({
  data = DEFAULT_PAN_DOSSIER,
  showControls = true
}: {
  data?: DossierReportData;
  showControls?: boolean;
}) {
  const [viewMode, setViewMode] = useState<"print" | "dark">("print");
  const [copied, setCopied] = useState(false);

  const isDetain = data.decision === "DETAIN / FRAUD ALERT" || (data.riskScore ?? 0) >= 70;
  const isClear = data.decision === "CLEAR TO ENTER" || (data.riskScore ?? 0) <= 30;

  const handlePrint = () => {
    // Set document title temporarily to match screenshot
    const originalTitle = document.title;
    document.title = "AI-Based Fake Identity & Document Screening System | Ministry of Home Affairs";
    window.print();
    document.title = originalTitle;
  };

  const handleCopyTextDossier = () => {
    const text = generateTextDossier(data);
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Top action toolbar (hidden on print) */}
      {showControls && (
        <div className="no-print p-4 rounded-xl bg-slate-900 border border-[#24365d] flex flex-wrap items-center justify-between gap-3 shadow-lg">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs font-mono font-bold text-white uppercase tracking-wider">
              Official MHA Evidentiary Screening Dossier
            </span>
            <span className="text-[11px] font-mono text-slate-400">
              #{data.caseNumber || "CASE-LIVE"}
            </span>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            <button
              type="button"
              onClick={() => setViewMode(viewMode === "print" ? "dark" : "print")}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-all"
            >
              Mode: {viewMode === "print" ? "📄 Official White Dossier" : "🌙 Dark Tactical View"}
            </button>

            <button
              type="button"
              onClick={handleCopyTextDossier}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-all flex items-center gap-1.5"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? "Copied ASCII Record" : "Copy ASCII Record"}</span>
            </button>

            <button
              type="button"
              onClick={handlePrint}
              className="px-4 py-1.5 rounded-lg bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-xs font-bold shadow-md shadow-blue-500/20 transition-all flex items-center gap-1.5"
            >
              <Printer className="w-4 h-4" />
              <span>Print Official Dossier (A4 / PDF)</span>
            </button>
          </div>
        </div>
      )}

      {/* Main 2-Page Printable Dossier Container */}
      <div
        className={`w-full max-w-[850px] mx-auto rounded-xl shadow-2xl transition-all ${
          viewMode === "print"
            ? "bg-white text-slate-900 border border-slate-300"
            : "bg-[#0b1329] text-white border border-[#24365d]"
        }`}
      >
        {/* ========================================================================= */}
        {/* PAGE 1: EVIDENTIARY VISUAL SUMMARY & BORDER CLEARANCE VERDICT */}
        {/* ========================================================================= */}
        <div className="p-8 sm:p-10 space-y-6">
          {/* Top Operational Stats Ribbon */}
          <div
            className={`flex flex-wrap items-center justify-between gap-4 pb-4 border-b text-[11px] font-mono leading-tight ${
              viewMode === "print" ? "border-slate-300 text-slate-700" : "border-[#24365d] text-slate-300"
            }`}
          >
            <div className="flex flex-wrap items-center gap-4 sm:gap-6">
              <div>
                <span className="text-slate-400 block text-[9px] uppercase">Total Screened</span>
                <span className="font-bold text-sm">{data.totalScreened ?? 164}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[9px] uppercase">Clearance Rate</span>
                <span className="font-bold text-sm text-emerald-600">{data.clearanceRate ?? 75.6}%</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[9px] uppercase">Tampering Intercepted</span>
                <span className="font-bold text-sm text-rose-600">{data.tamperingIntercepted ?? 32}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[9px] uppercase">Watchlist Apprehensions</span>
                <span className="font-bold text-sm text-amber-600">{data.watchlistApprehensions ?? 8}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[9px] uppercase">Avg Screening Latency</span>
                <span className="font-bold text-sm">{data.avgLatency ?? "6.91s"}</span>
              </div>
            </div>

            <div className="text-[10px] font-bold tracking-tight text-blue-600 sm:text-right">
              ⚡ GEMINI 2.5 FLASH NEURAL VISION | ICAO DOC 9303 | INTERPOL SLTD | ELA FORENSICS ACTIVE
            </div>
          </div>

          {/* Document Preview Card with AI Bounding Boxes */}
          <div
            className={`rounded-2xl border p-4 sm:p-6 shadow-xl relative overflow-hidden flex flex-col items-center justify-center ${
              viewMode === "print"
                ? "bg-slate-50 border-slate-300"
                : "bg-slate-950/80 border-[#24365d]"
            }`}
          >
            <div className="relative w-full max-w-[620px] aspect-[800/520] rounded-xl overflow-hidden shadow-2xl border border-slate-300/60 bg-gradient-to-br from-slate-200 via-white to-slate-100 flex items-center justify-center">
              {/* Document Graphic Renderer */}
              {data.documentType === "PASSPORT" ? (
                <PassportVisual data={data} />
              ) : (
                <PanCardVisual data={data} />
              )}

              {/* Dynamic Overlaid AI Bounding Boxes with tags matching screenshot */}
              {data.boundingBoxes &&
                data.boundingBoxes.map((b, idx) => (
                  <div
                    key={idx}
                    style={b.boxStyle}
                    className={`absolute border-2 pointer-events-none transition-all flex flex-col justify-start ${
                      b.color || "border-cyan-400 bg-cyan-400/10"
                    }`}
                  >
                    <span className="text-[10px] font-mono font-bold bg-slate-900/90 text-cyan-300 px-1.5 py-0.5 self-start -mt-3.5 ml-1 rounded border border-cyan-400/40 shadow-sm">
                      {b.label}
                    </span>
                  </div>
                ))}
            </div>

            {/* Under-Image Metadata line */}
            <div
              className={`w-full max-w-[620px] mt-3 flex items-center justify-between text-[11px] font-mono ${
                viewMode === "print" ? "text-slate-600" : "text-slate-400"
              }`}
            >
              <div className="truncate max-w-[380px]">
                <strong className="text-slate-800 dark:text-slate-200">DOCUMENT SHA-256:</strong>{" "}
                <span>{data.documentSha256?.slice(0, 24)}...</span>
              </div>
              <div>
                <strong className="text-slate-800 dark:text-slate-200">RESOLUTION:</strong>{" "}
                <span>{data.resolution || "800 x 520 px"}</span>
              </div>
            </div>
          </div>

          {/* Border Clearance Verdict Card */}
          <div
            className={`p-6 rounded-2xl border shadow-lg flex items-center justify-between gap-6 ${
              viewMode === "print"
                ? isDetain
                  ? "bg-white border-rose-300 shadow-rose-100"
                  : "bg-white border-emerald-300 shadow-emerald-100"
                : isDetain
                ? "bg-rose-950/20 border-rose-500/40 shadow-rose-950/20"
                : "bg-emerald-950/20 border-emerald-500/40 shadow-emerald-950/20"
            }`}
          >
            <div className="space-y-1.5 flex-1">
              <span className="text-[10px] font-mono font-bold tracking-widest text-slate-500 uppercase block">
                BORDER CLEARANCE VERDICT
              </span>
              <div className="flex items-center gap-2.5">
                <span
                  className={`w-4 h-4 rounded-full flex-shrink-0 ${
                    isDetain ? "bg-rose-500 animate-pulse" : "bg-emerald-500"
                  }`}
                />
                <h3
                  className={`text-2xl sm:text-3xl font-black tracking-tight ${
                    isDetain ? "text-rose-600" : "text-emerald-600"
                  }`}
                >
                  {isDetain ? "DETAIN / FRAUD ALERT" : "CLEAR TO ENTER"}
                </h3>
              </div>
              <p
                className={`text-xs font-medium leading-relaxed max-w-xl ${
                  viewMode === "print" ? "text-slate-700" : "text-slate-300"
                }`}
              >
                {data.verdictDirective ||
                  (isDetain
                    ? "IMMEDIATE DETENTION: Trigger border checkpoint security alert. Suspected forged credentials / identity fraud / watchlist match."
                    : "Auto-gate clearance approved. Traveler identity and document integrity verified.")}
              </p>
            </div>

            {/* Circular Risk Gauge Matching Screenshot */}
            <div className="flex flex-col items-center justify-center flex-shrink-0">
              <div className="relative w-20 h-20 flex items-center justify-center">
                <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                  <path
                    className={viewMode === "print" ? "text-slate-200" : "text-slate-800"}
                    strokeWidth="3.5"
                    stroke="currentColor"
                    fill="none"
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  />
                  <path
                    className={isDetain ? "text-rose-500" : "text-emerald-500"}
                    strokeDasharray={`${Math.min(100, Math.max(5, data.riskScore ?? 100))}, 100`}
                    strokeWidth="3.5"
                    strokeLinecap="round"
                    stroke="currentColor"
                    fill="none"
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  />
                </svg>
                <div className="absolute text-center">
                  <span
                    className={`font-mono font-black text-lg ${
                      isDetain ? "text-rose-600" : "text-emerald-600"
                    }`}
                  >
                    {(data.riskScore ?? 100).toFixed(1)}
                  </span>
                </div>
              </div>
              <span className="text-[9px] font-mono font-bold uppercase tracking-wider text-slate-400 mt-1">
                AI RISK SCORE
              </span>
            </div>
          </div>

          {/* Ministry Title Footer / Header */}
          <div
            className={`pt-4 border-t text-center space-y-0.5 ${
              viewMode === "print" ? "border-slate-300 text-slate-800" : "border-[#24365d] text-slate-200"
            }`}
          >
            <h4 className="text-xs font-bold font-mono tracking-wider uppercase">
              MINISTRY OF HOME AFFAIRS - OFFICIAL SCREENING DOSSIER
            </h4>
            <p className="text-[11px] text-slate-500 font-mono">
              Legal evidentiary summary generated at border checkpoint.
            </p>
          </div>
        </div>

        {/* Page break marker for print */}
        <div className="print-page-break border-t-2 border-dashed border-slate-300 my-8 no-print text-center text-xs font-mono text-slate-400 py-2">
          ▼ PAGE BREAK FOR PRINT (PAGE 2 BELOW) ▼
        </div>

        {/* ========================================================================= */}
        {/* PAGE 2: OFFICIAL SECURITY IMMIGRATION DOSSIER TERMINAL RECORD */}
        {/* ========================================================================= */}
        <div className="p-8 sm:p-10">
          <div
            className={`p-6 sm:p-8 rounded-xl font-mono text-xs sm:text-sm leading-relaxed border shadow-inner overflow-x-auto ${
              viewMode === "print"
                ? "bg-slate-50/80 border-slate-300 text-slate-900"
                : "bg-slate-950 border-[#24365d] text-slate-200"
            }`}
          >
            <pre className="whitespace-pre font-mono tracking-normal leading-5">
{generateTextDossier(data)}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Generates the clean official ASCII border immigration dossier text matching Image 3!
 */
export function generateTextDossier(data: DossierReportData): string {
  const line80 = "=".repeat(80);
  const lineSep = "-".repeat(80);

  const screenTime = data.screeningTime || new Date().toISOString();
  const risk = data.riskScore ?? 100.0;
  const decisionText = data.decision || (risk >= 70 ? "DETAIN / FRAUD ALERT" : "CLEAR TO ENTER");

  return `${line80}
MINISTRY OF HOME AFFAIRS (MHA) - BORDER SECURITY IMMIGRATION DOSSIER
${line80}
CHECKPOINT: ${data.checkpoint || "Indira Gandhi International Airport - Terminal 3 (E-Gate 04)"}
SCREENING TIME: ${screenTime} (UTC)
OFFICER ID: ${data.officerId || "Officer Sarim Moin (MHA-BOC-409)"}
DECISION: [ ${decisionText} ] (RISK SCORE: ${Math.round(risk)} / 100)
${lineSep}
TRAVELER PARTICULARS:
FULL NAME: ${data.traveler.fullName}
DOCUMENT NO: ${data.traveler.documentNo}
NATIONALITY: ${data.traveler.nationality}
DATE OF BIRTH: ${data.traveler.dob}
GENDER: ${data.traveler.gender}
EXPIRY DATE: ${data.traveler.expiryDate}

FORENSIC SCREENING FINDINGS:
1. ICAO MRZ STATUS: ${data.forensics.mrzStatus}
2. TAMPERING ASSESSMENT: ${data.forensics.tamperingAssessment}
3. BIOMETRIC MATCH: ${data.forensics.biometricMatch}
4. WATCHLIST STATUS: ${data.forensics.watchlistStatus}

CRYPTOGRAPHIC CHAIN OF CUSTODY (BLOCKCHAIN):
BLOCK INDEX: #${data.blockchain.blockIndex}
BLOCK HASH: ${data.blockchain.blockHash}
PREVIOUS HASH: ${data.blockchain.previousHash}
DIGITAL SIG: ${data.blockchain.digitalSignature}
${line80}
VERDICT DIRECTIVE: ${data.verdictDirective || (risk >= 70 ? "IMMEDIATE DETENTION: Trigger border checkpoint security alert. Suspected forged credentials / identity fraud / watchlist match." : "Auto-gate clearance approved. Traveler identity and document integrity verified.")}
${line80}`;
}

/**
 * High-fidelity PAN Card visual matching Image 2
 */
function PanCardVisual({ data }: { data: DossierReportData }) {
  return (
    <div className="w-full h-full relative bg-[#e0f2fe] text-slate-900 select-none overflow-hidden font-sans border-2 border-sky-300">
      {/* Subtle guilloche background texture */}
      <div className="absolute inset-0 opacity-15 bg-[radial-gradient(#0369a1_1px,transparent_1px)] [background-size:8px_8px]" />

      {/* Header bar */}
      <div className="relative z-10 px-6 pt-3 flex items-start justify-between">
        <div>
          <div className="text-sm font-black text-slate-800 tracking-wide">
            आयकर विभाग
          </div>
          <div className="text-[10px] font-bold text-slate-600 -mt-0.5 tracking-wider">
            INCOME TAX DEPARTMENT
          </div>
        </div>

        {/* Ashoka Emblem graphic */}
        <div className="flex flex-col items-center">
          <div className="w-6 h-8 text-amber-700 font-serif font-black text-[10px] leading-tight text-center">
            🏛️
            <div className="text-[6px] tracking-tighter">सत्यमेव जयते</div>
          </div>
        </div>

        <div className="text-right">
          <div className="text-sm font-black text-slate-800 tracking-wide">
            भारत सरकार
          </div>
          <div className="text-[10px] font-bold text-slate-600 -mt-0.5 tracking-wider">
            GOVT. OF INDIA
          </div>
        </div>
      </div>

      {/* Sub-header */}
      <div className="relative z-10 text-center mt-1">
        <div className="text-xs font-bold text-sky-900 tracking-wider">
          स्थायी लेखा संख्या कार्ड
        </div>
        <div className="text-[11px] font-semibold text-slate-700 -mt-0.5">
          Permanent Account Number Card
        </div>
      </div>

      {/* Card Body */}
      <div className="relative z-10 px-8 pt-3 flex items-start justify-between gap-4">
        {/* Left: Photo Portrait & Signature */}
        <div className="space-y-2">
          <div className="w-20 h-24 rounded bg-slate-800 border-2 border-sky-400 overflow-hidden shadow flex items-center justify-center">
            {/* Subject Avatar */}
            <div className="w-full h-full bg-gradient-to-t from-slate-700 via-slate-500 to-slate-400 flex flex-col items-center justify-end pb-1 text-center">
              <div className="w-8 h-8 rounded-full bg-slate-300 border border-slate-600 mb-1" />
              <div className="w-14 h-9 rounded-t-xl bg-slate-900" />
            </div>
          </div>

          <div className="w-20 h-6 border-b border-slate-700 flex items-center justify-center font-serif italic text-xs text-slate-800">
            {data.traveler.fullName.split(" ")[0]}
          </div>
        </div>

        {/* Center: Details */}
        <div className="flex-1 space-y-1.5 pl-2">
          <div>
            <span className="text-[8px] uppercase tracking-wider text-slate-500 font-bold block">
              Permanent Account Number
            </span>
            <span className="font-mono font-black text-xl tracking-widest text-slate-900">
              {data.traveler.documentNo || "EXYPG5811G"}
            </span>
          </div>

          <div>
            <span className="text-[8px] uppercase tracking-wider text-slate-500 font-bold block">
              Name / नाम
            </span>
            <span className="font-bold text-xs text-slate-900 block truncate">
              {data.traveler.fullName || "PRANAV MAHESH GORANI"}
            </span>
          </div>

          <div className="flex gap-4">
            <div>
              <span className="text-[8px] uppercase tracking-wider text-slate-500 font-bold block">
                DOB / जन्म तिथि
              </span>
              <span className="font-mono font-bold text-xs text-slate-800">
                {data.traveler.dob || "2007-07-20"}
              </span>
            </div>

            <div>
              <span className="text-[8px] uppercase tracking-wider text-slate-500 font-bold block">
                Gender / लिंग
              </span>
              <span className="font-mono font-bold text-xs text-slate-800">
                {data.traveler.gender || "M"}
              </span>
            </div>
          </div>
        </div>

        {/* Right: Hologram / QR Code */}
        <div className="w-20 flex flex-col items-center space-y-2">
          <div className="w-16 h-16 p-1 bg-white border border-slate-400 rounded shadow-sm flex items-center justify-center">
            {/* Simulated QR matrix */}
            <div className="w-full h-full bg-[repeating-conic-gradient(#000_0%_25%,#fff_0%_50%)] [background-size:6px_6px] rounded-sm" />
          </div>
          <span className="text-[8px] font-mono text-slate-600 font-bold">SECURE QR</span>
        </div>
      </div>
    </div>
  );
}

/**
 * High-fidelity Passport Visual matching Image 1
 */
function PassportVisual({ data }: { data: DossierReportData }) {
  return (
    <div className="w-full h-full relative bg-[#0f2137] text-white select-none overflow-hidden font-sans border-2 border-cyan-800/80">
      {/* Guilloche security pattern curves */}
      <svg className="absolute inset-0 w-full h-full opacity-20 pointer-events-none" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <pattern id="guilloche" width="40" height="40" patternUnits="userSpaceOnUse">
            <circle cx="20" cy="20" r="18" fill="none" stroke="#38bdf8" strokeWidth="0.5" />
            <circle cx="20" cy="20" r="10" fill="none" stroke="#38bdf8" strokeWidth="0.5" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#guilloche)" />
      </svg>

      {/* Header bar */}
      <div className="relative z-10 px-6 pt-3 flex items-center justify-between border-b border-cyan-800/50 pb-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-black tracking-widest text-cyan-300">
            REPUBLIC OF INDIA
          </span>
          <span className="text-[9px] font-mono bg-cyan-900/60 text-cyan-200 px-1.5 py-0.5 rounded border border-cyan-700">
            TYPE: P
          </span>
        </div>
        <div className="text-right text-[10px] font-mono text-cyan-400 font-bold">
          CONSULAR / PASSPORT
        </div>
      </div>

      {/* Body */}
      <div className="relative z-10 px-6 pt-3 flex items-start gap-5">
        {/* Subject Portrait */}
        <div className="w-24 h-32 rounded bg-slate-800 border-2 border-cyan-500 overflow-hidden shadow-lg flex flex-col items-center justify-end pb-2">
          <div className="w-10 h-10 rounded-full bg-slate-300 border border-slate-600 mb-1" />
          <div className="w-16 h-12 rounded-t-xl bg-cyan-950 border border-cyan-700" />
        </div>

        {/* Biographic Fields */}
        <div className="flex-1 grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
          <div>
            <span className="text-[8px] text-cyan-400 block font-mono">SURNAME / GIVEN NAMES</span>
            <span className="font-bold text-white tracking-wide block truncate">
              {data.traveler.fullName || "SHARMA RAHUL"}
            </span>
          </div>

          <div>
            <span className="text-[8px] text-cyan-400 block font-mono">PASSPORT NO.</span>
            <span className="font-mono font-bold text-amber-300">
              {data.traveler.documentNo || "Z83910245"}
            </span>
          </div>

          <div>
            <span className="text-[8px] text-cyan-400 block font-mono">NATIONALITY</span>
            <span className="font-mono text-white">
              {data.traveler.nationality || "IND"}
            </span>
          </div>

          <div>
            <span className="text-[8px] text-cyan-400 block font-mono">DATE OF BIRTH</span>
            <span className="font-mono text-white">
              {data.traveler.dob || "1992-08-14"}
            </span>
          </div>

          <div>
            <span className="text-[8px] text-cyan-400 block font-mono">SEX</span>
            <span className="font-mono text-white">
              {data.traveler.gender || "M"}
            </span>
          </div>

          <div>
            <span className="text-[8px] text-cyan-400 block font-mono">DATE OF EXPIRY</span>
            <span className="font-mono text-white">
              {data.traveler.expiryDate || "2031-05-09"}
            </span>
          </div>
        </div>

        {/* Right Seal */}
        <div className="w-16 h-16 rounded-full border-2 border-cyan-600/40 flex items-center justify-center opacity-60 text-center text-[7px] font-mono leading-tight">
          OFFICIAL<br/>EMBLEM
        </div>
      </div>

      {/* MRZ Band */}
      <div className="absolute bottom-2 left-6 right-6 p-2 rounded bg-black/70 border border-cyan-800/80 font-mono text-[11px] leading-tight text-emerald-400 tracking-wider">
        <div>P&lt;INDSHARMA&lt;&lt;RAHUL&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;</div>
        <div>Z839102459IND9208142M3105098&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;00</div>
      </div>
    </div>
  );
}
