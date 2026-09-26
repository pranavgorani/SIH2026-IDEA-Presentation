"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Settings,
  Sliders,
  Shield,
  Save,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  Info,
  Lock,
  Cpu,
  Database,
  ArrowRight,
  ShieldAlert
} from "lucide-react";
import { getSystemSettings, updateSystemSettings } from "@/lib/api";

export default function AdminSettingsPage() {
  const [weights, setWeights] = useState<{ [key: string]: number }>({
    document_validation: 0.15,
    visual_forensics: 0.25,
    identity_verification: 0.20,
    record_verification: 0.20,
    ocr_consistency: 0.10,
    image_quality: 0.05,
    mrz_validation: 0.05
  });

  const [thresholdLow, setThresholdLow] = useState<number>(30);
  const [thresholdMed, setThresholdMed] = useState<number>(60);
  const [aiProvider, setAiProvider] = useState<string>("LOCAL_CV_FALLBACK");
  const [verificationMode, setVerificationMode] = useState<string>("MOCK_SIMULATED");
  const [retentionDays, setRetentionDays] = useState<number>(30);

  const [statusMessage, setStatusMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);

  useEffect(() => {
    async function loadSettings() {
      try {
        const s = await getSystemSettings();
        if (s.weights) setWeights(s.weights);
        if (s.threshold_low !== undefined) setThresholdLow(s.threshold_low);
        if (s.threshold_medium !== undefined) setThresholdMed(s.threshold_medium);
        if (s.ai_provider) setAiProvider(s.ai_provider);
        if (s.verification_mode) setVerificationMode(s.verification_mode);
      } catch (err: unknown) {
        console.warn("Could not load remote settings, using production defaults", err);
      } finally {
        setLoading(false);
      }
    }
    loadSettings();
  }, []);

  const totalWeight = Object.values(weights).reduce((a, b) => a + b, 0);
  const isWeightValid = Math.abs(totalWeight - 1.0) < 0.01;

  const handleWeightChange = (key: string, val: number) => {
    setWeights(prev => ({ ...prev, [key]: parseFloat(val.toFixed(2)) }));
  };

  const handleSave = async () => {
    if (!isWeightValid) {
      setStatusMessage({
        type: "error",
        text: `Signal weights must sum to 100% (Current: ${(totalWeight * 100).toFixed(0)}%). Adjust values before saving.`
      });
      return;
    }

    setSaving(true);
    setStatusMessage(null);

    try {
      await updateSystemSettings({
        weights,
        threshold_low: thresholdLow,
        threshold_medium: thresholdMed,
        ai_provider: aiProvider,
        verification_mode: verificationMode
      });
      setStatusMessage({
        type: "success",
        text: "Security configuration saved and applied across multi-signal risk fusion engine."
      });
    } catch (err: unknown) {
      const e = err as Error;
      setStatusMessage({
        type: "error",
        text: e.message || "Failed to save configuration. Ensure your session has ADMIN privileges."
      });
    } finally {
      setSaving(false);
    }
  };

  const handleResetDefaults = () => {
    setWeights({
      document_validation: 0.15,
      visual_forensics: 0.25,
      identity_verification: 0.20,
      record_verification: 0.20,
      ocr_consistency: 0.10,
      image_quality: 0.05,
      mrz_validation: 0.05
    });
    setThresholdLow(30);
    setThresholdMed(60);
    setStatusMessage({ type: "success", text: "Reset to default SIH 2026 reference weights." });
  };

  const weightLabels: { [key: string]: { label: string; desc: string } } = {
    visual_forensics: { label: "Visual Forensics & Tamper ELA", desc: "Weight assigned to Error Level Analysis, noise variance, and inpainting signals" },
    identity_verification: { label: "Biometric 1:1 Identity Verification", desc: "Weight assigned to live camera face vs document portrait alignment" },
    record_verification: { label: "Central Issuer Registry Lookup", desc: "Weight assigned to official database verification adapter match" },
    document_validation: { label: "Document Field Rule Consistency", desc: "Weight assigned to chronological dates, expiration, and regex format rules" },
    ocr_consistency: { label: "OCR & MRZ Cross-Consistency", desc: "Weight assigned to visual OCR vs machine-readable zone checksum agreement" },
    image_quality: { label: "Image Quality & Specular Glare", desc: "Weight assigned to image resolution, blur, and lighting conditions" },
    mrz_validation: { label: "ICAO 9303 Check Digit Math", desc: "Weight assigned to 7-3-1 weight check digits on passport lines" }
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto pb-16">
      {/* Top Banner */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-blue-500/10 border border-blue-500/30 text-blue-400 flex items-center justify-center">
            <Lock className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              System Risk Thresholds & Model Weights
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30">
                ADMIN ONLY
              </span>
            </h1>
            <p className="text-xs text-slate-400">
              Configure parameters governing the multi-signal risk fusion engine and external verification adapters.
            </p>
          </div>
        </div>

        <Link
          href="/admin/system"
          className="text-xs font-mono text-blue-400 hover:text-blue-300 flex items-center gap-1.5"
        >
          View System Health & Latency
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      {statusMessage && (
        <div className={`p-4 rounded-xl border flex items-center gap-3 text-xs ${
          statusMessage.type === "success"
            ? "bg-emerald-950/40 border-emerald-500/40 text-emerald-300"
            : "bg-rose-950/40 border-rose-500/40 text-rose-300"
        }`}>
          {statusMessage.type === "success" ? <CheckCircle2 className="w-4 h-4 shrink-0" /> : <AlertTriangle className="w-4 h-4 shrink-0" />}
          <span>{statusMessage.text}</span>
        </div>
      )}

      {/* Section 1: Risk Engine Weight Allocations */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-4">
          <div>
            <h2 className="text-base font-semibold text-slate-100 flex items-center gap-2">
              <Sliders className="w-4 h-4 text-blue-400" />
              Multi-Signal Risk Engine Weights
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Adjust relative contribution of each forensic verification layer. Must sum exactly to 100%.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className={`px-3 py-1 rounded-lg font-mono text-xs border font-semibold ${
              isWeightValid ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30" : "bg-rose-500/10 text-rose-400 border-rose-500/30"
            }`}>
              Total Weight: {(totalWeight * 100).toFixed(0)}%
            </div>
            <button
              onClick={handleResetDefaults}
              className="px-2.5 py-1 text-xs text-slate-400 hover:text-slate-200 border border-slate-700 rounded-lg flex items-center gap-1.5"
            >
              <RotateCcw className="w-3 h-3" />
              Defaults
            </button>
          </div>
        </div>

        <div className="space-y-4">
          {Object.entries(weights).map(([key, val]) => {
            const meta = weightLabels[key] || { label: key, desc: "" };
            const percent = Math.round(val * 100);

            return (
              <div key={key} className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="flex-1 max-w-md">
                  <div className="text-xs font-semibold text-slate-200">{meta.label}</div>
                  <div className="text-[11px] text-slate-400">{meta.desc}</div>
                </div>

                <div className="flex items-center gap-4 w-full sm:w-72">
                  <input
                    type="range"
                    min="0"
                    max="50"
                    step="5"
                    value={percent}
                    onChange={(e) => handleWeightChange(key, parseInt(e.target.value) / 100)}
                    className="w-full accent-blue-500 h-1.5 bg-slate-800 rounded-lg cursor-pointer"
                  />
                  <span className="font-mono text-xs font-bold text-slate-200 w-12 text-right">
                    {percent}%
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Section 2: Thresholds & Governance */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
          <h2 className="text-sm font-semibold text-slate-100 flex items-center gap-2 border-b border-slate-800 pb-3">
            <Shield className="w-4 h-4 text-emerald-400" />
            Decision Threshold Tiers (0–100 Scale)
          </h2>
          <p className="text-xs text-slate-400 leading-relaxed">
            Categorizes the calculated risk score into statutory action tiers:
          </p>

          <div className="space-y-3 font-mono text-xs">
            <div className="p-3 bg-emerald-950/20 border border-emerald-500/30 rounded-xl flex items-center justify-between">
              <div>
                <span className="text-emerald-400 font-bold block">LOW RISK: 0 to {thresholdLow}</span>
                <span className="text-[10px] text-slate-400 font-sans">Eligible for Standard Verification</span>
              </div>
              <input
                type="number"
                min="10"
                max="50"
                value={thresholdLow}
                onChange={(e) => setThresholdLow(parseInt(e.target.value) || 30)}
                className="w-16 px-2 py-1 bg-slate-900 border border-slate-700 rounded text-slate-200 text-center font-mono"
              />
            </div>

            <div className="p-3 bg-amber-950/20 border border-amber-500/30 rounded-xl flex items-center justify-between">
              <div>
                <span className="text-amber-400 font-bold block">MEDIUM RISK: {thresholdLow + 1} to {thresholdMed}</span>
                <span className="text-[10px] text-slate-400 font-sans">Human Review Recommended</span>
              </div>
              <input
                type="number"
                min="40"
                max="80"
                value={thresholdMed}
                onChange={(e) => setThresholdMed(parseInt(e.target.value) || 60)}
                className="w-16 px-2 py-1 bg-slate-900 border border-slate-700 rounded text-slate-200 text-center font-mono"
              />
            </div>

            <div className="p-3 bg-rose-950/20 border border-rose-500/30 rounded-xl">
              <span className="text-rose-400 font-bold block">HIGH RISK: {thresholdMed + 1} to 100</span>
              <span className="text-[10px] text-slate-400 font-sans">Mandatory Human Review with Written Justification</span>
            </div>
          </div>
        </div>

        {/* Section 3: Provider & Retention Mode */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
          <h2 className="text-sm font-semibold text-slate-100 flex items-center gap-2 border-b border-slate-800 pb-3">
            <Cpu className="w-4 h-4 text-purple-400" />
            AI & Registry Provider Architecture
          </h2>

          <div className="space-y-4">
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1.5">
                Computer Vision & Forensics Provider
              </label>
              <select
                value={aiProvider}
                onChange={(e) => setAiProvider(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-blue-500"
              >
                <option value="LOCAL_CV_FALLBACK">Local Deterministic OpenCV (ELA + Noise Grid)</option>
                <option value="GEMINI_VISION_HYBRID">Gemini Multimodal Vision + Local CV</option>
                <option value="SANDBOXED_NEURAL_NET">Custom ResNet Forensics Sandbox</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1.5">
                Record Verification Adapter Mode
              </label>
              <select
                value={verificationMode}
                onChange={(e) => setVerificationMode(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-blue-500"
              >
                <option value="MOCK_SIMULATED">Simulated Registry Adapter (Demo Benchmark Mode)</option>
                <option value="SANDBOX_GATEWAY">Staging API Gateway (Authorized Gov Endpoints)</option>
              </select>
              <span className="text-[10px] text-slate-500 mt-1 block">
                Production deployments swap MockVerificationProvider for authorized central API adapters.
              </span>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1.5">
                Document Data Retention Policy
              </label>
              <select
                value={retentionDays}
                onChange={(e) => setRetentionDays(parseInt(e.target.value))}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-blue-500"
              >
                <option value={0}>Zero Retention (Purge Scan Post-Analysis)</option>
                <option value={30}>30 Days (Standard Border Security Quarantine)</option>
                <option value={90}>90 Days (Evidentiary Archive)</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Save Action Bar */}
      <div className="flex items-center justify-between pt-4 border-t border-slate-800">
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <Info className="w-4 h-4 text-slate-400" />
          Modifications are cryptographically committed to the system audit ledger.
        </div>

        <button
          onClick={handleSave}
          disabled={saving || !isWeightValid}
          className="inline-flex items-center gap-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-xl text-xs font-semibold shadow-lg shadow-blue-500/20 transition-colors"
        >
          <Save className="w-4 h-4" />
          {saving ? "Saving Configuration..." : "Save System Settings"}
        </button>
      </div>
    </div>
  );
}
