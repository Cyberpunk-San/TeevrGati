"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Send,
  Cpu,
  AlertTriangle,
  CheckCircle2,
  ChevronRight,
  Zap,
  BookOpen,
  FlaskConical,
  GitBranch,
  GraduationCap,
  Mic,
  MicOff,
  FileText,
  Activity,
  Loader2,
} from "lucide-react";

/* ── Types (unchanged from original) ─────────────────── */
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
  work_order?: unknown;
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
  structured_rule?: {
    type: string;
    confidence: number;
    rule_text: string;
  };
  agent_log?: AgentLog[];
}

/* ── Loading phase labels ─────────────────────────────── */
const LOAD_PHASES = [
  "Querying historian agent…",
  "Running physics simulation…",
  "Checking SOP conflicts…",
  "Synthesising final answer…",
];

/* ── Agent pipeline config ───────────────────────────── */
const PIPELINE_STEPS = [
  { id: "historian",  label: "Historian",  icon: BookOpen },
  { id: "simulator",  label: "Simulator",  icon: FlaskConical },
  { id: "conflict",   label: "Conflict",   icon: GitBranch },
  { id: "mentor",     label: "Mentor",     icon: GraduationCap },
];

/* ── Debate agent config ──────────────────────────────── */
const DEBATE_AGENTS = [
  {
    key: "historian" as const,
    label: "Historian",
    sub: "RAG + KG",
    letter: "H",
    border: "border-l-sky-500",
    text: "text-sky-400",
    bg: "bg-sky-500/5",
  },
  {
    key: "physicist" as const,
    label: "Physicist",
    sub: "Sensor Telemetry",
    letter: "P",
    border: "border-l-violet-500",
    text: "text-violet-400",
    bg: "bg-violet-500/5",
  },
  {
    key: "operator" as const,
    label: "Operator",
    sub: "Tacit Knowledge",
    letter: "O",
    border: "border-l-emerald-500",
    text: "text-emerald-400",
    bg: "bg-emerald-500/5",
  },
  {
    key: "consensus" as const,
    label: "Consensus",
    sub: "Resolution",
    letter: "C",
    border: "border-l-[#22d3ee]",
    text: "text-[#22d3ee]",
    bg: "bg-[#22d3ee]/5",
  },
];

/* ── Quick preset queries ─────────────────────────────── */
const QUICK_QUERIES = [
  {
    label: "P-201 High Vibration",
    query: "Pump P-201 is vibrating loudly. What could be wrong?",
  },
  {
    label: "LOTO Procedure P-201",
    query: "What are the LOTO lockout/tagout procedures for Pump P-201?",
  },
  {
    label: "SOP Contradiction Check",
    query: "What are the maintenance procedures for Pump P-201?",
  },
];

/* ── Severity colour ──────────────────────────────────── */
function severityClass(s?: string) {
  if (!s) return "text-[#a1a1aa]";
  const l = s.toLowerCase();
  if (l.includes("critical") || l.includes("high")) return "text-rose-400";
  if (l.includes("medium") || l.includes("moderate")) return "text-amber-400";
  return "text-emerald-400";
}

/* ── Inline VoiceInput ────────────────────────────────── */
function VoiceButton({ onTranscript }: { onTranscript: (t: string) => void }) {
  const [listening, setListening] = useState(false);

  const start = () => {
    const SR =
      (window as Record<string, unknown>).SpeechRecognition as typeof SpeechRecognition ||
      (window as Record<string, unknown>).webkitSpeechRecognition as typeof SpeechRecognition;
    if (!SR) { alert("Speech recognition not supported in this browser."); return; }
    const r = new SR();
    r.lang = "en-US";
    r.continuous = false;
    r.interimResults = false;
    r.onstart = () => setListening(true);
    r.onend   = () => setListening(false);
    r.onerror = () => setListening(false);
    r.onresult = (e: SpeechRecognitionEvent) => {
      const t = e.results[0][0].transcript;
      if (t) onTranscript(t);
    };
    r.start();
  };

  return (
    <button
      type="button"
      onClick={start}
      disabled={listening}
      title={listening ? "Listening…" : "Voice input"}
      className={`p-1.5 rounded-[4px] border transition-colors cursor-pointer ${
        listening
          ? "border-rose-500/50 bg-rose-500/10 text-rose-400"
          : "border-[#27272a] text-[#52525b] hover:border-[#22d3ee] hover:text-[#22d3ee]"
      }`}
    >
      {listening ? <MicOff className="h-3.5 w-3.5" /> : <Mic className="h-3.5 w-3.5" />}
    </button>
  );
}

