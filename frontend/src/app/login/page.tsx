"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Shield, Lock, User, ArrowRight, AlertCircle, CheckCircle } from "lucide-react";
import { api } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("verifier");
  const [password, setPassword] = useState("verifier123");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await api.login(username, password);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Authentication failed");
    } finally {
      setLoading(false);
    }
  };

  const selectRole = (u: string, p: string) => {
    setUsername(u);
    setPassword(p);
    setError(null);
  };

  return (
    <div className="min-h-[85vh] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md space-y-6">
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex p-3 rounded-2xl bg-blue-600/10 border border-blue-500/30 text-blue-400 mb-1">
            <Shield className="w-8 h-8" />
          </div>
          <h1 className="text-2xl font-black text-white tracking-tight">TRUST-ID Authentication</h1>
          <p className="text-xs text-slate-400">
            Ministry of Home Affairs • Secure Border Control & Screening Portal
          </p>
        </div>

        {/* Card */}
        <div className="p-6 sm:p-8 rounded-2xl bg-slate-900/90 border border-[#24365d] shadow-2xl backdrop-blur-xl">
          {error && (
            <div className="mb-5 p-3 rounded-lg bg-red-950/40 border border-red-800/50 text-red-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Officer Identifier / Username
              </label>
              <div className="relative">
                <User className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  className="w-full pl-9 pr-3 py-2.5 rounded-lg bg-slate-950 border border-[#24365d] text-white text-sm focus:outline-none focus:border-blue-500 transition-colors"
                  placeholder="e.g. verifier"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Security Passcode
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="w-full pl-9 pr-3 py-2.5 rounded-lg bg-slate-950 border border-[#24365d] text-white text-sm focus:outline-none focus:border-blue-500 transition-colors"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold text-sm shadow-lg shadow-blue-500/25 flex items-center justify-center gap-2 transition-all disabled:opacity-50"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  <span>Authenticate & Enter Command</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Quick Demo Credentials Switcher */}
          <div className="mt-6 pt-6 border-t border-[#24365d] space-y-2">
            <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider text-center">
              Quick Role Switcher (Hackathon Demo)
            </div>
            <div className="grid grid-cols-3 gap-2 pt-1">
              <button
                type="button"
                onClick={() => selectRole("verifier", "verifier123")}
                className={`p-2 rounded-lg text-xs font-semibold border transition-all text-center ${
                  username === "verifier"
                    ? "bg-blue-600/20 border-blue-500 text-blue-300"
                    : "bg-slate-950 border-[#24365d] text-slate-400 hover:text-white"
                }`}
              >
                Verifier
              </button>
              <button
                type="button"
                onClick={() => selectRole("investigator", "investigator123")}
                className={`p-2 rounded-lg text-xs font-semibold border transition-all text-center ${
                  username === "investigator"
                    ? "bg-purple-600/20 border-purple-500 text-purple-300"
                    : "bg-slate-950 border-[#24365d] text-slate-400 hover:text-white"
                }`}
              >
                Investigator
              </button>
              <button
                type="button"
                onClick={() => selectRole("admin", "admin123")}
                className={`p-2 rounded-lg text-xs font-semibold border transition-all text-center ${
                  username === "admin"
                    ? "bg-emerald-600/20 border-emerald-500 text-emerald-300"
                    : "bg-slate-950 border-[#24365d] text-slate-400 hover:text-white"
                }`}
              >
                Admin
              </button>
            </div>
          </div>
        </div>

        <div className="text-center text-[11px] text-slate-500">
          Protected by MHA RBAC & Multi-Factor Security Policies
        </div>
      </div>
    </div>
  );
}
