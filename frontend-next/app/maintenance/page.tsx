"use client";

import React, { useState, useEffect } from "react";
import { Wrench, ShieldAlert, Mail, RefreshCw, Bell, CheckCircle } from "lucide-react";
import { apiPost, ApiError } from "../lib/apiClient";

import { DEFAULT_ASSET_ID } from "../config";

interface WorkOrder {
  id: string;
  priority: string;
  labor_estimate_hours: number;
  spare_parts_required: string[];
  instructions: string[];
  safety_requirements: string[];
  description?: string;
}

interface PushAlert {
  type: string;
  recipient: string;
  message: string;
  title?: string;
}

export default function MaintenancePage() {
  const [workOrder, setWorkOrder] = useState<WorkOrder | null>(null);
  const [alerts, setAlerts] = useState<PushAlert[]>([]);
  const [briefingLoading, setBriefingLoading] = useState(false);
  const [briefingError, setBriefingError] = useState<string | null>(null);

  /* ── Load work-order from previous diagnostic session ── */
  const loadLocalData = () => {
    const savedResult = localStorage.getItem("query_result");
    if (savedResult) {
      try {
        const parsed = JSON.parse(savedResult);
        setWorkOrder(parsed.work_order ?? null);
        setAlerts(parsed.proactive_alerts ?? []);
      } catch {
        setWorkOrder(null);
        setAlerts([]);
      }
    } else {
      setWorkOrder(null);
      setAlerts([]);
    }
  };

  /* ── Fetch proactive shift briefing from backend ── */
  const fetchShiftBriefing = async () => {
    setBriefingLoading(true);
    setBriefingError(null);
    try {
      const data = await apiPost<{ success: boolean; alert: PushAlert; summary: Record<string, unknown> }>(
        "/api/shift-briefing",
        { asset_id: DEFAULT_ASSET_ID, shift: "Day" }
      );
      if (data.alert) {
        setAlerts((prev) => {
          // Avoid duplicate briefing entries
          const withoutBriefing = prev.filter((a) => a.type !== "shift_briefing");
          return [{ ...data.alert, type: "shift_briefing" }, ...withoutBriefing];
        });
      }
    } catch (err) {
      const msg = err instanceof ApiError ? err.detail : "Could not load shift briefing.";
      setBriefingError(msg);
    } finally {
      setBriefingLoading(false);
    }
  };

  useEffect(() => {
    loadLocalData();
    fetchShiftBriefing();
  }, []);

  const handleClear = () => {
    localStorage.removeItem("query_result");
    localStorage.removeItem("conflict_resolution");
    localStorage.removeItem("resolution_details");
    setWorkOrder(null);
    setAlerts([]);
  };

  const alertBorderColor = (type: string) => {
    if (type === "critical_alert") return "rgba(244,63,94,0.3)";
    if (type === "safety_alert") return "rgba(245,158,11,0.3)";
    if (type === "shift_briefing") return "rgba(34,211,238,0.3)";
    return "var(--border)";
  };
  const alertBg = (type: string) => {
    if (type === "critical_alert") return "rgba(244,63,94,0.06)";
    if (type === "safety_alert") return "rgba(245,158,11,0.06)";
    if (type === "shift_briefing") return "var(--accent-dim)";
    return "var(--bg-base)";
  };
  const alertTextColor = (type: string) => {
    if (type === "critical_alert") return "var(--danger)";
    if (type === "safety_alert") return "var(--warning)";
    if (type === "shift_briefing") return "var(--accent)";
    return "var(--text-secondary)";
  };

  return (
    <div className="page-shell">
      <div className="page-header">
        <div>
          <div className="label">Field operations</div>
          <h1 className="page-title" style={{ marginTop: 8 }}>Maintenance &amp; dispatch</h1>
          <p className="page-subtitle">
            LOTO work orders and proactive alerts generated from diagnostic runs.
          </p>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          <button
            className="btn btn-ghost"
            onClick={() => { loadLocalData(); fetchShiftBriefing(); }}
            disabled={briefingLoading}
          >
            <RefreshCw size={14} style={briefingLoading ? { animation: "spin 1s linear infinite" } : undefined} />
            Sync
          </button>
          <button className="btn btn-danger" onClick={handleClear}>
            Clear logs
          </button>
        </div>
      </div>

      {briefingError && (
        <div style={{
          padding: "12px 16px", borderRadius: "var(--r-sm)",
          background: "rgba(244,63,94,0.06)", border: "1px solid rgba(244,63,94,0.25)",
          color: "var(--danger)", fontSize: 13, display: "flex", gap: 10, alignItems: "center",
        }}>
          {briefingError}
          <button onClick={() => setBriefingError(null)} style={{ marginLeft: "auto", background: "none", border: "none", cursor: "pointer", color: "inherit" }}>✕</button>
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: 28, alignItems: "start" }}>

        {/* ── Work order ── */}
        <div className="card card-pad" style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          <div className="label" style={{ color: "var(--accent)", display: "flex", alignItems: "center", gap: 8 }}>
            <Wrench size={14} color="var(--accent)" />
            Active work order
          </div>

          {workOrder ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>

              {/* Header row */}
              <div style={{
                display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12,
              }}>
                <div style={{
                  padding: "14px 16px", borderRadius: "var(--r-sm)",
                  background: "var(--bg-base)", border: "1px solid var(--border-dim)",
                }}>
                  <div className="label" style={{ marginBottom: 6 }}>Work order ID</div>
                  <div style={{ fontFamily: "var(--font-mono)", fontSize: 13, color: "var(--accent)", fontWeight: 600 }}>
                    {workOrder.id}
                  </div>
                </div>
                <div style={{
                  padding: "14px 16px", borderRadius: "var(--r-sm)",
                  background: "var(--bg-base)", border: "1px solid var(--border-dim)",
                }}>
                  <div className="label" style={{ marginBottom: 6 }}>Vibration urgency</div>
                  <div style={{ fontSize: 13, color: "var(--danger)", fontWeight: 600 }}>{workOrder.priority}</div>
                </div>
              </div>

              {/* Stats row */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                <div>
                  <div className="label" style={{ marginBottom: 6 }}>Estimated labor</div>
                  <div style={{ fontSize: 14, fontWeight: 560 }}>{workOrder.labor_estimate_hours} hours</div>
                </div>
                <div>
                  <div className="label" style={{ marginBottom: 6 }}>Critical parts</div>
                  <div style={{ fontSize: 13, color: "var(--text-secondary)" }}>
                    {workOrder.spare_parts_required.join(", ") || "No parts logged"}
                  </div>
                </div>
              </div>

              {/* Description */}
              {workOrder.description && (
                <div style={{
                  padding: "14px 16px", borderRadius: "var(--r-sm)",
                  background: "var(--bg-base)", border: "1px solid var(--border-dim)",
                }}>
                  <div className="label" style={{ marginBottom: 6 }}>Description</div>
                  <p style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.6 }}>{workOrder.description}</p>
                </div>
              )}

              {/* Instructions */}
              <div style={{ borderTop: "1px solid var(--border-dim)", paddingTop: 16 }}>
                <div className="label" style={{ marginBottom: 10 }}>Maintenance instructions</div>
                <ol style={{ paddingLeft: 20, display: "flex", flexDirection: "column", gap: 8 }}>
                  {workOrder.instructions.map((step, idx) => (
                    <li key={idx} style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.55 }}>{step}</li>
                  ))}
                </ol>
              </div>

              {/* LOTO / Safety */}
              <div style={{ borderTop: "1px solid var(--border-dim)", paddingTop: 16 }}>
                <div className="label" style={{ marginBottom: 10 }}>Lockout-tagout (LOTO) guidelines</div>
                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                  {workOrder.safety_requirements.map((req, idx) => (
                    <div key={idx} style={{
                      display: "flex", alignItems: "flex-start", gap: 10,
                      padding: "12px 14px", borderRadius: "var(--r-sm)",
                      background: "rgba(245,158,11,0.06)", border: "1px solid rgba(245,158,11,0.2)",
                    }}>
                      <ShieldAlert size={14} color="var(--warning)" style={{ marginTop: 1, flexShrink: 0 }} />
                      <span style={{ fontSize: 13, color: "var(--warning)", lineHeight: 1.5 }}>{req}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div style={{
              border: "1px dashed var(--border)", borderRadius: "var(--r-md)",
              padding: 48, textAlign: "center", color: "var(--text-muted)", fontSize: 13, lineHeight: 1.6,
              minHeight: 280, display: "flex", alignItems: "center", justifyContent: "center",
            }}>
              No active work order. Run a diagnostic on the Co-Pilot page first.
            </div>
          )}
        </div>

        {/* ── Push dispatch / alerts ── */}
        <div className="card card-pad" style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          <div className="label" style={{ color: "var(--accent)", display: "flex", alignItems: "center", gap: 8 }}>
            <Mail size={14} color="var(--accent)" />
            Push dispatch
            {briefingLoading && (
              <RefreshCw size={11} style={{ marginLeft: 4, animation: "spin 1s linear infinite", color: "var(--text-muted)" }} />
            )}
          </div>

          {alerts.length > 0 ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 10, maxHeight: 480, overflowY: "auto" }}>
              {alerts.map((alert, i) => (
                <div key={i} style={{
                  padding: "14px 16px", borderRadius: "var(--r-sm)",
                  background: alertBg(alert.type),
                  border: `1px solid ${alertBorderColor(alert.type)}`,
                  display: "flex", flexDirection: "column", gap: 8,
                }}>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 8 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <Bell size={12} color={alertTextColor(alert.type)} />
                      <span style={{ fontSize: 12, fontWeight: 600, color: alertTextColor(alert.type) }}>
                        {alert.recipient || alert.title || "Alert"}
                      </span>
                    </div>
                    <span className="badge badge-default" style={{ fontSize: 10 }}>
                      {alert.type.replace(/_/g, " ")}
                    </span>
                  </div>
                  <p style={{ fontSize: 12, color: "var(--text-secondary)", lineHeight: 1.55 }}>
                    {alert.message}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <div style={{
              border: "1px dashed var(--border)", borderRadius: "var(--r-md)",
              padding: 48, textAlign: "center",
              color: "var(--text-muted)", fontSize: 13, lineHeight: 1.6,
              minHeight: 280, display: "flex", flexDirection: "column",
              alignItems: "center", justifyContent: "center", gap: 10,
            }}>
              <CheckCircle size={22} color="var(--border)" />
              No notifications dispatched.
            </div>
          )}
        </div>

      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
