"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  Activity, 
  BookOpen, 
  Layers, 
  Cpu, 
  Settings,
  Wrench,
  Gauge,
  Sun,
  Moon
} from "lucide-react";

export default function NavigationWrapper({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [isLight, setIsLight] = React.useState(false);

  const toggleTheme = () => {
    setIsLight(!isLight);
    if (!isLight) {
      document.documentElement.classList.add("light-theme");
    } else {
      document.documentElement.classList.remove("light-theme");
    }
  };

  const navItems = [
    { name: "Diagnostics Co-Pilot", href: "/", icon: Activity },
    { name: "Self-Healing Graph", href: "/graph", icon: Layers },
    { name: "SOP Ingestion", href: "/ingest", icon: BookOpen },
    { name: "Work Orders & Alerts", href: "/maintenance", icon: Wrench },
    { name: "Compliance & Metrics", href: "/dashboard", icon: Gauge },
  ];

  return (
    <div className="flex min-h-screen">
      {/* Sleek Left Sidebar */}
      <aside className="w-64 border-r border-[#1e293b] bg-[#0d1527] flex flex-col shadow-2xl">
        {/* Header Logo */}
        <div className="p-6 border-b border-[#1e293b] flex items-center gap-3">
          <div className="h-9 w-9 rounded-lg bg-gradient-to-tr from-[#00f5d4] to-[#0072ff] flex items-center justify-center shadow-md">
            <Cpu className="h-5.5 w-5.5 text-[#0b0f19]" />
          </div>
          <div>
            <h1 className="text-sm font-bold tracking-tight bg-gradient-to-r from-white via-[#e2e8f0] to-[#00f5d4] bg-clip-text text-transparent">
              TEEVRGATI PORTAL
            </h1>
            <p className="text-[10px] text-[#64748b]">v1.2 (Self-Healing)</p>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 px-4 py-6 flex flex-col gap-1.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg text-xs font-semibold tracking-wide uppercase transition-all duration-200 border ${
                  isActive
                    ? "bg-gradient-to-r from-[#0072ff]/10 to-[#00f5d4]/10 border-[#00f5d4]/30 text-[#00f5d4] shadow-inner"
                    : "border-transparent text-[#94a3b8] hover:text-white hover:bg-[#1e293b]/40"
                }`}
              >
                <Icon className={`h-4.5 w-4.5 ${isActive ? "text-[#00f5d4]" : "text-[#64748b]"}`} />
                {item.name}
              </Link>
            );
          })}
        </nav>

        {/* Sidebar Footer status */}
        <div className="p-6 border-t border-[#1e293b] bg-[#0b101f] flex flex-col gap-3">
          <button
            onClick={toggleTheme}
            className="w-full flex items-center justify-between px-3 py-2 bg-[#0d1527] border border-[#2e374a] hover:border-[#00f5d4] hover:text-white rounded-lg text-xs font-semibold text-[#94a3b8] transition-all cursor-pointer"
          >
            <span className="flex items-center gap-2">
              {isLight ? <Sun className="h-4 w-4 text-amber-400" /> : <Moon className="h-4 w-4 text-[#00f5d4]" />}
              {isLight ? "Light Mode" : "Dark Mode"}
            </span>
            <span className="text-[10px] text-[#475569] uppercase font-bold tracking-wider">Toggle</span>
          </button>

          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-[#00f5d4] animate-pulse"></span>
            <span className="text-[10px] text-[#94a3b8] font-medium uppercase tracking-wider">Truth Engine Active</span>
          </div>
          <p className="text-[9px] text-[#475569]">Closed-loop physical-semantic intelligence.</p>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col bg-[#0b0f19] overflow-y-auto">
        {/* Main Content Render */}
        <div className="flex-1">
          {children}
        </div>
      </div>
    </div>
  );
}
