"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Activity, AlertTriangle, Send, Cpu, ShieldAlert, CheckCircle,
  Loader2, BookOpen, Zap, Wrench, MessageSquare, ChevronRight,
  FileText, Eye, X
} from "lucide-react";
import { VoiceInput } from "./components/VoiceInput";
import { PathVisualization } from "./components/PathVisualization";

/* ─────────────────────────────────── Types ─────────────────────────────────── */
interface AgentLog { timestamp: string; level: string; message: string; }

interface QueryResult {
  asset_id?: string;
  conflict_detected: boolean;
  conflict_details?: {
    description: string;
    document_hypothesis: string;
    document_confidence: number;
    physics_result: string;
    physics_confidence: number;
    sources: { documents: string; physics: string; };
    auto_resolution?: { winner: string; reason: string; confidence: number; };
  };
  auto_resolution_recommendation?: { winner: string; reason: string; confidence: number; };
  human_question?: string;
  final_answer?: string;
  physics_result?: { fault_type: string; severity: string; recommendation: string; };
  work_order?: Record<string, unknown>;
  proactive_alerts?: unknown[];
  agent_log?: AgentLog[];
  paths?: unknown[];
  compliance_gaps?: unknown[];
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
  structured_rule?: { type: string; confidence: number; rule_text: string; };
  agent_log?: AgentLog[];
}

/* ─────────────────────────────── Agent Pipeline ───────────────────────────── */
const PIPELINE_STEPS = [
  { id: "historian",  label: "Historian",  icon: BookOpen,      desc: "RAG + KG retrieval" },
  { id: "physicist",  label: "Simulator",  icon: Activity,      desc: "Physics analysis" },
  { id: "conflict",   label: "Conflict",   icon: AlertTriangle, desc: "Discrepancy check" },
  { id: "synthesis",  label: "Synthesis",  icon: Cpu,           desc: "Final answer" },
];

