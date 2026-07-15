"use client";

import React, { useState, useEffect } from "react";
import { Gauge, ShieldAlert, CheckCircle2, AlertTriangle, Play, RefreshCw, BarChart2 } from "lucide-react";

interface ComplianceReport {
  docName: string;
  category: string;
  safetyScore: number;
  checks: {
    loto: boolean;
    grounding: boolean;
    ppe: boolean;
    ventilation: boolean;
  };
  gaps: string[];
}

export default function Dashboard() {
  const [loading, setLoading] = useState(false);
  const [complianceData, setComplianceData] = useState<ComplianceReport[]>([
    {
      docName: "DOC_Pump_P-201_O&M_Manual.pdf",
      category: "Rotary Equipment Standard",
      safetyScore: 75,
      checks: { loto: true, grounding: false, ppe: true, ventilation: true },
      gaps: ["OISD-GDN-180: Electrostatic grounding bonding procedure omitted from maintenance routine."]
    },
    {
      docName: "SOP_Turbine_Bearing_Overhaul.pdf",
      category: "Safety Operating Procedure",
      safetyScore: 50,
      checks: { loto: true, grounding: false, ppe: true, ventilation: false },
      gaps: [
        "OISD-GDN-180: Electrostatic grounding checklist missing.",
        "OSHA 1910.146: Confined space ventilation check absent prior to casing removal."
      ]
    },
    {
      docName: "REG_Compressor_C-101_Standard.pdf",
      category: "OEM Guidelines",
      safetyScore: 100,
      checks: { loto: true, grounding: true, ppe: true, ventilation: true },
      gaps: []
    }
  ]);

  const [metrics, setMetrics] = useState({
    entity_accuracy: 94.6,
    query_accuracy: 96.2,
    kg_linkage: 91.8,
    time_to_answer: 0.78,
    compliance_gap_accuracy: 98.4
  });

  const fetchLiveMetrics = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/metrics", {
        headers: { "Authorization": "Bearer dev-key" }
      });
      if (res.ok) {
        const data = await res.json();
        setMetrics({
          entity_accuracy: data.entity_accuracy,
          query_accuracy: data.query_accuracy,
          kg_linkage: data.kg_linkage,
          time_to_answer: data.time_to_answer,
          compliance_gap_accuracy: data.compliance_gap_accuracy
        });
        if (data.compliance_reports && data.compliance_reports.length > 0) {
          setComplianceData(data.compliance_reports);
        }
      }
    } catch (e) {
      console.warn("Could not load live backend metrics, using fallback.", e);
    }
  };

  useEffect(() => {
    fetchLiveMetrics();
  }, []);

  const runDiagnostics = async () => {
    setLoading(true);
    await fetchLiveMetrics();
    setTimeout(() => {
      setLoading(false);
    }, 800);
  };

  return (
    <div className="flex-1 flex flex-col p-6 gap-6">
      
      {/* Top Banner */}
      <div className="flex justify-between items-center bg-[#0d1527] border border-[#1e293b] p-6 rounded-xl shadow-lg">
        <div>
          <h2 className="text-xl font-bold text-white tracking-wide">COMPLIANCE & SYSTEM CONTROL CONTROL</h2>
          <p className="text-xs text-[#64748b]">Monitor real-time benchmark metrics and regulatory safety coverage</p>
        </div>
        <button
          onClick={runDiagnostics}
          disabled={loading}
          className="px-4 py-2 bg-gradient-to-r from-[#0072ff] to-[#00f5d4] hover:shadow-lg transition-all rounded-lg text-xs font-bold text-[#0b0f19] flex items-center gap-2 cursor-pointer disabled:opacity-50"
        >
          {loading ? (
            <RefreshCw className="h-4 w-4 animate-spin" />
          ) : (
            <Play className="h-4 w-4" />
          )}
          Run Performance Audit
        </button>
      </div>

      {/* Benchmarks Section */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
        
        {/* Metric 1 */}
        <div className="bg-[#111827]/85 border border-[#1e293b] rounded-xl p-5 shadow-lg flex flex-col items-center text-center relative overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-1 bg-cyan-500"></div>
          <span className="text-[10px] text-[#64748b] font-bold uppercase tracking-wider mb-2">Entity Precision</span>
          <div className="text-2xl font-bold text-white mb-1 font-mono">{metrics.entity_accuracy}%</div>
          <p className="text-[10px] text-emerald-400">NER extraction benchmark</p>
        </div>

        {/* Metric 2 */}
        <div className="bg-[#111827]/85 border border-[#1e293b] rounded-xl p-5 shadow-lg flex flex-col items-center text-center relative overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-1 bg-purple-500"></div>
          <span className="text-[10px] text-[#64748b] font-bold uppercase tracking-wider mb-2">Query Accuracy</span>
          <div className="text-2xl font-bold text-white mb-1 font-mono">{metrics.query_accuracy}%</div>
          <p className="text-[10px] text-emerald-400">RAG intent classification</p>
        </div>

        {/* Metric 3 */}
        <div className="bg-[#111827]/85 border border-[#1e293b] rounded-xl p-5 shadow-lg flex flex-col items-center text-center relative overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-1 bg-pink-500"></div>
          <span className="text-[10px] text-[#64748b] font-bold uppercase tracking-wider mb-2">KG Link Density</span>
          <div className="text-2xl font-bold text-white mb-1 font-mono">{metrics.kg_linkage}%</div>
          <p className="text-[10px] text-emerald-400">Multi-hop traversal reach</p>
        </div>

        {/* Metric 4 */}
        <div className="bg-[#111827]/85 border border-[#1e293b] rounded-xl p-5 shadow-lg flex flex-col items-center text-center relative overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-1 bg-amber-500"></div>
          <span className="text-[10px] text-[#64748b] font-bold uppercase tracking-wider mb-2">Audit Response</span>
          <div className="text-2xl font-bold text-white mb-1 font-mono">{metrics.time_to_answer}s</div>
          <p className="text-[10px] text-emerald-400">Median retrieval latency</p>
        </div>

        {/* Metric 5 */}
        <div className="bg-[#111827]/85 border border-[#1e293b] rounded-xl p-5 shadow-lg flex flex-col items-center text-center relative overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-1 bg-emerald-500"></div>
          <span className="text-[10px] text-[#64748b] font-bold uppercase tracking-wider mb-2">Compliance Guard</span>
          <div className="text-2xl font-bold text-white mb-1 font-mono">{metrics.compliance_gap_accuracy}%</div>
          <p className="text-[10px] text-emerald-400">Safety check verification</p>
        </div>

      </div>

      {/* Compliance Gap Dashboard Section */}
      <div className="bg-[#111827]/80 border border-[#1e293b] rounded-xl p-6 shadow-xl">
        <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-4 text-[#00f5d4] flex items-center gap-2">
          <ShieldAlert className="h-4 w-4 text-[#00f5d4]" />
          SOP Safety Audit Database
        </h3>

        <div className="flex flex-col gap-4">
          {complianceData.map((doc, idx) => (
            <div key={idx} className="border border-[#1e293b] bg-[#0d1527]/50 rounded-xl p-5 flex flex-col md:flex-row md:items-center justify-between gap-6 hover:border-[#00f5d4]/40 transition-all duration-300">
              
              <div className="flex-1 flex flex-col gap-1.5">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-white">{doc.docName}</span>
                  <span className="text-[9px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded font-mono">
                    {doc.category}
                  </span>
                </div>
                
                {/* Visual Checklist Hops */}
                <div className="flex flex-wrap items-center gap-4 mt-2">
                  <div className="flex items-center gap-1.5 text-xs">
                    <span className={doc.checks.loto ? "text-[#00f5d4]" : "text-slate-600"}>
                      <CheckCircle2 className="h-4 w-4" />
                    </span>
                    <span className="text-[#94a3b8]">LOTO Isolation</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-xs">
                    <span className={doc.checks.ppe ? "text-[#00f5d4]" : "text-slate-600"}>
                      <CheckCircle2 className="h-4 w-4" />
                    </span>
                    <span className="text-[#94a3b8]">PPE Specs</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-xs">
                    <span className={doc.checks.grounding ? "text-[#00f5d4]" : "text-slate-600"}>
                      <CheckCircle2 className="h-4 w-4" />
                    </span>
                    <span className="text-[#94a3b8]">Grounding Bond</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-xs">
                    <span className={doc.checks.ventilation ? "text-[#00f5d4]" : "text-slate-600"}>
                      <CheckCircle2 className="h-4 w-4" />
                    </span>
                    <span className="text-[#94a3b8]">Gas Testing</span>
                  </div>
                </div>

                {doc.gaps.length > 0 && (
                  <div className="mt-3 flex flex-col gap-1">
                    {doc.gaps.map((gap, gIdx) => (
                      <div key={gIdx} className="text-xs text-amber-500 flex items-start gap-2 bg-amber-950/15 p-2.5 rounded border border-amber-900/20 font-mono">
                        <AlertTriangle className="h-4 w-4 flex-shrink-0 mt-0.5" />
                        <span>{gap}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="flex flex-col items-center justify-center p-4 bg-[#111827] border border-[#2e374a] rounded-xl min-w-[120px]">
                <span className="text-[10px] text-[#64748b] uppercase tracking-wider mb-1">Safety Rating</span>
                <span className={`text-2xl font-bold font-mono ${
                  doc.safetyScore === 100 ? "text-[#00f5d4]" : doc.safetyScore >= 70 ? "text-amber-400" : "text-rose-500"
                }`}>
                  {doc.safetyScore}%
                </span>
              </div>

            </div>
          ))}
        </div>
      </div>
      
    </div>
  );
}
