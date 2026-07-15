"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  BookOpen,
  Network,
  Wrench,
  BarChart2,
  Clock,
} from "lucide-react";

const navItems = [
  { name: "Dashboard",    href: "/",           icon: Activity },
  { name: "Query",        href: "/",           icon: Activity,  alias: true },
  { name: "Graph",        href: "/graph",      icon: Network },
  { name: "Maintenance",  href: "/maintenance",icon: Wrench },
  { name: "Ingest",       href: "/ingest",     icon: BookOpen },
  { name: "Metrics",      href: "/dashboard",  icon: BarChart2 },
];

// Deduplicate: Dashboard & Query both point to "/"
const dedupedNav = [
  { name: "Dashboard",    href: "/",            icon: Activity },
  { name: "Graph",        href: "/graph",       icon: Network },
  { name: "Maintenance",  href: "/maintenance", icon: Wrench },
  { name: "Ingest",       href: "/ingest",      icon: BookOpen },
  { name: "Metrics",      href: "/dashboard",   icon: BarChart2 },
];

export default function NavigationWrapper({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const [time, setTime] = React.useState("");

  React.useEffect(() => {
    const fmt = () =>
      new Date().toLocaleTimeString("en-IN", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: false,
        timeZone: "Asia/Kolkata",
      });
    setTime(fmt());
    const id = setInterval(() => setTime(fmt()), 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="flex min-h-screen">
      {/* ── Sidebar ─────────────────────────────────── */}
      <aside className="w-56 shrink-0 border-r border-[#27272a] bg-[#09090b] flex flex-col">
        {/* Logo */}
        <div className="px-5 py-5 border-b border-[#27272a] flex items-center gap-3">
          <div className="h-8 w-8 rounded-[6px] bg-[#22d3ee] flex items-center justify-center shrink-0">
            <span className="text-[#09090b] font-black text-xs tracking-tight">
              TG
            </span>
          </div>
          <div className="min-w-0">
            <p className="text-[13px] font-semibold tracking-tight text-[#fafafa] truncate">
              TeevrGati
            </p>
            <p className="text-[10px] text-[#52525b] truncate">AI Diagnostics</p>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 flex flex-col gap-0.5">
          {dedupedNav.map((item) => {
            const Icon = item.icon;
            const isActive =
              pathname === item.href ||
              (item.href !== "/" && pathname.startsWith(item.href));
            return (
              <Link
                key={item.href + item.name}
                href={item.href}
                className={`flex items-center gap-2.5 px-3 py-2 rounded-[6px] text-[13px] font-medium transition-colors duration-150 ${
                  isActive
                    ? "bg-[#22d3ee]/10 text-[#22d3ee]"
                    : "text-[#71717a] hover:text-[#fafafa] hover:bg-[#18181b]"
                }`}
              >
                <Icon
                  className={`h-4 w-4 shrink-0 ${
                    isActive ? "text-[#22d3ee]" : "text-[#52525b]"
                  }`}
                />
                {item.name}
                {isActive && (
                  <span className="ml-auto h-1.5 w-1.5 rounded-full bg-[#22d3ee]" />
                )}
              </Link>
            );
          })}
        </nav>

        {/* Footer status */}
        <div className="px-4 py-4 border-t border-[#27272a]">
          <div className="flex items-center gap-2 mb-1">
            <span className="h-1.5 w-1.5 rounded-full bg-[#22d3ee] animate-pulse" />
            <span className="text-[10px] text-[#52525b] font-medium uppercase tracking-widest">
              Engine Online
            </span>
          </div>
          <p className="text-[10px] text-[#3f3f46] mono">{time} IST</p>
        </div>
      </aside>

      {/* ── Main Area ───────────────────────────────── */}
      <div className="flex-1 flex flex-col min-w-0 bg-[#09090b]">
        {/* Top bar */}
        <header className="h-12 border-b border-[#27272a] flex items-center justify-between px-6 shrink-0">
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-medium text-[#52525b] uppercase tracking-widest">
              BPCL Mathura Refinery
            </span>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
              <span className="text-[10px] text-[#52525b]">Online</span>
            </div>
            <div className="flex items-center gap-1.5 text-[#3f3f46]">
              <Clock className="h-3 w-3" />
              <span className="mono text-[10px]">{time}</span>
            </div>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-y-auto">{children}</main>
      </div>
    </div>
  );
}