/* ══════════════════════════════════════════════════════ */
/*  Main Page                                             */
/* ══════════════════════════════════════════════════════ */
export default function Home() {
  const [query, setQuery] = useState(
    "Pump P-201 is vibrating loudly. What could be wrong?"
  );
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QueryResult | null>(null);
  const [phaseIdx, setPhaseIdx] = useState(0);

  // Resolution states (identical to original)
  const [resolving, setResolving]               = useState(false);
  const [conflictResolution, setConflictResolution] = useState<string | null>(null);
  const [resolutionDetails, setResolutionDetails]   = useState<ResolutionDetails | null>(null);
  const [showInterview, setShowInterview]            = useState(false);
  const [humanResponse, setHumanResponse]            = useState("");

  const resultsRef = useRef<HTMLDivElement>(null);

  // Restore from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem("query_result");
    if (saved) {
      try { setResult(JSON.parse(saved)); } catch { /* ignore */ }
    }
    const savedRes = localStorage.getItem("conflict_resolution");
    if (savedRes) setConflictResolution(savedRes);
    const savedDet = localStorage.getItem("resolution_details");
    if (savedDet) {
      try { setResolutionDetails(JSON.parse(savedDet)); } catch { /* ignore */ }
    }
  }, []);

  // Cycle loading phases
  useEffect(() => {
    if (!loading) { setPhaseIdx(0); return; }
    const id = setInterval(
      () => setPhaseIdx((p) => (p + 1) % LOAD_PHASES.length),
      1200
    );
    return () => clearInterval(id);
  }, [loading]);

  /* ── handleQuery (unchanged logic) ─────────────────── */
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
        headers: {
          "Content-Type": "application/json",
          Authorization: "Bearer dev-key",
        },
        body: JSON.stringify({ query }),
      });
      if (res.ok) {
        const data = await res.json();
        setResult(data);
        localStorage.setItem("query_result", JSON.stringify(data));
        setTimeout(() => {
          resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
        }, 100);
      }
    } catch (err) {
      console.error("Query request failed:", err);
    } finally {
      setLoading(false);
    }
  };

  /* ── handleResolve (unchanged logic) ───────────────── */
  const handleResolve = async (choice: string) => {
    if (!result) return;
    setResolving(true);
    try {
      const res = await fetch("http://localhost:8000/api/resolve", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: "Bearer dev-key",
        },
        body: JSON.stringify({
          query_result: result,
          choice,
          human_feedback: choice === "human" ? humanResponse : null,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setResolutionDetails(data);
        setConflictResolution(choice);
        setShowInterview(false);
        localStorage.setItem("conflict_resolution", choice);
        localStorage.setItem("resolution_details", JSON.stringify(data));
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

  /* ── Derived pipeline state ─────────────────────────── */
  const pipelineDone = result != null;

  /* ─────────────────────────────────────────────────── */
  /*  RENDER                                             */
  /* ─────────────────────────────────────────────────── */
  return (
    <div className="p-6 h-full flex flex-col gap-6">

      {/* ── Page header ─────────────────────────────── */}
      <div className="flex items-center justify-between">
        <div>
          <p className="text-[10px] font-semibold tracking-[.15em] text-[#52525b] uppercase mb-1">
            Diagnostics Engine
          </p>
          <h1 className="text-base font-semibold text-[#fafafa] tracking-tight">
            AI Diagnostics Co-Pilot
          </h1>
        </div>
        {pipelineDone && (
          <span className="badge badge-success animate-fade-in">
            <CheckCircle2 className="h-3 w-3" />
            Analysis complete
          </span>
        )}
        {loading && (
          <span className="badge badge-info animate-pulse">
            <Loader2 className="h-3 w-3 animate-spin" />
            Processing
          </span>
        )}
      </div>

      {/* ── Two-column layout ───────────────────────── */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-[35%_65%] gap-5 min-h-0">

        {/* ════════════════════════════════════════════ */}
        {/*  LEFT — Query Panel                          */}
        {/* ════════════════════════════════════════════ */}
        <div className="flex flex-col gap-4">
          <div className="card p-5 flex flex-col gap-4">

            {/* Section label */}
            <p className="text-[10px] font-semibold tracking-[.15em] text-[#52525b] uppercase">
              Diagnostics Engine
            </p>

            {/* Textarea */}
            <form onSubmit={handleQuery} className="flex flex-col gap-3">
              <div className="relative">
                <textarea
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  rows={5}
                  placeholder="Describe the equipment issue or ask a maintenance question…"
                  className={`w-full bg-[#09090b] border-0 border-b-2 rounded-none px-0 pb-2 pt-1 text-sm text-[#fafafa] placeholder-[#3f3f46] resize-none mono transition-colors duration-200 ${
                    "border-b-[#27272a] focus:border-b-[#22d3ee]"
                  }`}
                  style={{ boxShadow: "none" }}
                />
                <div className="absolute bottom-3 right-0">
                  <VoiceButton onTranscript={(t) => setQuery(t)} />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading || !query.trim()}
                className="flex items-center justify-center gap-2 px-4 py-2.5 bg-[#22d3ee] text-[#09090b] font-semibold text-sm rounded-[6px] hover:bg-[#67e8f9] disabled:opacity-40 disabled:cursor-not-allowed transition-colors cursor-pointer"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    Analysing…
                  </>
                ) : (
                  <>
                    <Send className="h-3.5 w-3.5" />
                    Run Diagnostic
                  </>
                )}
              </button>
            </form>

            {/* Quick queries */}
            <div className="border-t border-[#1c1c1e] pt-4">
              <p className="text-[10px] font-semibold tracking-[.1em] text-[#52525b] uppercase mb-2.5">
                Quick Queries
              </p>
              <div className="flex flex-col gap-1.5">
                {QUICK_QUERIES.map(({ label, query: q }) => (
                  <button
                    key={label}
                    onClick={() => setQuery(q)}
                    className="flex items-center gap-2 w-full text-left px-3 py-2 rounded-[6px] bg-[#18181b] border border-[#27272a] text-[12px] text-[#71717a] hover:text-[#fafafa] hover:border-[#3f3f46] transition-colors cursor-pointer"
                  >
                    <ChevronRight className="h-3 w-3 shrink-0 text-[#3f3f46]" />
                    {label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Agent log (compact) */}
          {result?.agent_log && result.agent_log.length > 0 && (
            <div className="card p-4 flex flex-col gap-3 animate-slide-up">
              <p className="text-[10px] font-semibold tracking-[.15em] text-[#52525b] uppercase">
                Agent Log
              </p>
              <div className="h-32 overflow-y-auto flex flex-col gap-1 mono text-[10px]">
                {result.agent_log.map((log, i) => (
                  <div key={i} className="flex gap-2 leading-snug">
                    <span className="text-[#3f3f46] shrink-0">{log.timestamp}</span>
                    <span
                      className={`font-bold shrink-0 ${
                        log.level === "WARNING"
                          ? "text-amber-400"
                          : log.level === "ERROR"
                          ? "text-rose-400"
                          : "text-[#22d3ee]"
                      }`}
                    >
                      {log.level}
                    </span>
                    <span className="text-[#71717a]">{log.message}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* ════════════════════════════════════════════ */}
        {/*  RIGHT — Results Panel                       */}
        {/* ════════════════════════════════════════════ */}
        <div className="flex flex-col gap-4" ref={resultsRef}>

          {/* ── Empty state ───────────────────────── */}
          {!result && !loading && (
            <div className="card flex-1 flex flex-col items-center justify-center text-center py-16 gap-4">
              <div className="h-12 w-12 rounded-full border border-[#27272a] flex items-center justify-center mb-2">
                <Activity className="h-5 w-5 text-[#3f3f46]" />
              </div>
              <p className="text-sm font-medium text-[#3f3f46]">
                Run a diagnostic query
              </p>
              <p className="text-[12px] text-[#27272a] max-w-xs">
                Enter a maintenance question on the left and hit Run Diagnostic to start multi-agent analysis.
              </p>
            </div>
          )}

          {/* ── Loading state ─────────────────────── */}
          {loading && (
            <div className="card flex-1 flex flex-col items-center justify-center text-center py-16 gap-6">
              {/* Animated dots */}
              <div className="flex gap-1.5">
                {[0, 1, 2].map((i) => (
                  <span
                    key={i}
                    className="h-2 w-2 rounded-full bg-[#22d3ee]"
                    style={{
                      animation: `pulse 1.2s ease-in-out ${i * 0.2}s infinite`,
                    }}
                  />
                ))}
              </div>
              <div>
                <p className="text-sm font-medium text-[#fafafa] mb-1 animate-fade-in" key={phaseIdx}>
                  {LOAD_PHASES[phaseIdx]}
                </p>
                <p className="text-[12px] text-[#52525b]">
                  Multi-agent pipeline running…
                </p>
              </div>
            </div>
          )}

          {/* ── Results ───────────────────────────── */}
          {result && (
            <div className="flex flex-col gap-4 animate-slide-up">

              {/* Agent pipeline strip */}
              <div className="card px-5 py-3 flex items-center gap-2 overflow-x-auto">
                {PIPELINE_STEPS.map((step, i) => {
                  const Icon = step.icon;
                  return (
                    <React.Fragment key={step.id}>
                      <div
                        className={`flex items-center gap-1.5 shrink-0 ${
                          pipelineDone ? "text-[#22d3ee]" : "text-[#3f3f46]"
                        }`}
                      >
                        <div
                          className={`h-6 w-6 rounded-full flex items-center justify-center ${
                            pipelineDone
                              ? "bg-[#22d3ee]/10 border border-[#22d3ee]/30"
                              : "bg-[#18181b] border border-[#27272a]"
                          }`}
                        >
                          <Icon className="h-3 w-3" />
                        </div>
                        <span className="text-[11px] font-medium">{step.label}</span>
                        {pipelineDone && (
                          <CheckCircle2 className="h-3 w-3 text-[#22d3ee]" />
                        )}
                      </div>
                      {i < PIPELINE_STEPS.length - 1 && (
                        <ChevronRight className="h-4 w-4 text-[#3f3f46] shrink-0" />
                      )}
                    </React.Fragment>
                  );
                })}
              </div>

              {/* Physics metrics */}
              {result.physics_result && (
                <div className="card px-5 py-4">
                  <p className="text-[10px] font-semibold tracking-[.15em] text-[#52525b] uppercase mb-3">
                    Physics Analysis
                  </p>
                  <div className="grid grid-cols-3 gap-4 divide-x divide-[#27272a]">
                    <div className="pr-4">
                      <p className="text-[10px] text-[#52525b] uppercase tracking-wider mb-1">
                        Fault Type
                      </p>
                      <p className="text-sm font-semibold text-[#fafafa] mono">
                        {result.physics_result.fault_type}
                      </p>
                    </div>
                    <div className="px-4">
                      <p className="text-[10px] text-[#52525b] uppercase tracking-wider mb-1">
                        Severity
                      </p>
                      <p className={`text-sm font-semibold mono ${severityClass(result.physics_result.severity)}`}>
                        {result.physics_result.severity}
                      </p>
                    </div>
                    <div className="pl-4">
                      <p className="text-[10px] text-[#52525b] uppercase tracking-wider mb-1">
                        Recommendation
                      </p>
                      <p className="text-[12px] text-[#a1a1aa] leading-snug">
                        {result.physics_result.recommendation}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Answer card */}
              {(!result.conflict_detected || conflictResolution) &&
                result.final_answer && (
                  <div className="card px-5 py-4">
                    <div className="flex items-center justify-between mb-3">
                      <p className="text-[10px] font-semibold tracking-[.15em] text-[#52525b] uppercase">
                        Synthesised Answer
                      </p>
                      <button
                        onClick={() => window.print()}
                        className="flex items-center gap-1.5 px-2.5 py-1 rounded-[4px] border border-[#27272a] text-[10px] text-[#52525b] hover:text-[#fafafa] hover:border-[#3f3f46] transition-colors cursor-pointer"
                      >
                        <FileText className="h-3 w-3" />
                        Export PDF
                      </button>
                    </div>
                    <p className="text-[13px] text-[#a1a1aa] leading-relaxed whitespace-pre-wrap mono">
                      {result.final_answer}
                    </p>
                  </div>
                )}

              {/* Multi-agent debate */}
              {result.debate && (
                <div className="card px-5 py-4">
                  <p className="text-[10px] font-semibold tracking-[.15em] text-[#52525b] uppercase mb-3">
                    Agent Debate
                  </p>
                  <div className="grid grid-cols-2 gap-3">
                    {DEBATE_AGENTS.map((agent) => {
                      const value = result.debate![agent.key];
                      if (!value) return null;
                      return (
                        <div
                          key={agent.key}
                          className={`border-l-2 pl-3 py-2 pr-3 rounded-r-[6px] ${agent.border} ${agent.bg}`}
                        >
                          <div className="flex items-center gap-2 mb-1.5">
                            <div
                              className={`h-5 w-5 rounded-full flex items-center justify-center text-[9px] font-black ${agent.bg} border border-current ${agent.text}`}
                            >
                              {agent.letter}
                            </div>
                            <div>
                              <p className={`text-[11px] font-semibold ${agent.text}`}>
                                {agent.label}
                              </p>
                              <p className="text-[9px] text-[#52525b]">{agent.sub}</p>
                            </div>
                          </div>
                          <p className="text-[11px] text-[#71717a] italic leading-snug">
                            &ldquo;{value}&rdquo;
                          </p>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Conflict panel */}
              {result.conflict_detected &&
                !conflictResolution &&
                result.conflict_details && (
                  <div className="card border-amber-500/30 px-5 py-4 flex flex-col gap-4 animate-slide-up">
                    <div className="flex items-center gap-2">
                      <AlertTriangle className="h-4 w-4 text-amber-400 shrink-0" />
                      <div>
                        <p className="text-sm font-semibold text-[#fafafa]">
                          Conflict Detected
                        </p>
                        <p className="text-[11px] text-amber-400/80">
                          SOP documentation contradicts live physics data
                        </p>
                      </div>
                    </div>

                    {result.auto_resolution_recommendation && (
                      <div className="rounded-[6px] border border-[#22d3ee]/20 bg-[#22d3ee]/5 px-4 py-3">
                        <p className="text-[10px] font-semibold tracking-widest text-[#22d3ee] uppercase mb-1">
                          AI Recommendation
                        </p>
                        <p className="text-[12px] text-[#a1a1aa]">
                          Trust{" "}
                          <span className="text-[#fafafa] font-semibold">
                            {result.auto_resolution_recommendation.winner.toUpperCase()}
                          </span>
                          :{" "}
                          <em>{result.auto_resolution_recommendation.reason}</em>
                        </p>
                      </div>
                    )}

                    <div className="grid grid-cols-2 gap-3">
                      <div className="rounded-[6px] border border-[#27272a] bg-[#09090b] px-4 py-3">
                        <p className="text-[10px] font-semibold text-sky-400 uppercase tracking-wider mb-2">
                          SOP Documentation
                        </p>
                        <p className="text-[12px] text-[#a1a1aa] leading-snug mb-3">
                          {result.conflict_details.document_hypothesis}
                        </p>
                        <p className="text-[10px] text-[#52525b] mono">
                          Confidence{" "}
                          {(result.conflict_details.document_confidence * 100).toFixed(0)}%
                        </p>
                      </div>
                      <div className="rounded-[6px] border border-[#27272a] bg-[#09090b] px-4 py-3">
                        <p className="text-[10px] font-semibold text-[#22d3ee] uppercase tracking-wider mb-2">
                          Live Physics
                        </p>
                        <p className="text-[12px] text-[#a1a1aa] leading-snug mb-3">
                          {result.conflict_details.physics_result}
                        </p>
                        <p className="text-[10px] text-[#52525b] mono">
                          Confidence{" "}
                          {(result.conflict_details.physics_confidence * 100).toFixed(0)}%
                        </p>
                      </div>
                    </div>

                    {/* Resolution buttons */}
                    <div className="flex items-center gap-2 pt-1">
                      <button
                        onClick={() => handleResolve("physics")}
                        disabled={resolving}
                        className="flex-1 flex items-center justify-center gap-1.5 py-2 px-3 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-[12px] font-semibold rounded-[6px] hover:bg-emerald-500/20 disabled:opacity-50 cursor-pointer transition-colors"
                      >
                        <Zap className="h-3.5 w-3.5" />
                        Trust Physics
                      </button>
                      <button
                        onClick={() => handleResolve("documents")}
                        disabled={resolving}
                        className="flex-1 flex items-center justify-center gap-1.5 py-2 px-3 bg-[#18181b] border border-[#27272a] text-[#a1a1aa] text-[12px] font-semibold rounded-[6px] hover:border-[#3f3f46] hover:text-[#fafafa] disabled:opacity-50 cursor-pointer transition-colors"
                      >
                        <BookOpen className="h-3.5 w-3.5" />
                        Trust SOP
                      </button>
                      <button
                        onClick={() => setShowInterview(true)}
                        disabled={resolving}
                        className="flex-1 flex items-center justify-center gap-1.5 py-2 px-3 bg-[#22d3ee]/5 border border-[#22d3ee]/20 text-[#22d3ee] text-[12px] font-semibold rounded-[6px] hover:bg-[#22d3ee]/10 disabled:opacity-50 cursor-pointer transition-colors"
                      >
                        <Mic className="h-3.5 w-3.5" />
                        Ask Engineer
                      </button>
                    </div>

                    {/* Interview panel */}
                    {showInterview && (
                      <div className="border-t border-[#27272a] pt-4 flex flex-col gap-3 animate-slide-up">
                        {result.human_question && (
                          <div className="rounded-[6px] border border-amber-500/20 bg-amber-500/5 px-4 py-3">
                            <p className="text-[12px] text-amber-400/90 mono italic">
                              {result.human_question}
                            </p>
                          </div>
                        )}
                        <textarea
                          value={humanResponse}
                          onChange={(e) => setHumanResponse(e.target.value)}
                          rows={3}
                          placeholder="Enter tacit knowledge or engineer workaround details…"
                          className="w-full bg-[#09090b] border border-[#27272a] rounded-[4px] px-3 py-2 text-[12px] text-[#fafafa] placeholder-[#3f3f46] mono resize-none focus:border-[#22d3ee] transition-colors"
                        />
                        <div className="flex gap-2 justify-end">
                          <button
                            onClick={() => handleResolve("human")}
                            disabled={resolving || !humanResponse.trim()}
                            className="px-4 py-1.5 bg-[#22d3ee] text-[#09090b] font-semibold text-[12px] rounded-[6px] hover:bg-[#67e8f9] disabled:opacity-40 cursor-pointer transition-colors"
                          >
                            Submit Rule
                          </button>
                          <button
                            onClick={() => setShowInterview(false)}
                            className="px-4 py-1.5 bg-[#18181b] border border-[#27272a] text-[#71717a] text-[12px] rounded-[6px] hover:text-[#fafafa] cursor-pointer transition-colors"
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                )}

              {/* Resolved conflict */}
              {conflictResolution && (
                <div className="card px-5 py-3 flex items-start gap-3 animate-fade-in">
                  <CheckCircle2 className="h-4 w-4 text-[#22d3ee] shrink-0 mt-0.5" />
                  <div>
                    <p className="text-[12px] font-semibold text-[#fafafa]">
                      Conflict resolved —{" "}
                      <span className="text-[#22d3ee]">
                        {conflictResolution.toUpperCase()}
                      </span>{" "}
                      wins
                    </p>
                    {conflictResolution === "human" &&
                      resolutionDetails?.structured_rule && (
                        <div className="mt-2 rounded-[6px] border border-emerald-500/20 bg-emerald-500/5 px-3 py-2">
                          <p className="text-[10px] font-semibold text-emerald-400 uppercase tracking-wider mb-1">
                            Tacit Rule Captured
                          </p>
                          <p className="text-[11px] text-emerald-300 mono italic">
                            &ldquo;{resolutionDetails.structured_rule.rule_text}&rdquo;
                          </p>
                        </div>
                      )}
                    {resolutionDetails?.healed_nodes && (
                      <p className="text-[11px] text-[#71717a] mt-1.5">
                        Knowledge graph self-healing applied. View changes on the{" "}
                        <strong className="text-[#fafafa]">Graph</strong> page.
                      </p>
                    )}
                  </div>
                </div>
              )}

              {/* Work order notice */}
              {result.work_order && (
                <div className="flex items-center gap-3 px-4 py-3 rounded-[6px] border border-[#27272a] bg-[#18181b] text-[12px] text-[#71717a]">
                  <Cpu className="h-3.5 w-3.5 text-[#52525b] shrink-0" />
                  A maintenance work order was auto-generated. View it on the{" "}
                  <strong className="text-[#fafafa] ml-1">Maintenance</strong>{" "}
                  page.
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
