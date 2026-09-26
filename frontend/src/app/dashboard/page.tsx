"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ShieldAlert,
  FileCheck,
  AlertTriangle,
  Clock,
  Search,
  ArrowUpRight,
  TrendingUp,
  FileText,
  Scan,
  UserX,
  CalendarX,
  Cpu,
  RefreshCw,
} from "lucide-react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";
import { api } from "@/lib/api";

export default function DashboardPage() {
  const [stats, setStats] = useState<any>(null);
  const [recentCases, setRecentCases] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [s, c] = await Promise.all([
        api.getDashboardStats(),
        api.listCases({ limit: 8 } as any),
      ]);
      setStats(s);
      setRecentCases(c);
    } catch (err) {
      console.error("Dashboard fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const riskColors: Record<string, string> = {
    LOW: "#10B981",
    MEDIUM: "#F59E0B",
    HIGH: "#EF4444",
    PENDING: "#94A3B8",
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-[#24365d]">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
              Command Dashboard
            </h1>
            <span className="px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 text-xs font-mono font-bold">
              LIVE TELEMETRY
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real-time identity credential forensics & screening operational metrics.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchData}
            title="Refresh Data"
            className="p-2 rounded-lg bg-slate-900 border border-[#24365d] text-slate-400 hover:text-white transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </button>
          <Link
            href="/screen"
            className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs shadow-md shadow-blue-500/25 flex items-center gap-2 transition-all"
          >
            <Scan className="w-4 h-4" />
            <span>Screen Document</span>
          </Link>
          <Link
            href="/demo"
            className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-amber-400 font-bold text-xs border border-[#24365d] flex items-center gap-2 transition-all"
          >
            <Cpu className="w-4 h-4" />
            <span>Launch Demo</span>
          </Link>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {/* Total Screened */}
        <div className="p-4 rounded-xl bg-slate-900/80 border border-[#24365d] shadow-sm">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] font-bold uppercase tracking-wider">Screened</span>
            <FileText className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-black text-white font-mono mt-2">
            {stats?.total_screened || 0}
          </div>
          <div className="text-[10px] text-emerald-400 flex items-center gap-1 mt-1 font-semibold">
            <TrendingUp className="w-3 h-3" />
            <span>+14.2% this week</span>
          </div>
        </div>

        {/* Requiring Review */}
        <div className="p-4 rounded-xl bg-amber-950/20 border border-amber-600/30 shadow-sm">
          <div className="flex items-center justify-between text-amber-400">
            <span className="text-[11px] font-bold uppercase tracking-wider">Pending Review</span>
            <AlertTriangle className="w-4 h-4" />
          </div>
          <div className="text-2xl font-black text-amber-400 font-mono mt-2">
            {stats?.requiring_review || 0}
          </div>
          <div className="text-[10px] text-amber-300/80 mt-1 font-medium">
            Human-in-the-Loop active
          </div>
        </div>

        {/* High Risk Cases */}
        <div className="p-4 rounded-xl bg-red-950/20 border border-red-600/30 shadow-sm">
          <div className="flex items-center justify-between text-red-400">
            <span className="text-[11px] font-bold uppercase tracking-wider">High Risk</span>
            <ShieldAlert className="w-4 h-4" />
          </div>
          <div className="text-2xl font-black text-red-400 font-mono mt-2">
            {stats?.high_risk_cases || 0}
          </div>
          <div className="text-[10px] text-red-300/80 mt-1 font-medium">
            Mandatory human verification
          </div>
        </div>

        {/* Tampering Flags */}
        <div className="p-4 rounded-xl bg-slate-900/80 border border-[#24365d] shadow-sm">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] font-bold uppercase tracking-wider">Tamper Flags</span>
            <Scan className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-black text-purple-300 font-mono mt-2">
            {stats?.tampering_detected_count || 0}
          </div>
          <div className="text-[10px] text-slate-400 mt-1">ELA & noise anomalies</div>
        </div>

        {/* Avg Processing Time */}
        <div className="p-4 rounded-xl bg-slate-900/80 border border-[#24365d] shadow-sm">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] font-bold uppercase tracking-wider">Avg Latency</span>
            <Clock className="w-4 h-4 text-sky-400" />
          </div>
          <div className="text-2xl font-black text-white font-mono mt-2">
            {stats?.avg_processing_time_sec ? `${stats.avg_processing_time_sec}s` : "2.6s"}
          </div>
          <div className="text-[10px] text-slate-400 mt-1">10-step full analysis</div>
        </div>
      </div>

      {/* Secondary Signal Telemetry */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-3.5 rounded-lg bg-slate-900/60 border border-[#24365d] flex items-center justify-between">
          <div>
            <div className="text-xs text-slate-400">Biometric Alerts</div>
            <div className="text-lg font-bold text-white font-mono">
              {stats?.face_mismatch_alerts || 0}
            </div>
          </div>
          <UserX className="w-5 h-5 text-amber-400 opacity-80" />
        </div>
        <div className="p-3.5 rounded-lg bg-slate-900/60 border border-[#24365d] flex items-center justify-between">
          <div>
            <div className="text-xs text-slate-400">Expired Documents</div>
            <div className="text-lg font-bold text-white font-mono">
              {stats?.expired_documents_count || 0}
            </div>
          </div>
          <CalendarX className="w-5 h-5 text-red-400 opacity-80" />
        </div>
        <div className="p-3.5 rounded-lg bg-slate-900/60 border border-[#24365d] flex items-center justify-between">
          <div>
            <div className="text-xs text-slate-400">Low Risk Cases</div>
            <div className="text-lg font-bold text-emerald-400 font-mono">
              {stats?.low_risk_cases || 0}
            </div>
          </div>
          <FileCheck className="w-5 h-5 text-emerald-400 opacity-80" />
        </div>
        <div className="p-3.5 rounded-lg bg-slate-900/60 border border-[#24365d] flex items-center justify-between">
          <div>
            <div className="text-xs text-slate-400">Average Risk Index</div>
            <div className="text-lg font-bold text-sky-400 font-mono">
              {stats?.average_risk_score || 24.6} / 100
            </div>
          </div>
          <TrendingUp className="w-5 h-5 text-sky-400 opacity-80" />
        </div>
      </div>

      {/* Interactive Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Weekly Screening Volume */}
        <div className="lg:col-span-8 p-5 rounded-2xl bg-slate-900/90 border border-[#24365d]">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                Screening Volume Trend
              </h3>
              <p className="text-xs text-slate-400">Daily processed vs flagged credentials</p>
            </div>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stats?.screening_volume_trend || []}>
                <XAxis dataKey="day" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip
                  contentStyle={{ backgroundColor: "#0f172a", borderColor: "#24365d", borderRadius: 8, fontSize: 12 }}
                />
                <Bar dataKey="screened" fill="#3b82f6" radius={[4, 4, 0, 0]} name="Screened" />
                <Bar dataKey="flagged" fill="#ef4444" radius={[4, 4, 0, 0]} name="Flagged" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Risk Distribution Donut */}
        <div className="lg:col-span-4 p-5 rounded-2xl bg-slate-900/90 border border-[#24365d]">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-1">
            Risk Tier Distribution
          </h3>
          <p className="text-xs text-slate-400 mb-4">Proportion across low, medium & high tiers</p>
          <div className="h-64 flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={stats?.risk_distribution || []}
                  dataKey="count"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={80}
                  paddingAngle={4}
                >
                  {(stats?.risk_distribution || []).map((entry: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={entry.color || "#3b82f6"} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: "#0f172a", borderColor: "#24365d", borderRadius: 8, fontSize: 12 }}
                />
                <Legend
                  verticalAlign="bottom"
                  height={36}
                  wrapperStyle={{ fontSize: 11, color: "#94a3b8" }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Detection Categories Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="p-5 rounded-2xl bg-slate-900/90 border border-[#24365d]">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-1">
            Tampering & Detection Categories
          </h3>
          <p className="text-xs text-slate-400 mb-4">Breakdown of specific anomalies detected</p>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart layout="vertical" data={stats?.detection_categories || []}>
                <XAxis type="number" stroke="#64748b" fontSize={11} />
                <YAxis dataKey="category" type="category" stroke="#94a3b8" fontSize={11} width={130} />
                <Tooltip
                  contentStyle={{ backgroundColor: "#0f172a", borderColor: "#24365d", borderRadius: 8, fontSize: 12 }}
                />
                <Bar dataKey="count" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900/90 border border-[#24365d]">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-1">
            Documents by Credential Class
          </h3>
          <p className="text-xs text-slate-400 mb-4">Passports, Visas, National IDs & Licences</p>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stats?.document_types || []}>
                <XAxis dataKey="type" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip
                  contentStyle={{ backgroundColor: "#0f172a", borderColor: "#24365d", borderRadius: 8, fontSize: 12 }}
                />
                <Bar dataKey="count" fill="#0ea5e9" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Recent Screening Queue Table */}
      <div className="p-6 rounded-2xl bg-slate-900/90 border border-[#24365d] space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-white">Recent Screening Cases</h3>
            <p className="text-xs text-slate-400">Live feed of processed documents requiring scrutiny</p>
          </div>
          <Link
            href="/cases"
            className="text-xs font-semibold text-blue-400 hover:text-blue-300 flex items-center gap-1"
          >
            <span>View All Cases Queue</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="border-b border-[#24365d] text-slate-400 uppercase text-[10px] tracking-wider font-semibold">
              <tr>
                <th className="py-3 px-3">Case ID</th>
                <th className="py-3 px-3">Credential Type</th>
                <th className="py-3 px-3">Risk Tier</th>
                <th className="py-3 px-3">Score</th>
                <th className="py-3 px-3">Confidence</th>
                <th className="py-3 px-3">Status</th>
                <th className="py-3 px-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1e2f50]">
              {recentCases.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500">
                    No cases recorded yet. Run a scan or launch a demo scenario above.
                  </td>
                </tr>
              ) : (
                recentCases.map((c) => {
                  const rColor = riskColors[c.risk_level] || "#94a3b8";
                  return (
                    <tr key={c.id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="py-3 px-3 font-mono font-bold text-white">
                        {c.case_number}
                      </td>
                      <td className="py-3 px-3 font-semibold text-slate-300">
                        {c.document_type}
                      </td>
                      <td className="py-3 px-3">
                        <span
                          className="px-2 py-0.5 rounded text-[11px] font-bold"
                          style={{
                            backgroundColor: `${rColor}20`,
                            color: rColor,
                            border: `1px solid ${rColor}50`,
                          }}
                        >
                          {c.risk_level}
                        </span>
                      </td>
                      <td className="py-3 px-3 font-mono text-slate-200">
                        {c.risk_score} / 100
                      </td>
                      <td className="py-3 px-3 text-slate-400 font-mono">
                        {Math.round(c.confidence * 100)}%
                      </td>
                      <td className="py-3 px-3">
                        <span
                          className={`text-[11px] font-medium px-2 py-0.5 rounded ${
                            c.status === "COMPLETED"
                              ? "text-emerald-400 bg-emerald-500/10"
                              : c.status === "REVIEW_REQUIRED"
                              ? "text-amber-400 bg-amber-500/10"
                              : "text-blue-400 bg-blue-500/10"
                          }`}
                        >
                          {c.status.replace("_", " ")}
                        </span>
                      </td>
                      <td className="py-3 px-3 text-right">
                        <Link
                          href={`/cases/${c.id}`}
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-blue-600/20 hover:bg-blue-600/40 text-blue-300 border border-blue-500/30 text-xs font-semibold transition-colors"
                        >
                          <span>Investigate</span>
                          <ArrowUpRight className="w-3 h-3" />
                        </Link>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