function PipelineBar({ loading, result }: { loading: boolean; result: QueryResult | null }) {
  const getStepState = (stepId: string) => {
    if (!result && !loading) return "idle";
    if (loading) return stepId === "historian" ? "active" : "idle";
    if (result) return "done";
    return "idle";
  };
  return (
    <div className="flex items-start gap-0" style={{ display: "flex", alignItems: "flex-start", gap: 0 }}>
      {PIPELINE_STEPS.map((step, i) => {
        const state = getStepState(step.id);
        const Icon = step.icon;
        return (
          <div key={step.id} className="pipeline-step" style={{ flex: 1, position: "relative" }}>
            {i > 0 && (
              <div style={{
                position: "absolute",
                left: "-50%",
                top: 14,
                width: "100%",
                height: 1,
                background: state === "done" ? "var(--accent)" : "var(--border)",
                zIndex: 0,
                transition: "background 0.3s ease"
              }} />
            )}
            <div
              className={`pipeline-dot ${state}`}
              style={{
                width: 28, height: 28, borderRadius: "50%",
                border: `1.5px solid ${state === "done" ? "var(--accent)" : state === "active" ? "var(--accent)" : "var(--border)"}`,
                background: state === "done" ? "var(--accent-dim)" : state === "active" ? "var(--accent)" : "var(--bg-surface)",
                color: state === "active" ? "var(--bg-base)" : state === "done" ? "var(--accent)" : "var(--text-muted)",
                display: "flex", alignItems: "center", justifyContent: "center",
                position: "relative", zIndex: 1, margin: "0 auto",
                boxShadow: state === "active" ? "0 0 12px var(--accent-glow)" : "none",
              }}
            >
              {state === "active" ? (
                <Loader2 size={12} style={{ animation: "spin 1s linear infinite" }} />
              ) : (
                <Icon size={12} />
              )}
            </div>
            <div style={{ marginTop: 6, textAlign: "center" }}>
              <div style={{ fontSize: 10, fontWeight: 600, color: state === "done" ? "var(--accent)" : "var(--text-muted)", letterSpacing: "0.05em" }}>
                {step.label}
              </div>
              <div style={{ fontSize: 10, color: "var(--text-muted)", marginTop: 1 }}>{step.desc}</div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

/* ────────────────────────────── Metric Card ───────────────────────────────── */
function MetricCard({ label, value, valueColor }: { label: string; value: string; valueColor?: string }) {
  return (
    <div style={{
      padding: "12px 16px",
      background: "var(--bg-base)",
      border: "1px solid var(--border-dim)",
      borderRadius: "var(--r-sm)",
      flex: 1,
    }}>
      <div className="label" style={{ marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 13, fontWeight: 600, color: valueColor || "var(--text-primary)" }}>
        {value}
      </div>
    </div>
  );
}

/* ────────────────────────────── Agent Bubble ──────────────────────────────── */
const AGENT_STYLES: Record<string, { color: string; label: string; initial: string }> = {
  historian: { color: "#6366f1", label: "Historian Agent",  initial: "H" },
  physicist: { color: "#22d3ee", label: "Physicist Agent",  initial: "P" },
  operator:  { color: "#10b981", label: "Operator Agent",   initial: "O" },
  consensus: { color: "#f59e0b", label: "Consensus",        initial: "C" },
};

function AgentBubble({ agent, text }: { agent: string; text: string }) {
  const style = AGENT_STYLES[agent] || { color: "#a1a1aa", label: agent, initial: "?" };
  return (
    <div style={{
      padding: "12px 14px",
      background: "var(--bg-base)",
      border: "1px solid var(--border-dim)",
      borderLeft: `2px solid ${style.color}`,
      borderRadius: "var(--r-sm)",
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
        <div style={{
          width: 20, height: 20, borderRadius: "50%",
          background: `${style.color}18`,
          color: style.color, fontSize: 10, fontWeight: 700,
          display: "flex", alignItems: "center", justifyContent: "center",
          border: `1px solid ${style.color}40`,
        }}>
          {style.initial}
        </div>
        <span style={{ fontSize: 10, fontWeight: 600, color: style.color, letterSpacing: "0.06em", textTransform: "uppercase" }}>
          {style.label}
        </span>
      </div>
      <p style={{ fontSize: 12, color: "var(--text-secondary)", lineHeight: 1.6, fontStyle: "italic" }}>
        &ldquo;{text}&rdquo;
      </p>
    </div>
  );
}

/* ─────────────────────────── Log Console ──────────────────────────────────── */
function LogConsole({ logs }: { logs: AgentLog[] }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (ref.current) ref.current.scrollTop = ref.current.scrollHeight;
  }, [logs]);

  const levelColor = (l: string) =>
    l === "WARNING" ? "#f59e0b" : l === "ERROR" ? "#f43f5e" : "#22d3ee";

  return (
    <div style={{
      background: "var(--bg-base)",
      border: "1px solid var(--border-dim)",
      borderRadius: "var(--r-sm)",
      padding: "10px 14px",
    }}>
      <div className="label" style={{ marginBottom: 8 }}>Execution log</div>
      <div ref={ref} style={{ maxHeight: 120, overflowY: "auto", display: "flex", flexDirection: "column", gap: 3 }}>
        {logs.length === 0 ? (
          <span className="mono" style={{ color: "var(--text-muted)" }}>— no logs —</span>
        ) : (
          logs.map((log, i) => (
            <div key={i} className="mono" style={{ display: "flex", gap: 8, alignItems: "flex-start" }}>
              <span style={{ color: "var(--text-muted)", flexShrink: 0 }}>[{log.timestamp}]</span>
              <span style={{ color: levelColor(log.level), fontWeight: 700, flexShrink: 0 }}>[{log.level}]</span>
              <span style={{ color: "#d4d4d8" }}>{log.message}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

/* ─────────────────────────── Main Page ────────────────────────────────────── */
const QUICK_QUERIES = [
  { label: "P-201 High Vibration", query: "Pump P-201 is vibrating loudly. What could be wrong?" },
  { label: "LOTO Procedure P-201", query: "What are the lockout-tagout steps for Pump P-201 bearing replacement?" },
  { label: "SOP Contradiction Check", query: "Check for contradictions in P-201 maintenance SOP between 2019 and 2024 versions." },
];

export default function Home() {
  const [query, setQuery] = useState("Pump P-201 is vibrating loudly. What could be wrong?");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QueryResult | null>(null);
  const [resolving, setResolving] = useState(false);
  const [conflictResolution, setConflictResolution] = useState<string | null>(null);
  const [resolutionDetails, setResolutionDetails] = useState<ResolutionDetails | null>(null);
  const [showInterview, setShowInterview] = useState(false);
  const [humanResponse, setHumanResponse] = useState("");

  useEffect(() => {
    try {
      const saved = localStorage.getItem("query_result");
      if (saved) setResult(JSON.parse(saved));
      const savedRes = localStorage.getItem("conflict_resolution");
      if (savedRes) setConflictResolution(savedRes);
      const savedDet = localStorage.getItem("resolution_details");
      if (savedDet) setResolutionDetails(JSON.parse(savedDet));
    } catch {}
  }, []);

  const handleQuery = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setLoading(true);
    setResult(null);
    setConflictResolution(null);
    setResolutionDetails(null);
    setShowInterview(false);
    setHumanResponse("");
    localStorage.removeItem("query_result");
    localStorage.removeItem("conflict_resolution");
    localStorage.removeItem("resolution_details");
    try {
      const res = await fetch("http://localhost:8000/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": "Bearer dev-key" },
        body: JSON.stringify({ query }),
      });
      if (res.ok) {
        const data = await res.json();
        setResult(data);
        localStorage.setItem("query_result", JSON.stringify(data));
      }
    } catch (err) {
      console.error("Query failed:", err);
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
        headers: { "Content-Type": "application/json", "Authorization": "Bearer dev-key" },
        body: JSON.stringify({ query_result: result, choice, human_feedback: choice === "human" ? humanResponse : null }),
      });
      if (res.ok) {
        const data = await res.json();
        setResolutionDetails(data);
        setConflictResolution(choice);
        setShowInterview(false);
        localStorage.setItem("conflict_resolution", choice);
        localStorage.setItem("resolution_details", JSON.stringify(data));
        const updatedResult = { ...result };
        if (updatedResult.agent_log && data.agent_log)
          updatedResult.agent_log = [...updatedResult.agent_log, ...data.agent_log];
        setResult(updatedResult);
        localStorage.setItem("query_result", JSON.stringify(updatedResult));
      }
    } catch (err) {
      console.error("Resolve failed:", err);
    } finally {
      setResolving(false);
    }
  };

  const severityColor = (s?: string) => {
    if (!s) return "var(--text-secondary)";
    const sl = s.toLowerCase();
    if (sl.includes("critical") || sl.includes("high")) return "var(--danger)";
    if (sl.includes("medium") || sl.includes("moderate")) return "var(--warning)";
    return "var(--success)";
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 32, padding: "32px 40px", flex: 1 }}>

      {/* ── Page header ── */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div>
          <div className="label">Diagnostics Engine</div>
          <h1 style={{ fontSize: 18, fontWeight: 600, color: "var(--text-primary)", marginTop: 2 }}>
            Maintenance Co-Pilot
          </h1>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <div style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--success)", boxShadow: "0 0 6px #10b98166" }} />
          <span style={{ fontSize: 12, color: "var(--text-muted)" }}>API Live</span>
        </div>
      </div>

      {/* ── Pipeline strip ── */}
      <div className="card" style={{ padding: "24px 32px" }}>
        <PipelineBar loading={loading} result={result} />
      </div>

      {/* ── Main grid ── */}
      <div style={{ display: "grid", gridTemplateColumns: "360px 1fr", gap: 32, alignItems: "start" }}>

        {/* ── LEFT: Query panel ── */}
        <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
          <div className="card" style={{ padding: 24 }}>
            <form onSubmit={handleQuery} style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              <div className="label">Query</div>
              <textarea
                className="textarea"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                rows={5}
                placeholder="Describe the fault or ask a maintenance question…"
              />
              <div style={{ display: "flex", gap: 8 }}>
                <button
                  type="submit"
                  disabled={loading}
                  className="btn btn-primary"
                  style={{ flex: 1 }}
                >
                  {loading ? (
                    <><Loader2 size={14} style={{ animation: "spin 1s linear infinite" }} /> Analysing…</>
                  ) : (
                    <><Send size={14} /> Run Diagnostic</>
                  )}
                </button>
                <VoiceInput onTranscript={(t) => setQuery(t)} />
              </div>
            </form>
          </div>

          {/* Quick queries */}
          <div className="card" style={{ padding: 24 }}>
            <div className="label" style={{ marginBottom: 10 }}>Quick queries</div>
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              {QUICK_QUERIES.map((q) => (
                <button
                  key={q.label}
                  onClick={() => setQuery(q.query)}
                  style={{
                    display: "flex", alignItems: "center", justifyContent: "space-between",
                    padding: "8px 10px", borderRadius: "var(--r-sm)",
                    background: "var(--bg-base)", border: "1px solid var(--border-dim)",
                    cursor: "pointer", textAlign: "left", width: "100%",
                    transition: "border-color 0.15s, background 0.15s",
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.borderColor = "var(--border)")}
                  onMouseLeave={(e) => (e.currentTarget.style.borderColor = "var(--border-dim)")}
                >
                  <span style={{ fontSize: 12, color: "var(--text-secondary)" }}>{q.label}</span>
                  <ChevronRight size={12} color="var(--text-muted)" />
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* ── RIGHT: Results panel ── */}
        <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>

          {/* Empty state */}
          {!result && !loading && (
            <div className="card" style={{
              padding: 48, display: "flex", flexDirection: "column",
              alignItems: "center", justifyContent: "center", textAlign: "center", gap: 12, minHeight: 300,
            }}>
              <div style={{
                width: 48, height: 48, borderRadius: "var(--r-md)",
                background: "var(--bg-base)", border: "1px solid var(--border)",
                display: "flex", alignItems: "center", justifyContent: "center",
              }}>
                <Cpu size={22} color="var(--text-muted)" />
              </div>
              <div>
                <p style={{ fontSize: 14, fontWeight: 500, color: "var(--text-primary)" }}>Run a diagnostic query</p>
                <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 4 }}>
                  Multi-agent analysis across SOPs, vibration telemetry, and operator knowledge
                </p>
              </div>
            </div>
          )}

          {/* Loading state */}
          {loading && (
            <div className="card" style={{
              padding: 48, display: "flex", flexDirection: "column",
              alignItems: "center", justifyContent: "center", gap: 14, minHeight: 300,
            }}>
              <Loader2 size={28} color="var(--accent)" style={{ animation: "spin 1s linear infinite" }} />
              <div style={{ textAlign: "center" }}>
                <p style={{ fontSize: 14, fontWeight: 500, color: "var(--text-primary)" }}>Analysing…</p>
                <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 4 }}>
                  FFT waveform analysis · RAG retrieval · Knowledge graph traversal
                </p>
              </div>
            </div>
          )}

          {/* Results */}
          {result && (
            <div className="animate-fade-in" style={{ display: "flex", flexDirection: "column", gap: 14 }}>

              {/* Log console */}
              {result.agent_log && result.agent_log.length > 0 && (
                <LogConsole logs={result.agent_log} />
              )}

              {/* Physics metrics */}
              {result.physics_result && (
                <div style={{ display: "flex", gap: 10 }}>
                  <MetricCard label="Fault Diagnosis" value={result.physics_result.fault_type} />
                  <MetricCard
                    label="Severity"
                    value={result.physics_result.severity}
                    valueColor={severityColor(result.physics_result.severity)}
                  />
                  <MetricCard label="Action" value={result.physics_result.recommendation} />
                </div>
              )}

              {/* Conflict detected */}
              {result.conflict_detected && !conflictResolution && result.conflict_details && (
                <div className="conflict-card animate-slide-up" style={{ padding: 24 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 14 }}>
                    <div style={{
                      width: 32, height: 32, borderRadius: "var(--r-sm)",
                      background: "rgba(244,63,94,0.1)", border: "1px solid rgba(244,63,94,0.3)",
                      display: "flex", alignItems: "center", justifyContent: "center",
                    }}>
                      <AlertTriangle size={15} color="var(--danger)" />
                    </div>
                    <div>
                      <p style={{ fontSize: 13, fontWeight: 600, color: "var(--text-primary)" }}>Conflict Detected</p>
                      <p style={{ fontSize: 11, color: "var(--text-muted)" }}>{result.conflict_details.description}</p>
                    </div>
                    {result.auto_resolution_recommendation && (
                      <div className="badge badge-warning" style={{ marginLeft: "auto" }}>
                        AI recommends: {result.auto_resolution_recommendation.winner}
                      </div>
                    )}
                  </div>

                  {/* SOP vs Physics two-column */}
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 14 }}>
                    <div style={{
                      padding: "12px 14px",
                      background: "rgba(99,102,241,0.06)", border: "1px solid rgba(99,102,241,0.2)",
                      borderRadius: "var(--r-sm)",
                    }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 8 }}>
                        <FileText size={11} color="#818cf8" />
                        <span style={{ fontSize: 10, fontWeight: 600, color: "#818cf8", letterSpacing: "0.06em", textTransform: "uppercase" }}>
                          SOP Document
                        </span>
                        <span className="badge badge-info" style={{ marginLeft: "auto" }}>
                          {(result.conflict_details.document_confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                      <p style={{ fontSize: 12, color: "var(--text-secondary)", lineHeight: 1.6 }}>
                        {result.conflict_details.document_hypothesis}
                      </p>
                    </div>
                    <div style={{
                      padding: "12px 14px",
                      background: "var(--accent-dim)", border: "1px solid rgba(34,211,238,0.2)",
                      borderRadius: "var(--r-sm)",
                    }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 8 }}>
                        <Activity size={11} color="var(--accent)" />
                        <span style={{ fontSize: 10, fontWeight: 600, color: "var(--accent)", letterSpacing: "0.06em", textTransform: "uppercase" }}>
                          Live Physics
                        </span>
                        <span className="badge badge-accent" style={{ marginLeft: "auto" }}>
                          {(result.conflict_details.physics_confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                      <p style={{ fontSize: 12, color: "var(--text-secondary)", lineHeight: 1.6 }}>
                        {result.conflict_details.physics_result}
                      </p>
                    </div>
                  </div>

                  {/* Resolution buttons */}
                  <div style={{ display: "flex", gap: 8 }}>
                    <button
                      className="btn btn-primary"
                      style={{ flex: 1, fontSize: 12 }}
                      onClick={() => handleResolve("physics")}
                      disabled={resolving}
                    >
                      <Activity size={12} /> Trust Live Physics
                    </button>
                    <button
                      className="btn btn-ghost"
                      style={{ flex: 1, fontSize: 12 }}
                      onClick={() => handleResolve("documents")}
                      disabled={resolving}
                    >
                      <FileText size={12} /> Trust SOP Document
                    </button>
                    <button
                      className="btn btn-ghost"
                      style={{ fontSize: 12 }}
                      onClick={() => setShowInterview(!showInterview)}
                    >
                      <MessageSquare size={12} /> Ask Engineer
                    </button>
                  </div>

                  {/* Tacit interview */}
                  {showInterview && (
                    <div style={{
                      marginTop: 14, paddingTop: 14, borderTop: "1px solid var(--border)",
                      display: "flex", flexDirection: "column", gap: 10,
                    }}>
                      <div style={{ fontSize: 12, color: "var(--warning)", fontFamily: "monospace" }}>
                        {result.human_question}
                      </div>
                      <textarea
                        className="textarea"
                        rows={2}
                        value={humanResponse}
                        onChange={(e) => setHumanResponse(e.target.value)}
                        placeholder="Share the unwritten workaround or field knowledge…"
                      />
                      <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
                        <button className="btn btn-primary" style={{ fontSize: 12 }} onClick={() => handleResolve("human")}>
                          Submit Rule
                        </button>
                        <button className="btn btn-ghost" style={{ fontSize: 12 }} onClick={() => setShowInterview(false)}>
                          Cancel
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Conflict resolved */}
              {conflictResolution && (
                <div className="card" style={{ padding: "12px 16px", display: "flex", alignItems: "flex-start", gap: 12 }}>
                  <CheckCircle size={16} color="var(--success)" style={{ marginTop: 1, flexShrink: 0 }} />
                  <div>
                    <p style={{ fontSize: 13, fontWeight: 600 }}>
                      Conflict resolved — <span style={{ color: "var(--accent)" }}>{conflictResolution.toUpperCase()}</span> applied
                    </p>
                    {conflictResolution === "human" && resolutionDetails?.structured_rule && (
                      <div style={{
                        marginTop: 10, padding: "10px 12px",
                        background: "rgba(16,185,129,0.06)", border: "1px solid rgba(16,185,129,0.2)",
                        borderRadius: "var(--r-sm)",
                      }}>
                        <div className="label" style={{ color: "var(--success)", marginBottom: 4 }}>Tacit rule captured</div>
                        <p className="mono" style={{ color: "#6ee7b7", lineHeight: 1.6 }}>
                          &ldquo;{resolutionDetails.structured_rule.rule_text}&rdquo;
                        </p>
                      </div>
                    )}
                    {resolutionDetails?.healed_nodes && resolutionDetails.healed_nodes.length > 0 && (
                      <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 6 }}>
                        Knowledge graph updated · {resolutionDetails.healed_nodes.length} node(s) healed
                      </p>
                    )}
                  </div>
                </div>
              )}

              {/* Final answer */}
              {(!result.conflict_detected || conflictResolution) && result.final_answer && (
                <div className="card" style={{ padding: 24 }}>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
                    <div className="label">Synthesized action plan</div>
                    <button
                      className="btn btn-ghost"
                      style={{ fontSize: 11, padding: "4px 10px" }}
                      onClick={() => window.print()}
                    >
                      <Eye size={11} /> Export PDF
                    </button>
                  </div>
                  <div className="mono" style={{ color: "var(--text-secondary)", lineHeight: 1.8, whiteSpace: "pre-wrap" }}>
                    {result.final_answer}
                  </div>
                </div>
              )}

              {/* Multi-agent debate */}
              {result.debate && (
                <div className="card" style={{ padding: 24 }}>
                  <div className="label" style={{ marginBottom: 12 }}>Multi-agent debate</div>
                  <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                    {Object.entries(result.debate).map(([agent, text]) => (
                      <AgentBubble key={agent} agent={agent} text={text} />
                    ))}
                  </div>
                </div>
              )}

              {/* Path traversal */}
              {result.paths && result.paths.length > 0 && (
                <PathVisualization paths={result.paths as Parameters<typeof PathVisualization>[0]["paths"]} />
              )}

              {/* Work order notice */}
              {result.work_order && (
                <div style={{
                  padding: "10px 14px", display: "flex", alignItems: "center", gap: 10,
                  background: "var(--bg-base)", border: "1px solid var(--border-dim)",
                  borderRadius: "var(--r-sm)",
                }}>
                  <Wrench size={13} color="var(--text-muted)" />
                  <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
                    Work order auto-generated —{" "}
                    <a href="/maintenance" style={{ color: "var(--accent)", textDecoration: "none" }}>
                      view in Maintenance →
                    </a>
                  </span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        .animate-fade-in  { animation: fadeIn  0.3s ease both; }
        .animate-slide-up { animation: slideUp 0.4s ease both; }
        @keyframes fadeIn  { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes slideUp { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: translateY(0); } }
      `}</style>
    </div>
  );
}
