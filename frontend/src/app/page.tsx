import Link from "next/link";
import {
  Shield,
  FileCheck,
  Search,
  Cpu,
  Lock,
  Eye,
  FileSearch,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Database,
  Layers,
  Fingerprint,
  FileText,
  Clock,
  Sparkles,
  BarChart3,
  Server,
  Terminal,
} from "lucide-react";

export default function LandingPage() {
  return (
    <div className="flex flex-col min-h-screen">
      {/* Hero Section */}
      <section className="relative overflow-hidden pt-12 pb-20 lg:pt-20 lg:pb-28 border-b border-[#24365d]">
        <div className="absolute inset-0 -z-10 bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(59,130,246,0.18),rgba(255,255,255,0))]" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/30 text-blue-400 text-xs font-semibold uppercase tracking-wider mb-6">
              <span className="w-2 h-2 rounded-full bg-blue-400 animate-ping" />
              Smart India Hackathon 2026 • Ministry of Home Affairs
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black text-white tracking-tight leading-[1.15]">
              AI-Powered Identity & <br />
              <span className="bg-gradient-to-r from-blue-400 via-indigo-400 to-sky-300 bg-clip-text text-transparent">
                Document Screening System
              </span>
            </h1>

            <p className="mt-4 text-lg font-mono text-cyan-300 tracking-wide">
              &quot;Detect. Verify. Explain. Secure.&quot;
            </p>

            <p className="mt-4 text-base sm:text-lg text-slate-300 leading-relaxed">
              An enterprise AI-assisted document-forensics platform that screens government-issued
              credentials in seconds by combining{" "}
              <strong className="text-white font-semibold">OCR, visual tamper detection (ELA), rule validation, biometric comparison, and record cross-checking</strong>{" "}
              into one explainable, tamper-evident audit ledger.
            </p>

            {/* CTAs */}
            <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
              <Link
                href="/screen"
                className="px-6 py-3.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold text-sm shadow-lg shadow-blue-500/25 flex items-center gap-2 transition-all hover:scale-[1.02]"
              >
                <span>Start Screening</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                href="/demo"
                className="px-6 py-3.5 rounded-xl bg-slate-800/90 hover:bg-slate-700/90 text-white font-bold text-sm border border-[#24365d] shadow-md flex items-center gap-2 transition-all hover:scale-[1.02]"
              >
                <Cpu className="w-4 h-4 text-amber-400" />
                <span>Launch Interactive Demo</span>
              </Link>
              <Link
                href="/dashboard"
                className="px-6 py-3.5 rounded-xl bg-[#111e38] hover:bg-[#152445] text-slate-200 font-semibold text-sm border border-[#24365d] flex items-center gap-2 transition-all"
              >
                <BarChart3 className="w-4 h-4 text-sky-400" />
                <span>Command Dashboard</span>
              </Link>
            </div>

            {/* Key Telemetry Badges */}
            <div className="mt-12 grid grid-cols-2 md:grid-cols-4 gap-4 pt-8 border-t border-[#24365d]/60 text-left">
              <div className="p-3 rounded-lg bg-slate-900/60 border border-[#24365d]">
                <div className="text-2xl font-black text-white font-mono">&lt; 3.0s</div>
                <div className="text-xs text-slate-400 mt-0.5">Automated Multi-Layer Scan</div>
              </div>
              <div className="p-3 rounded-lg bg-slate-900/60 border border-[#24365d]">
                <div className="text-2xl font-black text-emerald-400 font-mono">100%</div>
                <div className="text-xs text-slate-400 mt-0.5">SHA-256 Audit Integrity</div>
              </div>
              <div className="p-3 rounded-lg bg-slate-900/60 border border-[#24365d]">
                <div className="text-2xl font-black text-sky-400 font-mono">5 Layers</div>
                <div className="text-xs text-slate-400 mt-0.5">Orthogonal Signal Defense</div>
              </div>
              <div className="p-3 rounded-lg bg-slate-900/60 border border-[#24365d]">
                <div className="text-2xl font-black text-purple-400 font-mono">Safety-1st</div>
                <div className="text-xs text-slate-400 mt-0.5">Human-in-the-Loop Protocol</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Real-World Problem & Government Context */}
      <section className="py-16 bg-[#091024] border-b border-[#24365d]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
            <div className="lg:col-span-6 space-y-4">
              <div className="text-xs font-bold text-red-400 uppercase tracking-widest flex items-center gap-2">
                <AlertTriangle className="w-4 h-4" />
                The Problem Landscape
              </div>
              <h2 className="text-3xl font-extrabold text-white tracking-tight">
                Sophisticated Forgeries, Leakages, and The Human Bottleneck
              </h2>
              <p className="text-slate-300 text-sm leading-relaxed">
                Manual border checks and enrolment desks take <strong className="text-white">18+ minutes per document</strong> with tired eyes catching only 85–92% of forgeries. Meanwhile, modern digital editing and AI generative tools make fraudulent photo replacement, text alteration, and fake visas visually imperceptible.
              </p>
              <div className="p-4 rounded-xl bg-red-950/20 border border-red-900/40 text-xs text-red-200 space-y-2">
                <div className="font-bold flex items-center gap-2 text-red-400">
                  <span>🏛 MHA & National Economic Context:</span>
                </div>
                <p>
                  India cancelled <strong className="text-white">2.95 crore (29.5M) duplicate and fake ration cards</strong> in three years — draining an estimated <strong className="text-white">₹17,000 crore annually</strong> from the public exchequer. Layered multi-signal automated screening stops duplicate identity fraud at enrolment, before taxpayer funds are lost.
                </p>
              </div>
            </div>

            <div className="lg:col-span-6 grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="p-5 rounded-xl bg-slate-900/70 border border-[#24365d] hover:border-blue-500/50 transition-colors">
                <Clock className="w-6 h-6 text-sky-400 mb-3" />
                <h3 className="font-bold text-white text-base">78% Speed Reduction</h3>
                <p className="text-xs text-slate-400 mt-1">
                  Replaces stacks of paper copies and manual cross-referencing with instant computer-vision screening.
                </p>
              </div>
              <div className="p-5 rounded-xl bg-slate-900/70 border border-[#24365d] hover:border-emerald-500/50 transition-colors">
                <CheckCircle2 className="w-6 h-6 text-emerald-400 mb-3" />
                <h3 className="font-bold text-white text-base">Fewer Genuine Rejections</h3>
                <p className="text-xs text-slate-400 mt-1">
                  Evidence-first verification avoids turning away genuine citizens due to minor scan artifacts or lighting variance.
                </p>
              </div>
              <div className="p-5 rounded-xl bg-slate-900/70 border border-[#24365d] hover:border-purple-500/50 transition-colors">
                <Layers className="w-6 h-6 text-purple-400 mb-3" />
                <h3 className="font-bold text-white text-base">5 Weak Signals → 1 Strong Verdict</h3>
                <p className="text-xs text-slate-400 mt-1">
                  Layered AI signals lift fraud detection accuracy by ~61% over isolated single-layer checks (AU10TIX).
                </p>
              </div>
              <div className="p-5 rounded-xl bg-slate-900/70 border border-[#24365d] hover:border-amber-500/50 transition-colors">
                <Lock className="w-6 h-6 text-amber-400 mb-3" />
                <h3 className="font-bold text-white text-base">Tamper-Evident Ledger</h3>
                <p className="text-xs text-slate-400 mt-1">
                  Every scan, flag, and human review is cryptographically linked with SHA-256 predecessor hashing.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* TRUST-ID 5-Step Workflow from Presentation */}
      <section className="py-16 border-b border-[#24365d]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-12">
            <h2 className="text-xs font-bold text-blue-400 uppercase tracking-widest">
              Core Workflow
            </h2>
            <h3 className="text-3xl font-extrabold text-white mt-1">
              SCAN → DETECT → VALIDATE → SCORE → REVIEW
            </h3>
            <p className="text-slate-400 text-sm mt-2">
              The exact operational lifecycle specified in the reference architecture.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            {[
              {
                step: "01",
                name: "SCAN",
                desc: "Extract text, layout, and ICAO 9303 MRZ zones with modular OCR.",
                color: "from-blue-600 to-cyan-600",
                icon: FileSearch,
              },
              {
                step: "02",
                name: "DETECT",
                desc: "Run Error Level Analysis (ELA), edge discontinuity & noise variance forensics.",
                color: "from-cyan-600 to-teal-600",
                icon: Eye,
              },
              {
                step: "03",
                name: "VALIDATE",
                desc: "Verify chronological logic, expiry, MRZ checksums & cross-field integrity.",
                color: "from-teal-600 to-emerald-600",
                icon: FileCheck,
              },
              {
                step: "04",
                name: "SCORE",
                desc: "Synthesize signals into an explainable 0–100 risk score and evidence list.",
                color: "from-emerald-600 to-indigo-600",
                icon: Cpu,
              },
              {
                step: "05",
                name: "REVIEW",
                desc: "Escalate edge cases and high-risk flags to an authorized human verifier.",
                color: "from-indigo-600 to-purple-600",
                icon: Shield,
              },
            ].map((item, idx) => {
              const Icon = item.icon;
              return (
                <div
                  key={idx}
                  className="p-5 rounded-xl bg-slate-900/60 border border-[#24365d] relative overflow-hidden group hover:border-blue-500/60 transition-all"
                >
                  <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${item.color} flex items-center justify-center text-white mb-3 shadow-md`}>
                    <Icon className="w-4 h-4" />
                  </div>
                  <div className="font-mono text-xs text-slate-500 font-bold">STEP {item.step}</div>
                  <div className="font-extrabold text-white text-base mt-1">{item.name}</div>
                  <p className="text-xs text-slate-400 mt-2 leading-relaxed">{item.desc}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* 5 Verification Layers */}
      <section className="py-16 bg-[#091024] border-b border-[#24365d]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-12">
            <h2 className="text-xs font-bold text-sky-400 uppercase tracking-widest">
              Defense In Depth
            </h2>
            <h3 className="text-3xl font-extrabold text-white mt-1">
              The 5 Orthogonal Verification Layers
            </h3>
            <p className="text-slate-400 text-sm mt-2">
              No single model determines a decision. Every case is grounded in multiple signals.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
            {[
              {
                layer: "Layer 1",
                title: "Document",
                desc: "Format recognition, ISO 7810 aspect ratio, field syntax, and expiry check.",
                features: ["Format match", "Required fields", "Expiry check", "Chronology"],
              },
              {
                layer: "Layer 2",
                title: "Visual Forensics",
                desc: "Computer vision tamper localization, ELA compression disparity, and noise profiles.",
                features: ["ELA Heatmap", "Noise variance", "Edge gradients", "Splice detection"],
              },
              {
                layer: "Layer 3",
                title: "Identity",
                desc: "1:1 biometric facial comparison between credential photo and live presenter.",
                features: ["Face detection", "Landmark alignment", "Quality check", "Similarity score"],
              },
              {
                layer: "Layer 4",
                title: "Records",
                desc: "Pluggable adapters for central issuing databases and consular lists (simulated).",
                features: ["Status check", "Name matching", "Lost/stolen flags", "Adapter architecture"],
              },
              {
                layer: "Layer 5",
                title: "Risk Engine",
                desc: "Configurable multi-signal fusion algorithm that outputs explainable evidence.",
                features: ["0–100 Score", "Positive evidence", "Risk factors", "Advisory action"],
              },
            ].map((l, i) => (
              <div key={i} className="p-5 rounded-xl bg-slate-900/80 border border-[#24365d] flex flex-col justify-between">
                <div>
                  <span className="text-[11px] font-mono font-bold text-blue-400 uppercase tracking-wider">
                    {l.layer}
                  </span>
                  <h4 className="text-lg font-bold text-white mt-1">{l.title}</h4>
                  <p className="text-xs text-slate-400 mt-2 leading-relaxed">{l.desc}</p>
                </div>
                <ul className="mt-4 pt-4 border-t border-[#24365d] space-y-1.5 text-[11px] text-slate-300 font-medium">
                  {l.features.map((f, j) => (
                    <li key={j} className="flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
                      <span>{f}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Safety & Human-in-the-Loop */}
      <section className="py-16 border-b border-[#24365d]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="p-8 rounded-2xl bg-gradient-to-r from-blue-950/40 via-indigo-950/30 to-slate-900 border border-blue-500/30">
            <div className="max-w-3xl">
              <span className="px-2.5 py-1 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 text-[11px] font-bold uppercase tracking-wider">
                MHA Safety & Constitutional Principle
              </span>
              <h2 className="text-2xl sm:text-3xl font-extrabold text-white mt-3">
                AI Informs. Authorized Humans Decide.
              </h2>
              <p className="text-sm text-slate-300 mt-3 leading-relaxed">
                TRUST-ID is strictly architected as an <strong className="text-white">AI-Assisted screening system</strong>. Machine learning models never make irreversible or punitive decisions regarding an individual. Every high-risk alert or borderline ambiguity is routed directly to an authorized human verifier with clear evidence, confidence levels, and interactive forensic heatmaps.
              </p>
              <div className="mt-6 flex flex-wrap gap-4 text-xs font-mono">
                <span className="px-3 py-1.5 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-semibold">
                  ✓ Low Risk (0–30): Eligible for Standard Verification
                </span>
                <span className="px-3 py-1.5 rounded bg-amber-500/10 border border-amber-500/30 text-amber-400 font-semibold">
                  ⚠ Medium Risk (31–60): Human Review Recommended
                </span>
                <span className="px-3 py-1.5 rounded bg-red-500/10 border border-red-500/30 text-red-400 font-semibold">
                  ⛔ High Risk (61–100): Mandatory Human Review
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Supported Credentials & Final CTA */}
      <section className="py-16 bg-[#070d1e]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-xs font-bold text-slate-400 uppercase tracking-widest">
            Ready for Border Control & Enrolment Desks
          </h2>
          <h3 className="text-2xl sm:text-3xl font-black text-white mt-2">
            Supported Identity Document Credentials
          </h3>
          <p className="text-slate-400 text-xs sm:text-sm mt-2 max-w-xl mx-auto">
            Passports • National ID Cards • Visas • Driving Licences • Work & Stay Permits • Travel Authorizations
          </p>

          <div className="mt-8 flex justify-center gap-4">
            <Link
              href="/screen"
              className="px-6 py-3.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-sm shadow-lg shadow-blue-500/30 transition-all"
            >
              Start Live Screening
            </Link>
            <Link
              href="/demo"
              className="px-6 py-3.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-bold text-sm border border-[#24365d] transition-all"
            >
              Test Demo Scenarios
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
