"use client";

import React, { useState, useEffect, useRef } from "react";
import { gsap } from "gsap";
import { 
  Activity, 
  AlertTriangle, 
  Send, 
  Layers, 
  Cpu, 
  ShieldAlert, 
  CheckCircle, 
  RefreshCw 
} from "lucide-react";
import { VoiceInput } from "./components/VoiceInput";
import { PathVisualization } from "./components/PathVisualization";

interface AgentLog {
  timestamp: string;
  level: string;
  message: string;
}

interface QueryResult {
  asset_id?: string;
  conflict_detected: boolean;
  conflict_details?: {
    description: string;
    document_hypothesis: string;
    document_confidence: number;
    physics_result: string;
    physics_confidence: number;
    sources: {
      documents: string;
      physics: string;
    };
    auto_resolution?: {
      winner: string;
      reason: string;
      confidence: number;
    };
  };
  auto_resolution_recommendation?: {
    winner: string;
    reason: string;
    confidence: number;
  };
  human_question?: string;
  final_answer?: string;
  physics_result?: {
    fault_type: string;
    severity: string;
    recommendation: string;
  };
  work_order?: any;
  proactive_alerts?: any[];
  agent_log?: AgentLog[];
  paths?: any[];
  compliance_gaps?: any[];
  debate?: {
    historian: string;
    physicist: string;
    operator: string;
    consensus: string;
  };
}

interface ResolutionDetails {
  healed_nodes: string[];
  winner_id: string;
  structured_rule?: {
    type: string;
    confidence: number;
    rule_text: string;
  };
  agent_log?: AgentLog[];
}

