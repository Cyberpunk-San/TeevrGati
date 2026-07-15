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
    <div className="flex-1 flex flex-col p-6 gap-6">
      
      {/* Page Header */}
      <div className="flex justify-between items-center bg-[#0d1527] border border-[#1e293b] p-6 rounded-xl shadow-lg">
        <div>
          <h2 className="text-xl font-bold text-white tracking-wide">MAINTENANCE & PROACTIVE DISPATCH LOGS</h2>
          <p className="text-xs text-[#64748b]">View generated lockout-tagout (LOTO) work orders and dispatcher communications</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={loadData}
            className="h-10 px-4 bg-[#1e293b] border border-[#2e374a] rounded-lg text-xs font-bold text-white hover:bg-slate-800 transition-all flex items-center gap-1.5 cursor-pointer"
          >
            <RefreshCw className="h-4 w-4" />
            Sync Logs
          </button>
          <button
            onClick={handleClear}
            className="h-10 px-4 bg-[#311b1b] border border-rose-900/40 rounded-lg text-xs font-bold text-rose-300 hover:bg-[#412222] transition-all cursor-pointer"
          >
            Clear Active Logs
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Work Order Panel (Left 7 columns) */}
        <div className="lg:col-span-7 bg-[#111827]/80 border border-[#1e293b] rounded-xl p-5 shadow-xl flex flex-col gap-4">
          <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-2 text-[#00f5d4] flex items-center gap-2">
            <Wrench className="h-4 w-4 text-[#00f5d4]" />
            Active Work Order
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

        {/* Alerts Log Panel (Right 5 columns) */}
        <div className="lg:col-span-5 bg-[#111827]/80 border border-[#1e293b] rounded-xl p-5 shadow-xl flex flex-col gap-4">
          <h3 className="text-xs font-bold text-[#00f5d4] uppercase tracking-wider mb-2 flex items-center gap-2">
            <Mail className="h-4 w-4 text-[#00f5d4]" />
            Push Dispatch History
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
