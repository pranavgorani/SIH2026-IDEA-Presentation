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
} from "lucide-react";
import { api } from "@/lib/api";

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<any>(null);

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
    <header className="sticky top-0 z-50 border-b border-[#24365d] bg-[#0b1329]/95 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-3 group">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center text-white shadow-lg shadow-blue-500/20 group-hover:scale-105 transition-transform">
              <Shield className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-lg tracking-wider text-white">TRUST-ID</span>
                <span className="text-[10px] font-bold uppercase tracking-widest px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30">
                  SIH 2026
                </span>
              </div>
              <p className="text-[11px] text-slate-400 -mt-0.5 tracking-tight font-medium">
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
                      ? "bg-blue-600/20 text-blue-400 border border-blue-500/40 shadow-sm shadow-blue-500/20"
                      : "text-slate-300 hover:text-white hover:bg-slate-800/60"
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
            <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-[11px] font-mono font-semibold">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>CHAIN: VERIFIED</span>
            </div>

            {user ? (
              <div className="flex items-center gap-2 pl-2 border-l border-[#24365d]">
                <div className="text-right hidden md:block">
                  <div className="text-xs font-bold text-white leading-none">{user.full_name || user.username}</div>
                  <div className="text-[10px] text-blue-400 font-mono font-semibold uppercase">{user.role}</div>
                </div>
                <Link
                  href="/login"
                  title="Switch Role or Logout"
                  className="p-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white border border-[#24365d] transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                </Link>
              </div>
            ) : (
              <Link
                href="/login"
                className="px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold transition-colors"
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
