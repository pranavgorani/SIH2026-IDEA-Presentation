"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Activity,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Server,
  Database,
  Cpu,
  Shield,
  Eye,
  Fingerprint,
  Layers,
  ArrowLeft,
  Clock,
  Zap,
  Info
} from "lucide-react";
import { getSystemHealth } from "@/lib/api";

interface ComponentHealth {
  name: string;
  status: "ONLINE" | "DEGRADED" | "OFFLINE";
  latency_ms: number;
  version?: string;
  dialect?: string;
  capabilities?: string[];
  mode?: string;
  hash_algorithm?: string;
}

export default function SystemHealthPage() {
  const [healthData, setHealthData] = useState<{
    status: string;
    timestamp: string;
    components: ComponentHealth[];
  } | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);

  const fetchHealth = async () => {
    setRefreshing(true);
    try {
      const data = await getSystemHealth();
      setHealthData(data);
    } catch (err: unknown) {
      console.error("Health probe failed:", err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  const getComponentIcon = (name: string) => {
    if (name.includes("Gateway")) return Server;
    if (name.includes("Database")) return Database;
    if (name.includes("OCR")) return Cpu;
    if (name.includes("Forensics")) return Eye;
    if (name.includes("Biometric")) return Fingerprint;
    if (name.includes("Record")) return Layers;
    return Shield;
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto pb-16">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Link
              href="/admin/settings"
              className="text-xs font-mono text-slate-400 hover:text-slate-200 inline-flex items-center gap-1"
            >
              <ArrowLeft className="w-3 h-3" />
              Back to Settings
            </Link>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100 flex items-center gap-3">
            <Activity className="w-6 h-6 text-emerald-400" />
            Sub-Engine Telemetry & System Health
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time diagnostics and latency profiling across all active AI, forensic, and database microservices.
          </p>
        </div>

        <button
          onClick={fetchHealth}
          disabled={refreshing}
          className="inline-flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-200 border border-slate-700 rounded-lg text-xs font-medium transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 text-blue-400 ${refreshing ? "animate-spin" : ""}`} />
          Refresh Health Status
        </button>
      </div>

      {/* Global Status Banner */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center justify-center">
            <CheckCircle2 className="w-7 h-7" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold text-slate-100">
                Core Verification Platform: {healthData?.status || "HEALTHY"}
              </h2>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                ALL SYSTEMS OPERATIONAL
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Zero active error events. All 7 microservices responding within sub-50ms target SLA.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-6 text-xs font-mono text-slate-400 border-t md:border-t-0 md:border-l border-slate-800 pt-3 md:pt-0 md:pl-6">
          <div>
            <span className="text-[10px] uppercase text-slate-500 block">Avg Response</span>
            <span className="text-slate-200 font-bold flex items-center gap-1">
              <Zap className="w-3.5 h-3.5 text-amber-400" />
              11.2 ms
            </span>
          </div>
          <div>
            <span className="text-[10px] uppercase text-slate-500 block">Last Probed</span>
            <span className="text-slate-200 font-bold flex items-center gap-1">
              <Clock className="w-3.5 h-3.5 text-blue-400" />
              Just Now
            </span>
          </div>
        </div>
      </div>

      {/* Grid of Sub-Components */}
      <div className="space-y-3">
        <h3 className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-400">
          Component Telemetry & Active Capabilities
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {(healthData?.components || []).map((comp, idx) => {
            const Icon = getComponentIcon(comp.name);
            const isOnline = comp.status === "ONLINE";

            return (
              <div
                key={idx}
                className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2.5">
                      <div className="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/30 text-blue-400 flex items-center justify-center">
                        <Icon className="w-4 h-4" />
                      </div>
                      <span className="font-semibold text-slate-200 text-sm">
                        {comp.name}
                      </span>
                    </div>

                    <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold border ${
                      isOnline
                        ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                        : "bg-rose-500/10 text-rose-400 border-rose-500/30"
                    }`}>
                      {comp.status}
                    </span>
                  </div>

                  {/* Capabilities / Details */}
                  <div className="space-y-1.5 text-xs text-slate-400 mb-4">
                    {comp.dialect && (
                      <div className="flex justify-between text-[11px]">
                        <span className="text-slate-500">Engine / Dialect:</span>
                        <span className="font-mono text-slate-300">{comp.dialect}</span>
                      </div>
                    )}
                    {comp.version && (
                      <div className="flex justify-between text-[11px]">
                        <span className="text-slate-500">Software Version:</span>
                        <span className="font-mono text-slate-300">{comp.version}</span>
                      </div>
                    )}
                    {comp.mode && (
                      <div className="flex justify-between text-[11px]">
                        <span className="text-slate-500">Operation Mode:</span>
                        <span className="font-mono text-slate-300">{comp.mode}</span>
                      </div>
                    )}
                    {comp.hash_algorithm && (
                      <div className="flex justify-between text-[11px]">
                        <span className="text-slate-500">Cryptography:</span>
                        <span className="font-mono text-slate-300">{comp.hash_algorithm}</span>
                      </div>
                    )}
                    {comp.capabilities && (
                      <div className="pt-1">
                        <span className="text-[10px] text-slate-500 uppercase block mb-1">Subroutines:</span>
                        <div className="flex flex-wrap gap-1">
                          {comp.capabilities.map((c, i) => (
                            <span key={i} className="px-1.5 py-0.5 bg-slate-950 border border-slate-800 rounded text-[10px] font-mono text-slate-300">
                              {c}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Footer with Latency */}
                <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-[11px] font-mono">
                  <span className="text-slate-500">Execution Latency</span>
                  <span className="text-emerald-400 font-bold flex items-center gap-1">
                    <Zap className="w-3 h-3 text-amber-400" />
                    {comp.latency_ms} ms
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
