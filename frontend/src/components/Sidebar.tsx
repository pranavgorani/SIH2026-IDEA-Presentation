"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  Shield,
  LayoutDashboard,
  ScanLine,
  FolderGit2,
  Sparkles,
  Layers,
  Sliders,
  Activity,
  LogOut,
  UserCheck,
  ChevronRight,
  Menu,
  X,
  Lock,
  Cpu,
  Fingerprint
} from "lucide-react";
import { api } from "@/lib/api";

interface SidebarProps {
  // Optional children if wrapping
}

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem("trustid_user");
    if (stored) {
      try {
        setUser(JSON.parse(stored));
      } catch {}
    } else {
      setUser({ role: "VERIFIER", full_name: "Inspector Nair", username: "verifier" });
    }
  }, []);

  // Close mobile drawer on route change
  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  const handleLogout = () => {
    api.logout();
    router.push("/login");
  };

  const role = (user?.role || "VERIFIER").toUpperCase();

  const getNavGroups = () => {
    if (role === "ADMIN") {
      return [
        {
          title: "ADMIN COMMAND CONSOLE",
          items: [
            { label: "Admin Dashboard", href: "/dashboard", icon: LayoutDashboard },
            { label: "Cases & Reviews", href: "/cases", icon: FolderGit2 },
            { label: "Reports Download Center", href: "/reports", icon: Sparkles, badge: "NEW" },
            { label: "Guided Demo Benchmark", href: "/demo", icon: Cpu, badge: "SIH 2026" },
          ],
        },
        {
          title: "SYSTEM & AI CONFIGURATION",
          items: [
            { label: "Risk Configuration", href: "/admin/settings", icon: Sliders },
            { label: "AI & Verification Providers", href: "/admin/settings", icon: Cpu },
            { label: "System Health & Telemetry", href: "/admin/system", icon: Activity },
            { label: "Security & Architecture", href: "/architecture", icon: Layers },
          ],
        },
      ];
    }

    if (role === "INSPECTOR") {
      return [
        {
          title: "FORENSIC INSPECTION WING",
          items: [
            { label: "Inspection Dashboard", href: "/dashboard", icon: LayoutDashboard },
            { label: "Inspection Queue", href: "/cases", icon: FolderGit2, badge: "Active" },
            { label: "Forensic Evidence & Notes", href: "/cases", icon: Fingerprint },
            { label: "Reports & Audit Exports", href: "/reports", icon: Sparkles, badge: "100-Checks" },
          ],
        },
        {
          title: "AUDIT & INVESTIGATION",
          items: [
            { label: "Investigation Timeline", href: "/cases", icon: Activity },
            { label: "Cryptographic Ledger", href: "/architecture", icon: Lock },
            { label: "Guided Demo Benchmark", href: "/demo", icon: Cpu, badge: "SIH 2026" },
          ],
        },
      ];
    }

    // Default: VERIFIER
    return [
      {
        title: "OPERATIONAL SCREENING",
        items: [
          { label: "Command Dashboard", href: "/dashboard", icon: LayoutDashboard },
          { label: "Screen Document", href: "/screen", icon: ScanLine, badge: "Scanner" },
          { label: "Review Queue & Cases", href: "/cases", icon: FolderGit2 },
          { label: "Reports Download Center", href: "/reports", icon: Sparkles, badge: "100-Checks" },
          { label: "Guided Demo Benchmark", href: "/demo", icon: Cpu, badge: "SIH 2026" },
        ],
      },
      {
        title: "VERIFICATION INTEGRITY",
        items: [
          { label: "System Architecture", href: "/architecture", icon: Layers },
          { label: "Tamper-Evident Ledger", href: "/admin/system", icon: Activity },
        ],
      },
    ];
  };

  const navGroups = getNavGroups();

  const sidebarContent = (
    <div className="flex flex-col h-full bg-[#070d1e] border-r border-[#24365d] text-slate-200">
      {/* Brand Header */}
      <div className="p-5 border-b border-[#24365d] flex items-center justify-between">
        <Link href="/" className="flex items-center gap-3 group">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center text-white shadow-lg shadow-blue-500/25 group-hover:scale-105 transition-transform">
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-base tracking-wider text-white">TRUST-ID</span>
              <span className="text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30">
                SIH26188
              </span>
            </div>
            <p className="text-[10px] text-slate-400 tracking-tight font-medium">
              Ministry of Home Affairs
            </p>
          </div>
        </Link>
        <button
          onClick={() => setMobileOpen(false)}
          className="md:hidden text-slate-400 hover:text-white p-1 rounded"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Security Status Ribbon */}
      <div className="px-5 py-2.5 bg-[#091227] border-b border-[#1b2b4d] flex items-center justify-between text-[11px] font-mono">
        <div className="flex items-center gap-2 text-emerald-400">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span>SYSTEM ACTIVE</span>
        </div>
        <span className="text-slate-500 text-[10px]">SHA-256 LEDGER</span>
      </div>

      {/* Navigation Links */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
        {navGroups.map((group, idx) => (
          <div key={idx}>
            <div className="px-3 mb-2 text-[10px] font-mono font-semibold uppercase tracking-wider text-slate-500">
              {group.title}
            </div>
            <div className="space-y-1">
              {group.items.map((item) => {
                const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
                const Icon = item.icon;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium transition-all ${
                      isActive
                        ? "bg-blue-600/20 text-blue-300 border border-blue-500/40 shadow-sm shadow-blue-500/10 font-semibold"
                        : "text-slate-400 hover:text-slate-200 hover:bg-[#0e1b38]"
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <Icon className={`w-4 h-4 ${isActive ? "text-blue-400" : "text-slate-400"}`} />
                      <span>{item.label}</span>
                    </div>
                    {item.badge && (
                      <span className="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-purple-500/20 text-purple-300 border border-purple-500/30">
                        {item.badge}
                      </span>
                    )}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* System Telemetry Micro-Widget */}
      <div className="p-3 mx-3 mb-3 bg-[#0a152d] border border-[#1d2f55] rounded-xl text-[11px] space-y-1.5">
        <div className="flex items-center justify-between text-slate-400">
          <span className="flex items-center gap-1.5">
            <Cpu className="w-3 h-3 text-blue-400" />
            AI Provider
          </span>
          <span className="text-[10px] font-mono text-emerald-400">LOCAL_CV / HYBRID</span>
        </div>
        <div className="flex items-center justify-between text-slate-400">
          <span className="flex items-center gap-1.5">
            <Lock className="w-3 h-3 text-purple-400" />
            Audit Chain
          </span>
          <span className="text-[10px] font-mono text-purple-300">IMMUTABLE</span>
        </div>
      </div>

      {/* User Session & Role Card */}
      <div className="p-4 border-t border-[#24365d] bg-[#050a17]">
        {user ? (
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/30 text-blue-400 flex items-center justify-center">
                <UserCheck className="w-4 h-4" />
              </div>
              <div className="overflow-hidden">
                <div className="text-xs font-semibold text-slate-200 truncate max-w-[110px]">
                  {user.full_name || user.username}
                </div>
                <div className="text-[10px] font-mono text-blue-400 uppercase tracking-wider">
                  {user.role}
                </div>
              </div>
            </div>
            <button
              onClick={handleLogout}
              title="Sign Out"
              className="text-slate-400 hover:text-rose-400 p-1.5 rounded-lg hover:bg-slate-800/80 transition-colors"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <Link
            href="/login"
            className="w-full py-2 px-3 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold flex items-center justify-center gap-2 shadow-sm transition-colors"
          >
            <Lock className="w-3.5 h-3.5" />
            Sign In to Console
          </Link>
        )}
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Persistent Sidebar */}
      <aside className="hidden md:fixed md:inset-y-0 md:left-0 md:flex md:w-64 md:flex-col z-40">
        {sidebarContent}
      </aside>

      {/* Mobile Top Header with Hamburger */}
      <header className="md:hidden sticky top-0 z-50 flex items-center justify-between h-14 px-4 bg-[#070d1e] border-b border-[#24365d]">
        <Link href="/" className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center text-white">
            <Shield className="w-4 h-4" />
          </div>
          <span className="font-extrabold text-sm tracking-wider text-white">TRUST-ID</span>
          <span className="text-[9px] font-mono px-1 py-0.2 rounded bg-blue-500/20 text-blue-400">
            MHA
          </span>
        </Link>
        <button
          onClick={() => setMobileOpen(true)}
          className="text-slate-300 hover:text-white p-1.5 rounded-lg bg-[#0e1b38] border border-[#24365d]"
          aria-label="Open Navigation"
        >
          <Menu className="w-5 h-5" />
        </button>
      </header>

      {/* Mobile Slide-Out Drawer Backdrop */}
      {mobileOpen && (
        <div className="md:hidden fixed inset-0 z-50 flex">
          <div
            className="fixed inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
            onClick={() => setMobileOpen(false)}
          />
          <div className="relative flex-1 flex flex-col max-w-xs w-full shadow-2xl">
            {sidebarContent}
          </div>
        </div>
      )}
    </>
  );
}
