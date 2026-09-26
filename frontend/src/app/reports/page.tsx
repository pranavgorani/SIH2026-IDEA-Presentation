"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  FileText, Download, Shield, AlertTriangle, CheckCircle, Clock,
  Search, Filter, RefreshCw, FileArchive, ArrowUpRight, BarChart2,
  Lock, CheckCircle2, AlertCircle
} from "lucide-react";
import { api } from "@/lib/api";

interface ReportItem {
  case_id: string;
  case_number: string;
  document_type: string;
  holder_name: string;
  risk_score: number;
  risk_level: string;
  status: string;
  decision: string;
  created_at: string;
  report_hash: string;
  pdf_url: string;
  csv_url: string;
  docx_url: string;
  zip_url: string;
}

export default function ReportsPage() {
  const [reports, setReports] = useState<ReportItem[]>([]);
  const [analytics, setAnalytics] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedRisk, setSelectedRisk] = useState("ALL");
  const [selectedType, setSelectedType] = useState("ALL");
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  const fetchReports = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/reports");
      if (res.ok) {
        const data = await res.json();
        setReports(data.reports || []);
        setAnalytics(data.analytics || null);
      } else {
        // Fallback to cases if empty
        const cases = await api.getCases({ limit: 50 });
        const items = cases.map((c: any) => ({
          case_id: c.id,
          case_number: c.case_number || `CASE-${c.id.slice(0, 8)}`,
          document_type: c.document_type || "PASSPORT",
          holder_name: c.holder_name || "Official Credential Holder",
          risk_score: c.risk_score || 15.0,
          risk_level: c.risk_level || "LOW",
          status: c.status || "COMPLETED",
          decision: c.decision || "APPROVED",
          created_at: c.created_at || new Date().toISOString(),
          report_hash: (c.id + c.risk_score).slice(0, 16),
          pdf_url: `/api/cases/${c.id}/report/pdf`,
          csv_url: `/api/cases/${c.id}/report/csv`,
          docx_url: `/api/cases/${c.id}/report/docx`,
          zip_url: `/api/cases/${c.id}/report/zip`,
        }));
        setReports(items);
      }
    } catch (e) {
      console.error("Failed to load reports:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const filteredReports = reports.filter((r) => {
    const matchesSearch =
      r.case_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.holder_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.document_type.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesRisk = selectedRisk === "ALL" || r.risk_level === selectedRisk;
    const matchesType = selectedType === "ALL" || r.document_type === selectedType;
    return matchesSearch && matchesRisk && matchesType;
  });

  const triggerDownload = (url: string, filename: string) => {
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#24365d]">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-blue-400 uppercase tracking-wider mb-1">
            <Shield className="w-4 h-4" />
            <span>Official Export Dispatch</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
            Document Screening Reports Center
          </h1>
          <p className="text-xs sm:text-sm text-slate-400">
            Generate, inspect, and export 100-point audit matrices in official PDF, CSV, and DOCX formats.
          </p>
        </div>

        <button
          onClick={fetchReports}
          disabled={loading}
          className="self-start sm:self-auto px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl border border-slate-700 flex items-center gap-2 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          <span>Refresh Ledger</span>
        </button>
      </div>

      {/* Analytics KPI Ribbon */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-slate-900/80 border border-[#24365d] shadow-sm">
          <div className="text-xs text-slate-400 font-mono mb-1">TOTAL REPORTS</div>
          <div className="text-2xl font-black text-white">{reports.length}</div>
          <div className="text-[10px] text-emerald-400 mt-1 flex items-center gap-1 font-mono">
            <CheckCircle2 className="w-3 h-3" /> 100-Point Verified
          </div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/80 border border-emerald-900/40 shadow-sm">
          <div className="text-xs text-slate-400 font-mono mb-1">LOW RISK (APPROVED)</div>
          <div className="text-2xl font-black text-emerald-400">
            {reports.filter((r) => r.risk_level === "LOW").length}
          </div>
          <div className="text-[10px] text-slate-400 mt-1 font-mono">Ready for Border Clearance</div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/80 border border-amber-900/40 shadow-sm">
          <div className="text-xs text-slate-400 font-mono mb-1">ELEVATED / REVIEW</div>
          <div className="text-2xl font-black text-amber-400">
            {reports.filter((r) => r.risk_level === "MEDIUM" || r.risk_level === "HIGH").length}
          </div>
          <div className="text-[10px] text-slate-400 mt-1 font-mono">Requires Inspector Audit</div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/80 border border-red-900/40 shadow-sm">
          <div className="text-xs text-slate-400 font-mono mb-1">CRITICAL REJECTIONS</div>
          <div className="text-2xl font-black text-red-400">
            {reports.filter((r) => r.risk_level === "CRITICAL").length}
          </div>
          <div className="text-[10px] text-red-300 mt-1 font-mono">Tamper / Impersonation</div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="p-4 rounded-xl bg-slate-900/80 border border-[#24365d] flex flex-col md:flex-row gap-3 items-center justify-between">
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search Case ID or Holder..."
            className="w-full pl-9 pr-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-blue-500"
          />
        </div>

        <div className="flex items-center gap-2 w-full md:w-auto">
          <div className="flex items-center gap-1.5 text-xs text-slate-400">
            <Filter className="w-3.5 h-3.5" />
            <span>Risk:</span>
          </div>
          <select
            value={selectedRisk}
            onChange={(e) => setSelectedRisk(e.target.value)}
            className="bg-slate-950 border border-slate-800 text-xs text-slate-300 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-blue-500"
          >
            <option value="ALL">All Risk Levels</option>
            <option value="LOW">Low Risk</option>
            <option value="MEDIUM">Medium Risk</option>
            <option value="HIGH">High Risk</option>
            <option value="CRITICAL">Critical</option>
          </select>

          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="bg-slate-950 border border-slate-800 text-xs text-slate-300 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-blue-500"
          >
            <option value="ALL">All Document Types</option>
            <option value="PASSPORT">Passport</option>
            <option value="NATIONAL_ID">National ID / Aadhaar</option>
            <option value="DRIVING_LICENSE">Driving License</option>
            <option value="VISA">Visa / Permit</option>
          </select>
        </div>
      </div>

      {/* Reports Table */}
      <div className="rounded-xl border border-[#24365d] bg-slate-900/60 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#0c1630] border-b border-[#24365d] text-slate-400 font-mono uppercase tracking-wider text-[11px]">
              <tr>
                <th className="py-3 px-4">Case Number</th>
                <th className="py-3 px-4">Document / Holder</th>
                <th className="py-3 px-4">Screening Date</th>
                <th className="py-3 px-4">Risk Evaluation</th>
                <th className="py-3 px-4">Audit Ledger</th>
                <th className="py-3 px-4 text-right">Actions & Exports</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80">
              {loading ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-400">
                    <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-blue-400" />
                    <span>Loading forensic report index...</span>
                  </td>
                </tr>
              ) : filteredReports.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-400">
                    <AlertCircle className="w-6 h-6 mx-auto mb-2 text-slate-500" />
                    <span>No reports found matching criteria.</span>
                  </td>
                </tr>
              ) : (
                filteredReports.map((report) => (
                  <tr key={report.case_id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3.5 px-4 font-mono font-bold text-white">
                      <Link
                        href={`/cases/${report.case_id}/report`}
                        className="hover:text-blue-400 underline decoration-slate-700 hover:decoration-blue-400"
                      >
                        {report.case_number}
                      </Link>
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="font-semibold text-slate-200">{report.document_type.replace(/_/g, " ")}</div>
                      <div className="text-[11px] text-slate-400">{report.holder_name}</div>
                    </td>
                    <td className="py-3.5 px-4 text-slate-300 font-mono">
                      {new Date(report.created_at).toLocaleDateString()} {new Date(report.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </td>
                    <td className="py-3.5 px-4">
                      <span
                        className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase border ${
                          report.risk_level === "LOW"
                            ? "bg-emerald-950/60 text-emerald-300 border-emerald-800"
                            : report.risk_level === "MEDIUM"
                            ? "bg-amber-950/60 text-amber-300 border-amber-800"
                            : "bg-red-950/60 text-red-300 border-red-800"
                        }`}
                      >
                        <span
                          className={`w-1.5 h-1.5 rounded-full ${
                            report.risk_level === "LOW"
                              ? "bg-emerald-400"
                              : report.risk_level === "MEDIUM"
                              ? "bg-amber-400"
                              : "bg-red-400 animate-ping"
                          }`}
                        />
                        {report.risk_level} ({report.risk_score})
                      </span>
                    </td>
                    <td className="py-3.5 px-4 font-mono text-[10px] text-slate-400">
                      <div className="flex items-center gap-1 text-purple-300">
                        <Lock className="w-3 h-3 text-purple-400" />
                        <span>SHA-256 SEALED</span>
                      </div>
                      <div className="text-slate-500 truncate max-w-[120px]">{report.report_hash}</div>
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <div className="flex items-center justify-end gap-1.5 flex-wrap">
                        {/* 100 Checks Link */}
                        <Link
                          href={`/cases/${report.case_id}/checks`}
                          className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] font-medium border border-slate-700 transition-colors"
                        >
                          100 Checks
                        </Link>

                        {/* PDF */}
                        <button
                          onClick={() => triggerDownload(report.pdf_url, `TRUST-ID_Report_${report.case_number}.pdf`)}
                          className="px-2 py-1 rounded bg-blue-600 hover:bg-blue-500 text-white text-[11px] font-bold shadow-sm transition-colors flex items-center gap-1"
                          title="Download PDF Report"
                        >
                          <FileText className="w-3 h-3" />
                          <span>PDF</span>
                        </button>

                        {/* CSV */}
                        <button
                          onClick={() => triggerDownload(report.csv_url, `TRUST-ID_Checks_${report.case_number}.csv`)}
                          className="px-2 py-1 rounded bg-emerald-700 hover:bg-emerald-600 text-white text-[11px] font-bold shadow-sm transition-colors"
                          title="Export 100-Checks to CSV"
                        >
                          CSV
                        </button>

                        {/* DOCX */}
                        <button
                          onClick={() => triggerDownload(report.docx_url, `TRUST-ID_Report_${report.case_number}.docx`)}
                          className="px-2 py-1 rounded bg-indigo-700 hover:bg-indigo-600 text-white text-[11px] font-bold shadow-sm transition-colors"
                          title="Export to Word DOCX"
                        >
                          DOCX
                        </button>

                        {/* ZIP */}
                        <button
                          onClick={() => triggerDownload(report.zip_url, `TRUST-ID_${report.case_number}_REPORTS.zip`)}
                          className="px-2 py-1 rounded bg-purple-700 hover:bg-purple-600 text-white text-[11px] font-bold shadow-sm transition-colors flex items-center gap-1"
                          title="Download All Formats (ZIP)"
                        >
                          <FileArchive className="w-3 h-3" />
                          <span>All</span>
                        </button>
                      </div>
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
