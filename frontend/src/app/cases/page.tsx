"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  FolderGit2,
  Filter,
  Search,
  ArrowUpRight,
  ShieldAlert,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Clock,
} from "lucide-react";
import { api } from "@/lib/api";

export default function CasesQueuePage() {
  const [cases, setCases] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const [riskFilter, setRiskFilter] = useState("");
  const [docFilter, setDocFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

  const loadCases = async () => {
    setLoading(true);
    try {
      const data = await api.listCases({
        risk_level: riskFilter || undefined,
        document_type: docFilter || undefined,
        status: statusFilter || undefined,
      });
      setCases(data);
    } catch (err) {
      console.error("Failed to load cases:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCases();
  }, [riskFilter, docFilter, statusFilter]);

  const filteredCases = cases.filter((c) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      c.case_number.toLowerCase().includes(q) ||
      c.document_type.toLowerCase().includes(q) ||
      (c.notes && c.notes.toLowerCase().includes(q))
    );
  });

  const riskBadge = (level: string, score: number) => {
    switch (level) {
      case "HIGH":
        return (
          <span className="px-2.5 py-0.5 rounded text-[11px] font-bold font-mono bg-red-500/20 text-red-400 border border-red-500/30 flex items-center gap-1 w-fit">
            <ShieldAlert className="w-3 h-3" />
            <span>HIGH ({score})</span>
          </span>
        );
      case "MEDIUM":
        return (
          <span className="px-2.5 py-0.5 rounded text-[11px] font-bold font-mono bg-amber-500/20 text-amber-400 border border-amber-500/30 flex items-center gap-1 w-fit">
            <AlertTriangle className="w-3 h-3" />
            <span>MED ({score})</span>
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-0.5 rounded text-[11px] font-bold font-mono bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center gap-1 w-fit">
            <CheckCircle2 className="w-3 h-3" />
            <span>LOW ({score})</span>
          </span>
        );
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-[#24365d]">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
              Screening Cases Queue
            </h1>
            <span className="px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 text-xs font-mono font-bold">
              VERIFIER WORKLIST
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Examine flagged credentials, review automated multi-signal risk assessments & submit verification decisions.
          </p>
        </div>

        <button
          onClick={loadCases}
          className="p-2 rounded-lg bg-slate-900 border border-[#24365d] text-slate-400 hover:text-white transition-colors self-start sm:self-auto"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {/* Filter & Search Bar */}
      <div className="p-4 rounded-xl bg-slate-900/90 border border-[#24365d] flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          {/* Search Box */}
          <div className="relative min-w-[220px]">
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search case #, type, notes..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 rounded-lg bg-slate-950 border border-[#24365d] text-white text-xs focus:outline-none focus:border-blue-500"
            />
          </div>

          {/* Risk Filter */}
          <select
            value={riskFilter}
            onChange={(e) => setRiskFilter(e.target.value)}
            className="px-3 py-1.5 rounded-lg bg-slate-950 border border-[#24365d] text-slate-300 text-xs focus:outline-none focus:border-blue-500"
          >
            <option value="">All Risk Tiers</option>
            <option value="HIGH">High Risk</option>
            <option value="MEDIUM">Medium Risk</option>
            <option value="LOW">Low Risk</option>
          </select>

          {/* Doc Type Filter */}
          <select
            value={docFilter}
            onChange={(e) => setDocFilter(e.target.value)}
            className="px-3 py-1.5 rounded-lg bg-slate-950 border border-[#24365d] text-slate-300 text-xs focus:outline-none focus:border-blue-500"
          >
            <option value="">All Credentials</option>
            <option value="PASSPORT">Passport</option>
            <option value="VISA">Visa</option>
            <option value="NATIONAL_ID">National ID</option>
            <option value="DRIVING_LICENSE">Driving Licence</option>
            <option value="PERMIT">Permit</option>
          </select>

          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-1.5 rounded-lg bg-slate-950 border border-[#24365d] text-slate-300 text-xs focus:outline-none focus:border-blue-500"
          >
            <option value="">All Statuses</option>
            <option value="REVIEW_REQUIRED">Review Required</option>
            <option value="COMPLETED">Completed</option>
            <option value="ESCALATED">Escalated</option>
            <option value="REUPLOAD_REQUESTED">Re-upload Requested</option>
          </select>
        </div>

        <div className="text-xs font-mono text-slate-400">
          Showing <strong className="text-white">{filteredCases.length}</strong> case(s)
        </div>
      </div>

      {/* Cases Table */}
      <div className="rounded-2xl bg-slate-900/90 border border-[#24365d] overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/70 border-b border-[#24365d] text-slate-400 uppercase text-[10px] tracking-wider font-semibold">
              <tr>
                <th className="py-3.5 px-4">Case Identifier</th>
                <th className="py-3.5 px-4">Credential Type</th>
                <th className="py-3.5 px-4">Risk Assessment</th>
                <th className="py-3.5 px-4">Confidence</th>
                <th className="py-3.5 px-4">Screening Date</th>
                <th className="py-3.5 px-4">Status</th>
                <th className="py-3.5 px-4 text-right">Investigation</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1e2f50]">
              {loading ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-400">
                    <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
                    <span>Loading screening queue...</span>
                  </td>
                </tr>
              ) : filteredCases.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-400 space-y-2">
                    <FolderGit2 className="w-8 h-8 mx-auto text-slate-600" />
                    <div>No matching screening cases found.</div>
                    <Link href="/demo" className="text-xs text-blue-400 underline font-semibold">
                      Launch a synthetic benchmark demo scenario
                    </Link>
                  </td>
                </tr>
              ) : (
                filteredCases.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3.5 px-4 font-mono font-bold text-white">
                      {c.case_number}
                    </td>
                    <td className="py-3.5 px-4 font-semibold text-slate-200">
                      {c.document_type}
                    </td>
                    <td className="py-3.5 px-4">
                      {riskBadge(c.risk_level, c.risk_score)}
                    </td>
                    <td className="py-3.5 px-4 font-mono text-slate-300">
                      {Math.round(c.confidence * 100)}%
                    </td>
                    <td className="py-3.5 px-4 text-slate-400 font-mono text-[11px]">
                      {new Date(c.created_at).toLocaleString()}
                    </td>
                    <td className="py-3.5 px-4">
                      <span
                        className={`px-2 py-0.5 rounded text-[11px] font-medium ${
                          c.status === "COMPLETED"
                            ? "bg-emerald-500/10 text-emerald-400"
                            : c.status === "REVIEW_REQUIRED"
                            ? "bg-amber-500/10 text-amber-400"
                            : c.status === "ESCALATED"
                            ? "bg-purple-500/10 text-purple-400"
                            : "bg-blue-500/10 text-blue-400"
                        }`}
                      >
                        {c.status.replace("_", " ")}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <Link
                        href={`/cases/${c.id}`}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600/20 hover:bg-blue-600/40 text-blue-300 border border-blue-500/30 text-xs font-bold transition-all"
                      >
                        <span>Investigate</span>
                        <ArrowUpRight className="w-3.5 h-3.5" />
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
