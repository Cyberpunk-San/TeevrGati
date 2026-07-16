"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity, GitBranch, FileText, Wrench, Upload, LayoutDashboard
} from "lucide-react";

const NAV_ITEMS = [
  { href: "/",            label: "Diagnostics",  icon: Activity },
  { href: "/dashboard",   label: "Dashboard",    icon: LayoutDashboard },
  { href: "/graph",       label: "KG Graph",     icon: GitBranch },
  { href: "/maintenance", label: "Maintenance",  icon: Wrench },
  { href: "/ingest",      label: "Ingest SOP",   icon: Upload },
];

export default function NavigationWrapper({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [time, setTime] = useState(() => new Date().toLocaleTimeString("en-IN", { hour12: false }));

  React.useEffect(() => {
    const t = setInterval(() => setTime(new Date().toLocaleTimeString("en-IN", { hour12: false })), 1000);
    return () => clearInterval(t);
  }, []);

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "var(--bg-base)" }}>

      {/* ── Sidebar ── */}
      <aside style={{
        width: 220,
        flexShrink: 0,
        background: "var(--bg-surface)",
        borderRight: "1px solid var(--border)",
        display: "flex",
        flexDirection: "column",
        padding: "20px 0",
        position: "sticky",
        top: 0,
        height: "100vh",
        overflowY: "auto",
      }}>

        {/* Logo */}
        <div style={{ padding: "0 16px 20px", borderBottom: "1px solid var(--border-dim)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{
              width: 32, height: 32,
              background: "var(--accent)",
              borderRadius: "var(--r-sm)",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontWeight: 800, fontSize: 13, color: "#09090b",
              fontFamily: "monospace", letterSpacing: "-0.02em",
            }}>
              TG
            </div>
            <div>
              <div style={{ fontSize: 13, fontWeight: 600, color: "var(--text-primary)", letterSpacing: "-0.01em" }}>
                TeevrGati
              </div>
              <div style={{ fontSize: 10, color: "var(--text-muted)", letterSpacing: "0.02em" }}>
                Refinery AI
              </div>
            </div>
          </div>
        </div>

        {/* Plant badge */}
        <div style={{ padding: "12px 16px", borderBottom: "1px solid var(--border-dim)" }}>
          <div style={{ fontSize: 10, fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", marginBottom: 4 }}>
            Active Plant
          </div>
          <div style={{ fontSize: 11, fontWeight: 500, color: "var(--text-secondary)" }}>
            BPCL Mathura Refinery
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 5, marginTop: 6 }}>
            <div style={{ width: 5, height: 5, borderRadius: "50%", background: "#10b981", boxShadow: "0 0 5px #10b98166" }} />
            <span style={{ fontSize: 10, color: "#10b981" }}>Online · {time}</span>
          </div>
        </div>

        {/* Nav items */}
        <nav style={{ padding: "10px 8px", flex: 1 }}>
          <div style={{ fontSize: 10, fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", padding: "4px 8px 8px" }}>
            Navigation
          </div>
          {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
            const active = pathname === href || (href !== "/" && pathname.startsWith(href));
            return (
              <Link key={href} href={href} style={{ textDecoration: "none" }}>
                <div style={{
                  display: "flex", alignItems: "center", gap: 10,
                  padding: "8px 10px", borderRadius: "var(--r-sm)", marginBottom: 2,
                  background: active ? "var(--accent-dim)" : "transparent",
                  border: active ? "1px solid rgba(34,211,238,0.2)" : "1px solid transparent",
                  cursor: "pointer",
                  transition: "background 0.15s, border-color 0.15s",
                }}>
                  <Icon size={14} color={active ? "var(--accent)" : "var(--text-muted)"} />
                  <span style={{
                    fontSize: 13, fontWeight: active ? 500 : 400,
                    color: active ? "var(--text-primary)" : "var(--text-secondary)",
                  }}>
                    {label}
                  </span>
                </div>
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div style={{ padding: "12px 16px", borderTop: "1px solid var(--border-dim)" }}>
          <div style={{ fontSize: 10, color: "var(--text-muted)" }}>
            तीव्र गति &middot; High Velocity
          </div>
          <div style={{ fontSize: 10, color: "var(--text-muted)", marginTop: 2 }}>
            OISD-105 · ISO 10816-3 · API 610
          </div>
        </div>
      </aside>

      {/* ── Main content ── */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
        {/* Top bar */}
        <header style={{
          height: 48,
          borderBottom: "1px solid var(--border)",
          display: "flex",
          alignItems: "center",
          padding: "0 24px",
          gap: 12,
          background: "var(--bg-surface)",
          position: "sticky",
          top: 0,
          zIndex: 10,
        }}>
          <div style={{ fontSize: 12, color: "var(--text-muted)", flex: 1 }}>
            {NAV_ITEMS.find(n => n.href === pathname || (n.href !== "/" && pathname.startsWith(n.href)))?.label || "Diagnostics"}
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
            <div style={{ fontSize: 11, color: "var(--text-muted)" }}>
              Pump P-201 · C-101 · T-301
            </div>
            <div style={{
              padding: "3px 10px", borderRadius: "100px",
              background: "rgba(34,211,238,0.08)", border: "1px solid rgba(34,211,238,0.2)",
              fontSize: 11, color: "var(--accent)", fontWeight: 500,
            }}>
              gemini-2.0-flash
            </div>
          </div>
        </header>

        {/* Page content */}
        <main style={{ flex: 1, overflowY: "auto" }}>
          {children}
        </main>
      </div>
    </div>
  );
}
