"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Shield, Lock, User, ArrowRight, AlertCircle, ScanLine, Microscope, ShieldAlert, CheckCircle2 } from "lucide-react";
import { api } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [activeRole, setActiveRole] = useState<"VERIFIER" | "INSPECTOR" | "ADMIN">("VERIFIER");
  const [username, setUsername] = useState("verifier");
  const [password, setPassword] = useState("verifier123");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleRoleSelect = (role: "VERIFIER" | "INSPECTOR" | "ADMIN") => {
    setActiveRole(role);
    setError(null);
    if (role === "ADMIN") {
      setUsername("admin");
      setPassword("admin123");
    } else if (role === "INSPECTOR") {
      setUsername("inspector");
      setPassword("inspector123");
    } else {
      setUsername("verifier");
      setPassword("verifier123");
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await api.login(username, password);
      if (activeRole === "ADMIN") {
        router.push("/admin/settings");
      } else if (activeRole === "INSPECTOR") {
        router.push("/cases");
      } else {
        router.push("/screen");
      }
    } catch (err: any) {
      setError(err.message || "Authentication failed");
    } finally {
      setLoading(false);
    }
  };

  const portals = [
    {
      role: "VERIFIER" as const,
      title: "Verifier Portal",
      href: "/login/verifier",
      desc: "Document Screening & Review",
      icon: ScanLine,
      color: "from-blue-600 to-cyan-600",
      border: "border-blue-500/40",
      activeBg: "bg-blue-600/10",
      badge: "Border Control"
    },
    {
      role: "INSPECTOR" as const,
      title: "Inspector Portal",
      href: "/login/inspector",
      desc: "Deep Forensics & Audit Timeline",
      icon: Microscope,
      color: "from-amber-600 to-purple-600",
      border: "border-amber-500/40",
      activeBg: "bg-amber-600/10",
      badge: "Investigation"
    },
    {
      role: "ADMIN" as const,
      title: "Admin Command",
      href: "/login/admin",
      desc: "System Architecture & AI Config",
      icon: ShieldAlert,
      color: "from-red-600 to-amber-700",
      border: "border-red-500/40",
      activeBg: "bg-red-600/10",
      badge: "Root Control"
    }
  ];

  return (
    <div className="min-h-[88vh] flex items-center justify-center px-4 py-10">
      <div className="w-full max-w-2xl space-y-6">
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex p-3 rounded-2xl bg-blue-600/10 border border-blue-500/30 text-blue-400 mb-1">
            <Shield className="w-8 h-8" />
          </div>
          <h1 className="text-3xl font-black text-white tracking-tight">TRUST-ID SECURITY GATEWAY</h1>
          <p className="text-xs text-slate-400 max-w-lg mx-auto">
            Ministry of Home Affairs • Official Role-Based Authentication Matrix
          </p>
        </div>

        {/* 3 Dedicated Portal Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {portals.map((p) => {
            const Icon = p.icon;
            const isSelected = activeRole === p.role;
            return (
              <div
                key={p.role}
                onClick={() => handleRoleSelect(p.role)}
                className={`p-4 rounded-xl border cursor-pointer transition-all duration-200 relative text-left ${
                  isSelected
                    ? `${p.border} ${p.activeBg} shadow-lg shadow-blue-900/20`
                    : "border-slate-800 bg-slate-900/60 hover:bg-slate-800/80 hover:border-slate-700"
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${p.color} flex items-center justify-center text-white shadow-sm`}>
                    <Icon className="w-4 h-4" />
                  </div>
                  <span className="text-[9px] font-mono uppercase px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                    {p.badge}
                  </span>
                </div>
                <div className="text-sm font-bold text-white mb-0.5">{p.title}</div>
                <p className="text-[11px] text-slate-400 leading-tight mb-3">{p.desc}</p>
                <div className="flex items-center justify-between text-[10px] font-mono">
                  <span className={isSelected ? "text-blue-400 font-bold" : "text-slate-500"}>
                    {isSelected ? "Active Session" : "Click to select"}
                  </span>
                  <Link
                    href={p.href}
                    onClick={(e) => e.stopPropagation()}
                    className="text-slate-400 hover:text-white flex items-center gap-0.5 underline hover:no-underline"
                  >
                    Open Page →
                  </Link>
                </div>
              </div>
            );
          })}
        </div>

        {/* Direct Authentication Form */}
        <div className="p-6 sm:p-8 rounded-2xl bg-slate-900/90 border border-[#24365d] shadow-2xl backdrop-blur-xl">
          <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-800">
            <div>
              <span className="text-xs text-slate-400 font-mono">AUTHENTICATING AS</span>
              <h2 className="text-base font-bold text-white">
                {activeRole === "ADMIN" ? "System Administrator" : activeRole === "INSPECTOR" ? "Forensic Field Inspector" : "Border Screening Verifier"}
              </h2>
            </div>
            <Link
              href={activeRole === "ADMIN" ? "/login/admin" : activeRole === "INSPECTOR" ? "/login/inspector" : "/login/verifier"}
              className="text-xs text-blue-400 hover:text-blue-300 font-medium flex items-center gap-1"
            >
              Dedicated {activeRole} Portal →
            </Link>
          </div>

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
                  className="w-full pl-9 pr-3 py-2.5 rounded-lg bg-slate-950 border border-[#24365d] text-white text-sm focus:outline-none focus:border-blue-500 transition-colors font-mono"
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
                  <span>Sign In as {activeRole}</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Security Notice */}
          <div className="mt-6 pt-4 border-t border-slate-800 text-center">
            <p className="text-[11px] text-slate-400 font-mono">
              Authorized personnel only. All activities are recorded in the tamper-evident audit ledger.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
