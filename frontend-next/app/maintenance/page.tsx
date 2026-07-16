"use client";

import React, { useState, useEffect } from "react";
import { Wrench, ShieldAlert, ShieldCheck, Mail, RefreshCw } from "lucide-react";

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
  title: string;
}

export default function MaintenancePage() {
  const [workOrder, setWorkOrder] = useState<WorkOrder | null>(null);
  const [alerts, setAlerts] = useState<PushAlert[]>([]);

  const loadData = () => {
    const savedResult = localStorage.getItem("query_result");
    if (savedResult) {
      try {
        const parsed = JSON.parse(savedResult);
        if (parsed.work_order) {
          setWorkOrder(parsed.work_order);
        } else {
          setWorkOrder(null);
        }
        if (parsed.proactive_alerts) {
          setAlerts(parsed.proactive_alerts);
        } else {
          setAlerts([]);
        }
      } catch (e) {
        console.error(e);
      }
    } else {
      setWorkOrder(null);
      setAlerts([]);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleClear = () => {
    localStorage.removeItem("query_result");
    localStorage.removeItem("conflict_resolution");
    localStorage.removeItem("resolution_details");
    setWorkOrder(null);
    setAlerts([]);
  };

  return (
    <div className="page-shell">
      <div className="page-header">
        <div>
          <div className="label">Field operations</div>
          <h1 className="page-title" style={{ marginTop: 8 }}>Maintenance & dispatch</h1>
          <p className="page-subtitle">
            LOTO work orders and proactive alerts generated from diagnostic runs.
          </p>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          <button onClick={loadData} className="btn btn-ghost">
            <RefreshCw size={14} /> Sync
          </button>
          <button onClick={handleClear} className="btn btn-danger">
            Clear logs
          </button>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: 28, alignItems: "start" }}>
        
        <div className="card card-pad" style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          <h3 className="label" style={{ color: "var(--accent)", display: "flex", alignItems: "center", gap: 8 }}>
            <Wrench size={14} color="var(--accent)" />
            Active work order
          </h3>

          {workOrder ? (
            <div className="flex flex-col gap-4">
              <div className="flex justify-between items-center bg-[#0d1527] p-3 rounded-lg border border-[#1e293b]">
                <div>
                  <span className="text-[#64748b] text-[9px] block uppercase">Work Order ID</span>
                  <span className="text-[#00f5d4] font-mono text-sm font-bold">{workOrder.id}</span>
                </div>
                <div>
                  <span className="text-[#64748b] text-[9px] block uppercase">Vibration Urgency</span>
                  <span className="text-rose-400 text-xs font-bold">{workOrder.priority}</span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 text-xs">
                <div>
                  <span className="text-[#64748b] text-[10px] block">ESTIMATED LABOR TIME</span>
                  <span className="text-white font-bold">{workOrder.labor_estimate_hours} Hours</span>
                </div>
                <div>
                  <span className="text-[#64748b] text-[10px] block">CRITICAL PARTS REQUIRED</span>
                  <span className="text-white font-bold">{workOrder.spare_parts_required.join(", ") || "No parts logged"}</span>
                </div>
              </div>

              {workOrder.description && (
                <div className="text-xs bg-[#0d1527]/50 p-3 border border-[#1e293b] rounded">
                  <span className="text-[#64748b] text-[10px] block mb-1">DESCRIPTION</span>
                  <p className="text-slate-300">{workOrder.description}</p>
                </div>
              )}

              <div className="border-t border-[#1e293b] pt-3">
                <span className="text-[#64748b] text-[10px] block mb-2 font-bold uppercase">Maintenance Instructions</span>
                <ul className="list-decimal pl-4 text-xs text-slate-300 flex flex-col gap-1.5">
                  {workOrder.instructions.map((step, idx) => (
                    <li key={idx} className="pl-1">{step}</li>
                  ))}
                </ul>
              </div>

              <div className="border-t border-[#1e293b] pt-3">
                <span className="text-[#64748b] text-[10px] block mb-2 font-bold uppercase">Lockout-Tagout (LOTO) Guidelines</span>
                <div className="flex flex-col gap-2">
                  {workOrder.safety_requirements.map((req, idx) => (
                    <span key={idx} className="text-xs text-amber-500 flex items-center gap-2 bg-amber-950/10 p-2 rounded border border-amber-900/30">
                      <ShieldAlert className="h-4 w-4 text-amber-500 flex-shrink-0" />
                      {req}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center text-center h-[320px] border border-dashed border-[#2e374a] rounded-lg p-6">
              <span className="text-xs text-[#64748b]">No active work order generated. Run diagnostic overrides on the Co-Pilot page first.</span>
            </div>
          )}
        </div>

        <div className="card card-pad" style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          <h3 className="label" style={{ color: "var(--accent)", display: "flex", alignItems: "center", gap: 8 }}>
            <Mail size={14} color="var(--accent)" />
            Push dispatch
          </h3>

          {alerts.length > 0 ? (
            <div className="flex flex-col gap-2 overflow-y-auto max-h-[500px]">
              {alerts.map((alert, i) => (
                <div 
                  key={i} 
                  className={`p-3 rounded-lg border text-xs flex flex-col gap-1.5 ${
                    alert.type === 'critical_alert' 
                      ? 'bg-rose-950/20 border-rose-900/40 text-rose-300' 
                      : alert.type === 'safety_alert'
                      ? 'bg-amber-950/20 border-amber-900/40 text-amber-300'
                      : 'bg-cyan-950/20 border-cyan-900/40 text-cyan-300'
                  }`}
                >
                  <div className="flex justify-between items-center font-bold">
                    <span>🔔 {alert.recipient}</span>
                    <span className="text-[9px] uppercase opacity-75">{alert.type.replace("_", " ")}</span>
                  </div>
                  <p className="text-[11px] font-medium opacity-90 leading-tight">
                    {alert.message}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center text-center h-[320px] border border-dashed border-[#2e374a] rounded-lg p-6">
              <span className="text-xs text-[#64748b]">No notifications dispatched.</span>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
