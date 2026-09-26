"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Shield, Lock, User, AlertCircle, ArrowRight, Microscope, Fingerprint } from "lucide-react";
import { api } from "@/lib/api";

export default function InspectorLoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("inspector");
  const [password, setPassword] = useState("inspector123");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await api.login(username, password);
      router.push("/cases");
    } catch (err: any) {
      setError(err.message || "Inspector authentication failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[90vh] flex items-center justify-center px-4 py-12 relative overflow-hidden">
      {/* Background Ambience */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-96 h-96 bg-amber-600/10 rounded-full blur-3xl pointer-events-none" />

      <div className="w-full max-w-lg space-y-6 relative z-10">
        {/* Header Badge */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-950/80 border border-amber-700/50 text-amber-400 text-xs font-mono font-bold tracking-wider mb-1 shadow-inner">
            <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
            FORENSIC INTELLIGENCE & AUDIT INVESTIGATION WING
          </div>
          <div className="flex justify-center my-3">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-amber-600 to-purple-600 flex items-center justify-center text-white shadow-xl shadow-amber-950/50 border border-amber-400/30">
              <Microscope className="w-8 h-8" />
            </div>
          </div>
          <h1 className="text-3xl font-black text-white tracking-tight">TRUST-ID INSPECTION PORTAL</h1>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            Deep Forensic Analysis, Tamper Heatmaps, 100-Point Audit Ledger & Investigation Timeline
          </p>
        </div>

        {/* Inspector Card */}
        <div className="p-7 sm:p-9 rounded-2xl bg-slate-900/95 border border-amber-900/40 shadow-2xl backdrop-blur-xl relative">
          <div className="absolute top-0 right-0 transform translate-x-2 -translate-y-2 bg-amber-600 text-[10px] font-mono font-extrabold uppercase px-2.5 py-0.5 rounded shadow">
            INSPECTOR PORTAL
          </div>

          {error && (
            <div className="mb-5 p-3 rounded-lg bg-red-950/60 border border-red-800 text-red-200 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center justify-between">
                <span>Field Inspector Badge / Username</span>
                <span className="text-[10px] text-amber-400 font-mono">SENIOR-INVESTIGATOR</span>
              </label>
              <div className="relative">
                <User className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  className="w-full pl-9 pr-3 py-2.5 rounded-lg bg-slate-950 border border-amber-900/50 text-white text-sm focus:outline-none focus:border-amber-500 transition-colors font-mono"
                  placeholder="inspector"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center justify-between">
                <span>Investigative Passcode</span>
                <span className="text-[10px] text-slate-500 font-mono">CRYPTOGRAPHIC</span>
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="w-full pl-9 pr-3 py-2.5 rounded-lg bg-slate-950 border border-amber-900/50 text-white text-sm focus:outline-none focus:border-amber-500 transition-colors"
                  placeholder="••••••••••••"
                />
              </div>
            </div>

            <div className="p-3 bg-amber-950/30 border border-amber-900/40 rounded-xl flex items-center gap-3 text-xs text-slate-300">
              <Fingerprint className="w-4 h-4 text-amber-400 flex-shrink-0" />
              <span>Grants access to full forensic evidence drawers, case notes, and 100-check audit matrix.</span>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full mt-2 py-3 px-4 rounded-xl bg-gradient-to-r from-amber-600 to-purple-600 hover:from-amber-500 hover:to-purple-500 text-white font-bold text-sm shadow-lg shadow-amber-950/50 flex items-center justify-center gap-2 transition-all disabled:opacity-50"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  <span>Access Case Investigation Vault</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Security Notice */}
          <div className="mt-6 pt-4 border-t border-slate-800 text-center">
            <p className="text-[11px] text-slate-400 leading-relaxed font-mono">
              <strong className="text-amber-400">Authorized personnel only.</strong><br />
              All case queries, investigative notes, and report downloads are permanently logged in the tamper-evident audit ledger.
            </p>
          </div>
        </div>

        {/* Portal Switcher Footer */}
        <div className="flex items-center justify-between text-xs text-slate-400 px-2 font-mono">
          <Link href="/login/admin" className="hover:text-red-400 transition-colors">
            ← Switch to Admin Portal
          </Link>
          <Link href="/login/verifier" className="hover:text-blue-400 transition-colors">
            Switch to Verifier Portal →
          </Link>
        </div>
      </div>
    </div>
  );
}
