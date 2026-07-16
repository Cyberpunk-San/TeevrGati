"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity, GitBranch, Wrench, Upload, LayoutDashboard
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

  const current = NAV_ITEMS.find(
    (n) => n.href === pathname || (n.href !== "/" && pathname.startsWith(n.href))
  );

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "var(--bg-base)" }}>
      <aside style={{
        width: 240,
        flexShrink: 0,
        background: "var(--bg-surface)",
        borderRight: "1px solid var(--border)",
        display: "flex",
        flexDirection: "column",
        position: "sticky",
        top: 0,
        height: "100vh",
      }}>
        {/* Brand */}
        <div style={{ padding: "28px 22px 24px", borderBottom: "1px solid var(--border-dim)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <div style={{
              width: 36, height: 36,
              background: "var(--accent)",
              borderRadius: 10,
              display: "flex", alignItems: "center", justifyContent: "center",
              fontWeight: 700, fontSize: 13, color: "#09090b",
              letterSpacing: "-0.04em",
            }}>
              TG
            </div>
            <div>
              <div style={{ fontSize: 15, fontWeight: 600, letterSpacing: "-0.02em" }}>
                TeevrGati
              </div>
              <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>
                Refinery AI
              </div>
            </div>
          </div>
        </div>

        {/* Plant */}
        <div style={{ padding: "20px 22px", borderBottom: "1px solid var(--border-dim)" }}>
          <div className="label" style={{ marginBottom: 8 }}>Active plant</div>
          <div style={{ fontSize: 13, fontWeight: 500, color: "var(--text-primary)", lineHeight: 1.4 }}>
            BPCL Mathura Refinery
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 10 }}>
            <div style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--success)", boxShadow: "0 0 6px #10b98166" }} />
            <span style={{ fontSize: 12, color: "var(--success)" }}>Online · {time}</span>
          </div>
        </div>

        {/* Nav */}
        <nav style={{ padding: "20px 12px", flex: 1, overflowY: "auto" }}>
          <div className="label" style={{ padding: "0 10px 12px" }}>Navigation</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
              const active = pathname === href || (href !== "/" && pathname.startsWith(href));
              return (
                <Link key={href} href={href} style={{ textDecoration: "none" }}>
                  <div style={{
                    display: "flex", alignItems: "center", gap: 12,
                    padding: "11px 12px",
                    borderRadius: "var(--r-sm)",
                    background: active ? "var(--accent-dim)" : "transparent",
                    border: active ? "1px solid rgba(34,211,238,0.2)" : "1px solid transparent",
                    transition: "background 0.15s, border-color 0.15s",
                  }}>
                    <Icon size={16} color={active ? "var(--accent)" : "var(--text-muted)"} />
                    <span style={{
                      fontSize: 13.5,
                      fontWeight: active ? 550 : 400,
                      color: active ? "var(--text-primary)" : "var(--text-secondary)",
                    }}>
                      {label}
                    </span>
                  </div>
                </Link>
              );
            })}
          </div>
        </nav>

        <div style={{ padding: "20px 22px", borderTop: "1px solid var(--border-dim)" }}>
          <div style={{ fontSize: 12, color: "var(--text-muted)", lineHeight: 1.5 }}>
            तीव्र गति · High Velocity
          </div>
          <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 6, opacity: 0.8 }}>
            OISD-105 · ISO 10816 · API 610
          </div>
        </div>
      </aside>

      <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
        <header style={{
          height: 56,
          borderBottom: "1px solid var(--border)",
          display: "flex",
          alignItems: "center",
          padding: "0 40px",
          gap: 16,
          background: "var(--bg-surface)",
          position: "sticky",
          top: 0,
          zIndex: 10,
        }}>
          <div style={{ fontSize: 13, color: "var(--text-secondary)", flex: 1, fontWeight: 500 }}>
            {current?.label || "Diagnostics"}
          </div>
          <div style={{ fontSize: 12, color: "var(--text-muted)" }}>
            P-201 · C-101 · T-301
          </div>
          <div className="badge badge-accent">gemini-2.0-flash</div>
        </header>

        <main style={{ flex: 1, overflowY: "auto" }}>
          {children}
        </main>
      </div>
    </div>
  );
}
