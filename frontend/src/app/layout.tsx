import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/Sidebar";

export const metadata: Metadata = {
  title: "TRUST-ID — AI-Powered Fake Identity & Document Screening System",
  description:
    "Ministry of Home Affairs SIH26188: Production-grade automated identity credential screening platform combining modular OCR, Error Level Analysis (ELA), ICAO 9303 checksums, biometric verification, and tamper-evident SHA-256 audit ledger.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full">
      <body className="min-h-full flex flex-col bg-slate-50 text-slate-900 antialiased selection:bg-blue-600 selection:text-white">
        {/* Left Command-Center Sidebar Navigation */}
        <Sidebar />

        {/* Main Content Area Offset for Desktop Sidebar */}
        <div className="md:pl-64 flex flex-col flex-1 min-h-screen">
          <main className="flex-1 p-4 sm:p-6 lg:p-8">{children}</main>

          <footer className="border-t border-slate-200 bg-white py-6 px-4 sm:px-8 text-center text-xs text-slate-600 shadow-sm">
            <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <span className="font-bold text-slate-900 tracking-wide">TRUST-ID</span>
                <span>— Ministry of Home Affairs | SIH2026 Problem ID: SIH26188</span>
              </div>
              <div className="text-slate-500 text-[11px]">
                Theme: Blockchain & Cybersecurity | Evaluation Benchmark with Synthetic Data
              </div>
              <div className="text-[11px] text-emerald-600 font-mono font-medium">
                ● AI Safety Protocol: Human-in-the-Loop Active
              </div>
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}
