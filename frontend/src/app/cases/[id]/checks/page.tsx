"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  Shield, CheckCircle2, AlertTriangle, XCircle, HelpCircle,
  Search, Filter, ArrowLeft, Download, FileText, ChevronRight,
  Info, ExternalLink, RefreshCw, X, ShieldAlert, Check
} from "lucide-react";

interface CheckItem {
  check_id: string;
  category: string;
  name: string;
  description: string;
  status: "PASS" | "FAIL" | "WARNING" | "UNAVAILABLE" | "NOT_APPLICABLE" | "NOT_CHECKED";
  severity: "INFO" | "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  confidence: number;
  evidence: string;
  value?: string;
  expected_value?: string;
  message: string;
}

export default function CaseChecksPage() {
  const params = useParams();
  const caseId = params.id as string;
  const router = useRouter();

  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [selectedCheck, setSelectedCheck] = useState<CheckItem | null>(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [categoryFilter, setCategoryFilter] = useState<string>("ALL");
  const [severityFilter, setSeverityFilter] = useState<string>("ALL");
  const [searchTerm, setSearchTerm] = useState<string>("");

  const fetchChecks = async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/cases/${caseId}/checks`);
      if (res.ok) {
        const json = await res.json();
        setData(json);
      } else {
        console.error("Failed to fetch checks");
      }
    } catch (e) {
      console.error("Network error fetching checks:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (caseId) {
      fetchChecks();
    }
  }, [caseId]);

  const checks: CheckItem[] = data?.checks || [];

  const filteredChecks = checks.filter((c) => {
    const matchesSearch =
      c.check_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.evidence.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === "ALL" || c.status === statusFilter;
    const matchesCategory = categoryFilter === "ALL" || c.category === categoryFilter;
    const matchesSeverity = severityFilter === "ALL" || c.severity === severityFilter;
    return matchesSearch && matchesStatus && matchesCategory && matchesSeverity;
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "PASS":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-950/70 text-emerald-400 border border-emerald-800">
            <Check className="w-3 h-3 text-emerald-400" /> PASS
          </span>
        );
      case "FAIL":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-red-950/70 text-red-400 border border-red-800">
            <XCircle className="w-3 h-3 text-red-400" /> FAIL
          </span>
        );
      case "WARNING":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-950/70 text-amber-400 border border-amber-800">
            <AlertTriangle className="w-3 h-3 text-amber-400" /> WARNING
          </span>
        );
      case "UNAVAILABLE":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-slate-800 text-slate-300 border border-slate-700">
            <HelpCircle className="w-3 h-3 text-slate-400" /> UNAVAILABLE
          </span>
        );
      case "NOT_APPLICABLE":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-slate-900 text-slate-400 border border-slate-800">
            N/A
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-400">
            {status}
          </span>
        );
    }
  };

  const getSeverityBadge = (sev: string) => {
    const map: Record<string, string> = {
      CRITICAL: "text-red-400 border-red-800/80 bg-red-950/40",
      HIGH: "text-orange-400 border-orange-800/80 bg-orange-950/40",
      MEDIUM: "text-amber-400 border-amber-800/80 bg-amber-950/40",
      LOW: "text-blue-400 border-blue-800/80 bg-blue-950/40",
      INFO: "text-slate-400 border-slate-800 bg-slate-900/40"
    };
    return (
      <span className={`px-1.5 py-0.5 rounded text-[9px] font-mono font-bold uppercase border ${map[sev] || map.INFO}`}>
        {sev}
      </span>
    );
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Navigation Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#24365d]">
        <div>
          <Link
            href={`/cases/${caseId}`}
            className="inline-flex items-center gap-1.5 text-xs text-blue-400 hover:text-blue-300 font-mono mb-2"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Case Overview
          </Link>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
              100-Point Document Audit Matrix
            </h1>
            <span className="px-2.5 py-0.5 rounded-full bg-blue-500/20 text-blue-400 border border-blue-500/40 text-xs font-mono font-bold">
              {caseId ? (caseId.length > 12 ? caseId.slice(0, 12) + "..." : caseId) : ""}
            </span>
          </div>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Real verification signals evaluated across 8 forensic layers. Unavailable checks are strictly isolated from PASS.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link
            href={`/api/cases/${caseId}/report/pdf`}
            target="_blank"
            className="px-3 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold shadow-lg shadow-blue-950/50 flex items-center gap-1.5 transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download PDF</span>
          </Link>
          <Link
            href={`/api/cases/${caseId}/report/csv`}
            className="px-3 py-2 rounded-xl bg-emerald-700 hover:bg-emerald-600 text-white text-xs font-bold shadow-sm flex items-center gap-1.5 transition-colors"
          >
            <FileText className="w-3.5 h-3.5" />
            <span>CSV</span>
          </Link>
        </div>
      </div>

      {/* Summary KPI Cards */}
      {data && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800">
            <div className="text-[10px] font-mono text-slate-400 uppercase">Total Checks</div>
            <div className="text-xl font-black text-white">{data.total_checks}</div>
            <div className="text-[10px] text-slate-500 font-mono">100/100 Executed</div>
          </div>
          <div className="p-3 rounded-xl bg-slate-900/90 border border-emerald-900/50">
            <div className="text-[10px] font-mono text-emerald-400 uppercase">Passed</div>
            <div className="text-xl font-black text-emerald-400">{data.passed}</div>
            <div className="text-[10px] text-emerald-500 font-mono">Verified Clear</div>
          </div>
          <div className="p-3 rounded-xl bg-slate-900/90 border border-red-900/50">
            <div className="text-[10px] font-mono text-red-400 uppercase">Failed</div>
            <div className="text-xl font-black text-red-400">{data.failed}</div>
            <div className="text-[10px] text-red-500 font-mono">Anomalies Detected</div>
          </div>
          <div className="p-3 rounded-xl bg-slate-900/90 border border-amber-900/50">
            <div className="text-[10px] font-mono text-amber-400 uppercase">Warnings</div>
            <div className="text-xl font-black text-amber-400">{data.warnings}</div>
            <div className="text-[10px] text-amber-500 font-mono">Review Advised</div>
          </div>
          <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800">
            <div className="text-[10px] font-mono text-slate-400 uppercase">Unavailable</div>
            <div className="text-xl font-black text-slate-300">{data.unavailable}</div>
            <div className="text-[10px] text-slate-500 font-mono">Ext. Records Off</div>
          </div>
          <div className="p-3 rounded-xl bg-slate-900/90 border border-blue-900/50">
            <div className="text-[10px] font-mono text-blue-400 uppercase">Integrity Score</div>
            <div className="text-xl font-black text-blue-400">{data.document_integrity_score} / 100</div>
            <div className="text-[10px] text-blue-300 font-mono">Weighted Health</div>
          </div>
        </div>
      )}

      {/* Category Progress Bars */}
      {data?.category_breakdown && (
        <div className="p-4 rounded-xl bg-slate-900/70 border border-[#24365d]">
          <h2 className="text-xs font-mono font-bold uppercase text-slate-300 mb-3 tracking-wider">
            Verification Category Health Breakdown
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {Object.entries(data.category_breakdown).map(([cat, stats]: [string, any]) => {
              const passPct = stats.total > 0 ? (stats.passed / stats.total) * 100 : 0;
              return (
                <div key={cat} className="space-y-1.5 p-2 rounded-lg bg-slate-950/60 border border-slate-800/80">
                  <div className="flex items-center justify-between text-xs font-medium">
                    <span className="text-slate-300 truncate max-w-[130px]">{cat.replace(/_/g, " ")}</span>
                    <span className="font-mono text-slate-400 text-[11px]">
                      {stats.passed}/{stats.total}
                    </span>
                  </div>
                  <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden flex">
                    <div
                      className={`h-full ${
                        stats.failed > 0
                          ? "bg-red-500"
                          : stats.warnings > 0
                          ? "bg-amber-400"
                          : "bg-emerald-500"
                      }`}
                      style={{ width: `${passPct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Filter and Search Ribbon */}
      <div className="p-4 rounded-xl bg-slate-900/80 border border-[#24365d] flex flex-col md:flex-row gap-3 items-center justify-between">
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search Check ID (CHK-001) or Title..."
            className="w-full pl-9 pr-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-blue-500"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2 w-full md:w-auto">
          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 text-xs text-slate-300 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-blue-500"
          >
            <option value="ALL">All Statuses</option>
            <option value="PASS">PASS</option>
            <option value="FAIL">FAIL</option>
            <option value="WARNING">WARNING</option>
            <option value="UNAVAILABLE">UNAVAILABLE</option>
            <option value="NOT_APPLICABLE">NOT APPLICABLE</option>
          </select>

          {/* Category Filter */}
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 text-xs text-slate-300 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-blue-500"
          >
            <option value="ALL">All 8 Categories</option>
            <option value="DOCUMENT_INTEGRITY">Document Integrity (001-015)</option>
            <option value="OCR_TEXT_EXTRACTION">OCR & Text (016-030)</option>
            <option value="FIELD_LOGICAL_VALIDATION">Field Validation (031-045)</option>
            <option value="MRZ_DATA">MRZ Data (046-055)</option>
            <option value="VISUAL_FORENSICS">Visual Forensics (056-070)</option>
            <option value="IDENTITY_VERIFICATION">Identity (071-080)</option>
            <option value="RECORD_VERIFICATION">Record Verification (081-090)</option>
            <option value="SECURITY_RISK_AUDIT">Security & Risk (091-100)</option>
          </select>

          {/* Severity Filter */}
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 text-xs text-slate-300 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-blue-500"
          >
            <option value="ALL">All Severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
            <option value="INFO">Info</option>
          </select>
        </div>
      </div>

      {/* 100 Checks Matrix Table */}
      <div className="rounded-xl border border-[#24365d] bg-slate-900/60 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#0c1630] border-b border-[#24365d] text-slate-400 font-mono uppercase tracking-wider text-[11px]">
              <tr>
                <th className="py-3 px-4">ID</th>
                <th className="py-3 px-4">Category</th>
                <th className="py-3 px-4">Verification Check</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Severity</th>
                <th className="py-3 px-4">Confidence</th>
                <th className="py-3 px-4">Evidence Summary</th>
                <th className="py-3 px-4 text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80">
              {loading ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-400">
                    <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-blue-400" />
                    <span>Loading 100-point check ledger...</span>
                  </td>
                </tr>
              ) : filteredChecks.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-400">
                    <Info className="w-6 h-6 mx-auto mb-2 text-slate-500" />
                    <span>No checks match the selected filters.</span>
                  </td>
                </tr>
              ) : (
                filteredChecks.map((chk) => (
                  <tr
                    key={chk.check_id}
                    onClick={() => setSelectedCheck(chk)}
                    className="hover:bg-slate-800/50 cursor-pointer transition-colors"
                  >
                    <td className="py-3 px-4 font-mono font-bold text-white whitespace-nowrap">
                      {chk.check_id}
                    </td>
                    <td className="py-3 px-4 text-slate-400 font-mono text-[10px] whitespace-nowrap">
                      {chk.category.replace(/_/g, " ")}
                    </td>
                    <td className="py-3 px-4 font-semibold text-slate-200">
                      {chk.name}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      {getStatusBadge(chk.status)}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      {getSeverityBadge(chk.severity)}
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-300">
                      {(chk.confidence * 100).toFixed(0)}%
                    </td>
                    <td className="py-3 px-4 text-slate-400 max-w-xs truncate">
                      {chk.evidence || chk.message || "—"}
                    </td>
                    <td className="py-3 px-4 text-right text-slate-500 hover:text-blue-400">
                      <ChevronRight className="w-4 h-4 ml-auto" />
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Check Detail Slide-Out Modal / Drawer (Requirement 11) */}
      {selectedCheck && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="w-full max-w-xl rounded-2xl bg-slate-900 border border-[#24365d] shadow-2xl p-6 relative space-y-4">
            {/* Header */}
            <div className="flex items-start justify-between pb-3 border-b border-slate-800">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-mono font-bold text-blue-400">{selectedCheck.check_id}</span>
                  {getStatusBadge(selectedCheck.status)}
                  {getSeverityBadge(selectedCheck.severity)}
                </div>
                <h3 className="text-lg font-bold text-white mt-1">{selectedCheck.name}</h3>
                <div className="text-[11px] font-mono text-slate-400 mt-0.5">
                  Category: {selectedCheck.category.replace(/_/g, " ")}
                </div>
              </div>
              <button
                onClick={() => setSelectedCheck(null)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Description & Message */}
            <div className="space-y-3 text-xs">
              <div>
                <span className="font-semibold text-slate-400 uppercase tracking-wider text-[10px] font-mono">
                  Description
                </span>
                <p className="text-slate-200 mt-0.5">{selectedCheck.description || selectedCheck.name}</p>
              </div>

              <div>
                <span className="font-semibold text-slate-400 uppercase tracking-wider text-[10px] font-mono">
                  Analysis Outcome & Message
                </span>
                <p className="text-slate-200 mt-0.5 bg-slate-950 p-2.5 rounded-lg border border-slate-800 font-mono text-[11px]">
                  {selectedCheck.message}
                </p>
              </div>

              {/* Confidence Meter */}
              <div>
                <div className="flex items-center justify-between text-[11px] font-mono mb-1">
                  <span className="text-slate-400">Detection Confidence:</span>
                  <span className="text-white font-bold">{(selectedCheck.confidence * 100).toFixed(1)}%</span>
                </div>
                <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                  <div
                    className="h-full bg-blue-500 rounded-full"
                    style={{ width: `${selectedCheck.confidence * 100}%` }}
                  />
                </div>
              </div>

              {/* Evidence Drawer */}
              <div>
                <span className="font-semibold text-slate-400 uppercase tracking-wider text-[10px] font-mono">
                  Forensic Evidence & Region Analysis
                </span>
                <div className="mt-1 p-3 rounded-lg bg-slate-950/80 border border-slate-800 text-slate-300 leading-relaxed font-mono text-[11px]">
                  "{selectedCheck.evidence || "No anomalous variance detected in document substrate."}"
                </div>
              </div>

              {/* Expected vs Actual Value (if present) */}
              {(selectedCheck.expected_value || selectedCheck.value) && (
                <div className="grid grid-cols-2 gap-2 pt-1 font-mono text-[11px]">
                  <div className="p-2 rounded bg-slate-950 border border-slate-800">
                    <span className="text-[10px] text-slate-500 block">Expected Value:</span>
                    <span className="text-slate-300">{selectedCheck.expected_value || "N/A"}</span>
                  </div>
                  <div className="p-2 rounded bg-slate-950 border border-slate-800">
                    <span className="text-[10px] text-slate-500 block">Actual Extracted:</span>
                    <span className="text-slate-300">{selectedCheck.value || "N/A"}</span>
                  </div>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="pt-3 border-t border-slate-800 flex justify-end">
              <button
                onClick={() => setSelectedCheck(null)}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold rounded-lg transition-colors"
              >
                Close Drawer
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