export default function Home() {
  const [query, setQuery] = useState("Pump P-201 is vibrating loudly. What could be wrong?");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QueryResult | null>(null);
  
  // Resolution states
  const [resolving, setResolving] = useState(false);
  const [conflictResolution, setConflictResolution] = useState<string | null>(null);
  const [resolutionDetails, setResolutionDetails] = useState<ResolutionDetails | null>(null);
  const [showInterview, setShowInterview] = useState(false);
  const [humanResponse, setHumanResponse] = useState("");
  
  // Animation refs
  const consoleRef = useRef<HTMLDivElement>(null);
  
  // Load saved query results on mount
  useEffect(() => {
    const saved = localStorage.getItem("query_result");
    if (saved) {
      try {
        setResult(JSON.parse(saved));
      } catch (e) {
        console.error(e);
      }
    }
    const savedRes = localStorage.getItem("conflict_resolution");
    if (savedRes) setConflictResolution(savedRes);
    const savedDet = localStorage.getItem("resolution_details");
    if (savedDet) {
      try {
        setResolutionDetails(JSON.parse(savedDet));
      } catch (e) {
        console.error(e);
      }
    }
  }, []);

  const handleQuery = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setLoading(true);
    setResult(null);
    setConflictResolution(null);
    setResolutionDetails(null);
    setShowInterview(false);
    setHumanResponse("");
    
    // Clear storage keys on new query
    localStorage.removeItem("query_result");
    localStorage.removeItem("conflict_resolution");
    localStorage.removeItem("resolution_details");
    
    try {
      const res = await fetch("http://localhost:8000/api/query", {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Authorization": "Bearer dev-key"
        },
        body: JSON.stringify({ query })
      });
      if (res.ok) {
        const data = await res.json();
        setResult(data);
        localStorage.setItem("query_result", JSON.stringify(data));
        
        setTimeout(() => {
          if (consoleRef.current) {
            gsap.fromTo(
              consoleRef.current.children,
              { opacity: 0, x: -10 },
              { opacity: 1, x: 0, duration: 0.3, stagger: 0.05, ease: "power2.out" }
            );
          }
        }, 100);
      }
    } catch (err) {
      console.error("Query request failed:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleResolve = async (choice: string) => {
    if (!result) return;
    setResolving(true);
    try {
      const res = await fetch("http://localhost:8000/api/resolve", {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Authorization": "Bearer dev-key"
        },
        body: JSON.stringify({
          query_result: result,
          choice,
          human_feedback: choice === "human" ? humanResponse : null
        })
      });
      if (res.ok) {
        const data = await res.json();
        setResolutionDetails(data);
        setConflictResolution(choice);
        setShowInterview(false);
        
        localStorage.setItem("conflict_resolution", choice);
        localStorage.setItem("resolution_details", JSON.stringify(data));
        
        // Update query result log references in storage
        const updatedResult = { ...result };
        if (updatedResult.agent_log && data.agent_log) {
          updatedResult.agent_log = [...updatedResult.agent_log, ...data.agent_log];
        }
        setResult(updatedResult);
        localStorage.setItem("query_result", JSON.stringify(updatedResult));
      }
    } catch (err) {
      console.error("Conflict resolution failed:", err);
    } finally {
      setResolving(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col p-6 gap-6">
      
      {/* Top Welcome Title */}
      <div className="flex justify-between items-center bg-[#0d1527] border border-[#1e293b] p-6 rounded-xl shadow-lg">
        <div>
          <h2 className="text-xl font-bold text-white tracking-wide">DIAGNOSTICS CO-PILOT CONSOLE</h2>
          <p className="text-xs text-[#64748b]">Run signals analysis and query semantic maintenance standards</p>
        </div>
        <div className="h-10 w-10 rounded-lg bg-[#00f5d4]/10 border border-[#00f5d4]/20 flex items-center justify-center">
          <Activity className="h-5.5 w-5.5 text-[#00f5d4]" />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Input Panel (Left Column) */}
        <div className="lg:col-span-4 flex flex-col gap-6">
          <div className="bg-[#111827]/80 border border-[#1e293b] rounded-xl p-5 shadow-xl">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-4 text-[#00f5d4]">
              ⚡ Query Engine
            </h3>
            
            <form onSubmit={handleQuery} className="flex flex-col gap-3">
              <label className="text-xs text-[#94a3b8] font-medium">Enter Maintenance Query:</label>
              <textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                rows={4}
                className="w-full bg-[#0d1527] border border-[#2e374a] rounded-lg p-3 text-sm text-white focus:outline-none focus:border-[#00f5d4] focus:ring-1 focus:ring-[#00f5d4] placeholder-[#475569] resize-none font-mono"
                placeholder="Ask standard or real-time diagnostics parameters..."
              />
              
              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 bg-gradient-to-r from-[#0072ff] to-[#00f5d4] text-[#0b0f19] font-bold text-sm rounded-lg hover:shadow-lg transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
              >
                {loading ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    Analysing Waveforms...
                  </>
                ) : (
                  <>
                    <Send className="h-4 w-4" />
                    Execute Diagnostic
                  </>
                )}
              </button>
            </form>

            <div className="mt-6 border-t border-[#1e293b] pt-4">
              <h4 className="text-xs font-semibold text-[#64748b] mb-2 uppercase tracking-wide">Quick Queries</h4>
              <div className="flex flex-col gap-2">
                <button 
                  onClick={() => setQuery("Pump P-201 is vibrating loudly. What could be wrong?")}
                  className="text-left text-xs bg-[#0d1527] p-2.5 rounded-lg border border-[#1e293b] hover:border-[#00f5d4] transition-all text-[#94a3b8] hover:text-white"
                >
                  🔍 Pump P-201 Vibration Alert (Flag Discrepancy)
                </button>
                <button 
                  onClick={() => setQuery("What are the maintenance procedures for Pump P-201?")}
                  className="text-left text-xs bg-[#0d1527] p-2.5 rounded-lg border border-[#1e293b] hover:border-[#00f5d4] transition-all text-[#94a3b8] hover:text-white"
                >
                  📄 Procedures / SOP Specs for Pump P-201
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Results Panel (Right Column) */}
        <div className="lg:col-span-8 flex flex-col gap-6">
          {!result && !loading && (
            <div className="bg-[#111827]/40 border border-[#1e293b] rounded-2xl p-10 flex flex-col items-center justify-center text-center h-[350px]">
              <Cpu className="h-16 w-16 text-[#475569] mb-4 animate-pulse" />
              <h3 className="text-lg font-bold text-white mb-2">Platform Diagnostics Co-Pilot</h3>
              <p className="text-sm text-[#64748b] max-w-md">
                Enter parameters on the left to start multi-agent vibration and document verification.
              </p>
            </div>
          )}

          {loading && (
            <div className="bg-[#111827]/40 border border-[#1e293b] rounded-2xl p-10 flex flex-col items-center justify-center text-center h-[350px]">
              <RefreshCw className="h-12 w-12 text-[#00f5d4] mb-4 animate-spin" />
              <h3 className="text-lg font-bold text-white mb-2">Analyzing Signals...</h3>
              <p className="text-sm text-[#64748b]">Running FFT, calculating anomaly severity, indexing vectors...</p>
            </div>
          )}

          {result && (
            <div className="flex flex-col gap-6">
              
              {/* Log Console */}
              <div className="bg-[#0b0f19] border border-[#1e293b] rounded-xl p-4 shadow-inner">
                <h4 className="text-xs font-semibold text-[#64748b] mb-3 uppercase tracking-wider flex items-center gap-2">
                  <Layers className="h-3.5 w-3.5" />
                  Agent Execution Log
                </h4>
                <div ref={consoleRef} className="h-28 overflow-y-auto font-mono text-[11px] flex flex-col gap-1.5 scrollbar-thin scrollbar-thumb-slate-700">
                  {result.agent_log?.map((log, i) => (
                    <div key={i} className="flex gap-2">
                      <span className="text-[#475569]">[{log.timestamp}]</span>
                      <span className={`font-bold ${
                        log.level === "WARNING" ? "text-amber-500" : log.level === "ERROR" ? "text-rose-500" : "text-[#00f5d4]"
                      }`}>
                        [{log.level}]
                      </span>
                      <span className="text-slate-300">{log.message}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Path Traversal Proof */}
              {result.paths && result.paths.length > 0 && (
                <PathVisualization paths={result.paths} />
              )}

              {/* Multi-Agent Debate Panel */}
              {result.debate && (
                <div className="bg-[#111827]/80 border border-[#1e293b] rounded-xl p-5 shadow-lg flex flex-col gap-4">
                  <h3 className="text-xs font-bold text-[#00f5d4] uppercase tracking-wider flex items-center gap-2">
                    <Cpu className="h-4 w-4 text-[#00f5d4]" />
                    Multi-Agent Consensus Debate
                  </h3>

                  <div className="flex flex-col gap-3">
                    {/* Historian bubble */}
                    <div className="flex flex-col gap-1 p-3 bg-blue-950/10 border border-blue-900/20 rounded-lg text-xs">
                      <span className="text-[#4cc9f0] font-bold uppercase text-[9px] tracking-wide">📜 Historian Agent (RAG + KG)</span>
                      <p className="text-slate-300 italic">"{result.debate.historian}"</p>
                    </div>

                    {/* Physicist bubble */}
                    <div className="flex flex-col gap-1 p-3 bg-purple-950/10 border border-purple-900/20 rounded-lg text-xs">
                      <span className="text-purple-400 font-bold uppercase text-[9px] tracking-wide">🔬 Physicist Agent (Sensor Telemetry)</span>
                      <p className="text-slate-300 italic">"{result.debate.physicist}"</p>
                    </div>

                    {/* Operator bubble */}
                    <div className="flex flex-col gap-1 p-3 bg-emerald-950/10 border border-emerald-900/20 rounded-lg text-xs">
                      <span className="text-emerald-400 font-bold uppercase text-[9px] tracking-wide">🔧 Operator Agent (Tacit Knowledge)</span>
                      <p className="text-slate-300 italic">"{result.debate.operator}"</p>
                    </div>

                    {/* Consensus banner */}
                    <div className="p-3.5 bg-cyan-950/15 border border-cyan-900/40 rounded-lg text-xs flex flex-col gap-1">
                      <span className="text-[#00f5d4] font-bold uppercase text-[9px] tracking-wide">🤝 Consensus Resolution</span>
                      <p className="text-white font-semibold">{result.debate.consensus}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Conflict Detection Panel */}
              {result.conflict_detected && !conflictResolution && result.conflict_details && (
                <div className="bg-gradient-to-b from-[#1c1917] to-[#0c0a09] border border-amber-900/50 rounded-xl p-5 shadow-2xl flex flex-col gap-4">
                  <div className="flex items-center gap-3">
                    <AlertTriangle className="h-6 w-6 text-amber-500" />
                    <div>
                      <h3 className="text-md font-bold text-white">Discrepancy Detected between Standards and Live Physics!</h3>
                      <p className="text-xs text-amber-500/80">Automated engine recommends action plan below.</p>
                    </div>
                  </div>

                  {result.auto_resolution_recommendation && (
                    <div className="bg-[#1c1d21] border border-cyan-950 p-4 rounded-lg text-xs">
                      <span className="text-[#00f5d4] font-bold block mb-1">🤖 TRUTH ENGINE RECOMMENDATION</span>
                      Suggest resolving using <span className="text-white font-bold">{result.auto_resolution_recommendation.winner.toUpperCase()}</span>: <span className="italic">"{result.auto_resolution_recommendation.reason}"</span>
                    </div>
                  )}

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-[#0f172a]/80 p-4 rounded-lg border border-[#1e293b]">
                      <h4 className="text-xs font-bold text-sky-400 mb-2 uppercase">📄 SOP Documentation</h4>
                      <p className="text-xs text-slate-300 font-medium mb-3">{result.conflict_details.document_hypothesis}</p>
                      <div className="flex justify-between items-center text-[10px] text-[#64748b]">
                        <span>Confidence: {(result.conflict_details.document_confidence * 100).toFixed(0)}%</span>
                      </div>
                    </div>
                    <div className="bg-[#0f172a]/80 p-4 rounded-lg border border-[#1e293b]">
                      <h4 className="text-xs font-bold text-[#00f5d4] mb-2 uppercase">🔬 Live Physics</h4>
                      <p className="text-xs text-slate-300 font-medium mb-3">{result.conflict_details.physics_result}</p>
                      <div className="flex justify-between items-center text-[10px] text-[#64748b]">
                        <span>Confidence: {(result.conflict_details.physics_confidence * 100).toFixed(0)}%</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-2 pt-2">
                    <button
                      onClick={() => handleResolve("physics")}
                      className="flex-1 py-2 px-3 bg-gradient-to-r from-emerald-500 to-teal-500 text-white font-bold text-xs rounded-lg hover:shadow-lg cursor-pointer"
                    >
                      ✅ Trust Physics Result
                    </button>
                    <button
                      onClick={() => handleResolve("documents")}
                      className="flex-1 py-2 px-3 bg-[#1e293b] border border-[#2e374a] text-white font-semibold text-xs rounded-lg cursor-pointer"
                    >
                      📄 Trust Document SOP
                    </button>
                    <button
                      onClick={() => setShowInterview(true)}
                      className="flex-1 py-2 px-3 bg-[#0d1527] border border-cyan-900/50 text-[#00f5d4] font-semibold text-xs rounded-lg cursor-pointer"
                    >
                      🎙️ Interview Senior Engineer
                    </button>
                  </div>

                  {showInterview && (
                    <div className="border-t border-[#2e374a] pt-4 mt-2 flex flex-col gap-3">
                      <div className="p-3 bg-[#0c0a09] border border-amber-900/30 rounded-lg text-xs text-amber-500/90 font-mono">
                        {result.human_question}
                      </div>
                      <textarea
                        value={humanResponse}
                        onChange={(e) => setHumanResponse(e.target.value)}
                        rows={2}
                        className="w-full bg-[#0d1527] border border-[#2e374a] rounded-lg p-3 text-xs text-white focus:outline-none focus:border-[#00f5d4]"
                        placeholder="Type unwritten engineer workaround details..."
                      />
                      <div className="flex gap-2 justify-end">
                        <button
                          onClick={() => handleResolve("human")}
                          className="py-2 px-4 bg-gradient-to-r from-[#0072ff] to-[#00f5d4] text-[#0b0f19] font-bold text-xs rounded-lg cursor-pointer"
                        >
                          Submit Rule
                        </button>
                        <button
                          onClick={() => setShowInterview(false)}
                          className="py-2 px-4 bg-[#1e293b] border border-[#2e374a] text-xs rounded-lg cursor-pointer"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Resolved Conflict State */}
              {conflictResolution && (
                <div className="bg-[#0f172a] border border-[#2e374a] rounded-xl p-5 shadow-md flex flex-col gap-3">
                  <div className="flex items-center gap-2 text-xs font-bold text-slate-400">
                    <CheckCircle className="h-4 w-4 text-[#00f5d4]" />
                    DISCREPANCY RESOLVED: {conflictResolution.toUpperCase()} WINS
                  </div>
                  {conflictResolution === 'human' && resolutionDetails?.structured_rule && (
                    <div className="p-4 bg-emerald-950/20 border border-emerald-900/50 rounded-lg text-xs">
                      <div className="font-bold text-[#52b788] mb-2">💾 STRUCTURED TACIT RULE CAPTURED</div>
                      <p className="italic text-emerald-300 font-mono">"{resolutionDetails.structured_rule.rule_text}"</p>
                    </div>
                  )}
                  {resolutionDetails?.healed_nodes && (
                    <div className="text-xs text-[#94a3b8]">
                      🩹 Graph self-healing applied. Check the <strong className="text-white">Self-Healing Graph</strong> page to view node changes.
                    </div>
                  )}
                </div>
              )}

              {/* Diagnostics Output Section */}
              {(!result.conflict_detected || conflictResolution) && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="md:col-span-2 bg-[#111827]/85 border border-[#1e293b] rounded-xl p-5 shadow-lg">
                    <div className="flex justify-between items-center mb-3">
                      <h3 className="text-sm font-bold text-white">📝 Synthesized Action Plan</h3>
                      <button
                        onClick={() => window.print()}
                        className="px-2.5 py-1.5 bg-[#0d1527] border border-[#2e374a] hover:border-[#00f5d4] hover:text-white rounded-lg text-[10px] font-semibold text-[#94a3b8] transition-all flex items-center gap-1.5 cursor-pointer"
                        title="Export safety report as PDF"
                      >
                        Export Report PDF
                      </button>
                    </div>
                    <div className="text-xs text-slate-300 leading-relaxed font-mono whitespace-pre-wrap">
                      {result.final_answer}
                    </div>
                  </div>
                  
                  <div className="bg-[#111827]/85 border border-[#1e293b] rounded-xl p-5 shadow-lg">
                    <h3 className="text-sm font-bold text-white mb-3">📊 Waveform Signature</h3>
                    {result.physics_result ? (
                      <div className="flex flex-col gap-3 text-xs">
                        <div>
                          <span className="text-[#64748b] text-[10px] block uppercase">Diagnosis</span>
                          <span className="text-white font-bold">{result.physics_result.fault_type}</span>
                        </div>
                        <div>
                          <span className="text-[#64748b] text-[10px] block uppercase">Severity</span>
                          <span className="text-rose-400 font-bold">{result.physics_result.severity}</span>
                        </div>
                        <div>
                          <span className="text-[#64748b] text-[10px] block uppercase">Action Required</span>
                          <p className="text-slate-400 text-[11px] leading-tight">{result.physics_result.recommendation}</p>
                        </div>
                      </div>
                    ) : (
                      <span className="text-xs text-[#475569]">No active physics telemetry.</span>
                    )}
                  </div>
                </div>
              )}

              {result.work_order && (
                <div className="p-4 bg-[#0d1527] border border-[#1e293b] rounded-lg text-xs text-slate-400">
                  🛠️ A maintenance work order has been generated automatically. Navigate to the <strong className="text-white">Work Orders & Alerts</strong> page to view full details.
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
