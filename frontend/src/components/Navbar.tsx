"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  Shield,
  FileSearch,
  LayoutDashboard,
  FolderGit2,
  PlayCircle,
  Network,
  Settings,
  LogOut,
  UserCheck,
  Activity,
  Layers,
  RefreshCw,
  Check,
} from "lucide-react";
import { api } from "@/lib/api";

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [refreshState, setRefreshState] = useState<"idle" | "refreshing" | "refreshed">("idle");

  const handleGlobalRefresh = () => {
    if (refreshState !== "idle") return;
    setRefreshState("refreshing");
    try {
      window.dispatchEvent(new CustomEvent("trustid:refresh"));
    } catch {}
    setTimeout(() => {
      setRefreshState("refreshed");
      setTimeout(() => {
        setRefreshState("idle");
      }, 1500);
    }, 600);
  };

  useEffect(() => {
    const stored = localStorage.getItem("trustid_user");
    if (stored) {
      try {
        setUser(JSON.parse(stored));
      } catch {}
    } else {
      // Default to verifier demo role
      setUser({ role: "VERIFIER", full_name: "Inspector Nair", username: "verifier" });
    }
  }, []);

  const handleLogout = () => {
    api.logout();
    router.push("/login");
  };

  const navItems = [
    { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { label: "Screen Document", href: "/screen", icon: FileSearch },
    { label: "Cases Queue", href: "/cases", icon: FolderGit2 },
    { label: "Interactive Demo", href: "/demo", icon: PlayCircle },
    { label: "Architecture", href: "/architecture", icon: Layers },
    { label: "System Health", href: "/admin/system", icon: Activity },
    { label: "Settings", href: "/admin/settings", icon: Settings },
  ];

  return (
    <header className="sticky top-0 z-50 border-b border-slate-200 bg-white/95 backdrop-blur-md shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-3 group">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center text-white shadow-md shadow-blue-500/20 group-hover:scale-105 transition-transform">
              <Shield className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-lg tracking-wider text-slate-900">TRUST-ID</span>
                <span className="text-[10px] font-bold uppercase tracking-widest px-1.5 py-0.5 rounded bg-blue-100 text-blue-700 border border-blue-200">
                  SIH 2026
                </span>
              </div>
              <p className="text-[11px] text-slate-500 -mt-0.5 tracking-tight font-medium">
                MHA Identity Screening Command
              </p>
            </div>
          </Link>

          {/* Navigation Links */}
          <nav className="hidden lg:flex items-center gap-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold tracking-wide transition-all ${
                    isActive
                      ? "bg-blue-50 text-blue-700 border border-blue-200 shadow-xs"
                      : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>

          {/* User profile & Network pill */}
          <div className="flex items-center gap-3">
            <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-700 text-[11px] font-mono font-semibold">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span>CHAIN: VERIFIED</span>
            </div>

            {/* TOP-RIGHT REFRESH BUTTON (Lucide RefreshCw) */}
            <button
              type="button"
              onClick={handleGlobalRefresh}
              disabled={refreshState !== "idle"}
              title="Refresh and reload current data from backend"
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold font-mono transition-all border shadow-xs ${
                refreshState === "refreshing"
                  ? "bg-blue-50 text-blue-700 border-blue-300 cursor-wait"
                  : refreshState === "refreshed"
                  ? "bg-emerald-50 text-emerald-700 border-emerald-300"
                  : "bg-white hover:bg-slate-50 text-slate-700 hover:text-slate-900 border-slate-300 hover:border-slate-400"
              }`}
            >
              {refreshState === "refreshing" ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin text-blue-600" />
                  <span>↻ Refreshing...</span>
                </>
              ) : refreshState === "refreshed" ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-600" />
                  <span>✓ Refreshed</span>
                </>
              ) : (
                <>
                  <RefreshCw className="w-3.5 h-3.5 text-slate-500" />
                  <span>↻ Refresh</span>
                </>
              )}
            </button>

            {user ? (
              <div className="flex items-center gap-2 pl-2 border-l border-slate-200">
                <div className="text-right hidden md:block">
                  <div className="text-xs font-bold text-slate-800 leading-none">{user.full_name || user.username}</div>
                  <div className="text-[10px] text-blue-600 font-mono font-semibold uppercase">{user.role}</div>
                </div>
                <Link
                  href="/login"
                  title="Switch Role or Logout"
                  className="p-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-600 hover:text-slate-900 border border-slate-200 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                </Link>
              </div>
            ) : (
              <Link
                href="/login"
                className="px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold transition-colors"
              >
                Sign In
              </Link>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
