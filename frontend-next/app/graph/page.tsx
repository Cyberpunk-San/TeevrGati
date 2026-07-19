"use client";

import React, { useState, useEffect, useMemo, useRef } from "react";
import { gsap } from "gsap";
import { RefreshCw, Cpu, AlertTriangle } from "lucide-react";
import { apiGet, ApiError } from "../lib/apiClient";

interface GraphNode {
  id: string;
  label: string;
  type: string;
  metadata?: {
    status?: string;
    [key: string]: unknown;
  };
}

interface GraphEdge {
  from: string;
  to: string;
  label?: string;
  metadata?: unknown;
}

const TYPE_COLOR: Record<string, string> = {
  equipment: "#22d3ee",
  procedure: "#38bdf8",
  document: "#38bdf8",
  component: "#c084fc",
  incident: "#fb923c",
  tacitrule: "#34d399",
  tacit_rule: "#34d399",
  outdated: "#52525b",
};

const MAX_NODES = 36;
const SVG_W = 920;
const SVG_H = 560;

function normalizeType(t: string) {
  return (t || "").toLowerCase().replace(/\s+/g, "");
}

/** Prefer plant-relevant nodes so the canvas stays readable. */
function selectFocusNodes(nodes: GraphNode[], edges: GraphEdge[]): GraphNode[] {
  if (nodes.length <= MAX_NODES) return nodes;

  const score = (n: GraphNode) => {
    const t = normalizeType(n.type);
    const label = (n.label || n.id || "").toLowerCase();
    let s = 0;
    if (t === "equipment") s += 50;
    if (t === "procedure" || t === "document") s += 30;
    if (t === "incident") s += 25;
    if (t === "tacitrule" || t === "tacit_rule") s += 28;
    if (t === "component") s += 15;
    if (label.includes("p-201") || label.includes("p201")) s += 40;
    if (label.includes("c-101") || label.includes("c101")) s += 20;
    if (n.metadata?.status === "outdated") s += 12;
    return s;
  };

  const ranked = [...nodes].sort((a, b) => score(b) - score(a));
  const seed = ranked.slice(0, Math.min(18, ranked.length));
  const seedIds = new Set(seed.map((n) => n.id));

  // Expand one hop from seeds via edges
  for (const e of edges) {
    if (seedIds.has(e.from) || seedIds.has(e.to)) {
      seedIds.add(e.from);
      seedIds.add(e.to);
    }
    if (seedIds.size >= MAX_NODES) break;
  }

  const byId = new Map(nodes.map((n) => [n.id, n]));
  const selected = [...seedIds].map((id) => byId.get(id)).filter(Boolean) as GraphNode[];
  return selected.slice(0, MAX_NODES);
}

function layoutNodes(nodes: GraphNode[]) {
  const positions: Record<string, { x: number; y: number }> = {};
  const buckets: Record<string, GraphNode[]> = {
    procedure: [],
    equipment: [],
    component: [],
    right: [],
  };

  for (const n of nodes) {
    const t = normalizeType(n.type);
    if (t === "procedure" || t === "document") buckets.procedure.push(n);
    else if (t === "equipment") buckets.equipment.push(n);
    else if (t === "component") buckets.component.push(n);
    else buckets.right.push(n);
  }

  const placeColumn = (items: GraphNode[], x: number) => {
    const n = items.length;
    if (!n) return;
    const top = 64;
    const bottom = SVG_H - 64;
    items.forEach((item, idx) => {
      const y = n === 1 ? SVG_H / 2 : top + (idx / (n - 1)) * (bottom - top);
      positions[item.id] = { x, y };
    });
  };

  placeColumn(buckets.procedure, 110);
  placeColumn(buckets.equipment, 320);
  placeColumn(buckets.component, 530);
  placeColumn(buckets.right, 760);

  return positions;
}

export default function GraphPage() {
  const [graphData, setGraphData] = useState<{ nodes: GraphNode[]; edges: GraphEdge[] }>({ nodes: [], edges: [] });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeNode, setActiveNode] = useState<GraphNode | null>(null);
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const graphContainerRef = useRef<HTMLDivElement>(null);

  const fetchGraph = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiGet<{ nodes: GraphNode[]; edges: GraphEdge[] }>("/api/graph");
      setGraphData(data);
      if (graphContainerRef.current) {
        gsap.fromTo(
          graphContainerRef.current,
          { opacity: 0, y: 8 },
          { opacity: 1, y: 0, duration: 0.45, ease: "power2.out" }
        );
      }
    } catch (err) {
      const msg = err instanceof ApiError ? err.detail : "Failed to load knowledge graph.";
      setError(msg);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGraph();
  }, []);

  const focusNodes = useMemo(
    () => selectFocusNodes(graphData.nodes, graphData.edges),
    [graphData.nodes, graphData.edges]
  );
  const focusIds = useMemo(() => new Set(focusNodes.map((n) => n.id)), [focusNodes]);
  const focusEdges = useMemo(
    () => graphData.edges.filter((e) => focusIds.has(e.from) && focusIds.has(e.to)).slice(0, 80),
    [graphData.edges, focusIds]
  );
  const nodePositions = useMemo(() => layoutNodes(focusNodes), [focusNodes]);

  const shortLabel = (label: string) => {
    const base = label.split(".")[0];
    return base.length > 22 ? `${base.slice(0, 20)}…` : base;
  };

  return (
    <div className="page-shell">
      <div className="page-header">
        <div>
          <div className="label">Knowledge graph</div>
          <h1 className="page-title" style={{ marginTop: 8 }}>Self-healing ontology</h1>
          <p className="page-subtitle">
            Focused view of equipment, SOPs, incidents, and tacit overrides. Showing{" "}
            {focusNodes.length} of {graphData.nodes.length || 0} nodes for readability.
          </p>
        </div>
        <button className="btn btn-ghost" onClick={fetchGraph} disabled={loading}>
          <RefreshCw size={14} style={loading ? { animation: "spin 1s linear infinite" } : undefined} />
          Refresh
        </button>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "minmax(0, 1fr) 300px", gap: 28, alignItems: "start" }}>
        <div className="card" style={{ padding: 24 }}>
          <div
            ref={graphContainerRef}
            style={{
              background: "var(--bg-base)",
              border: "1px solid var(--border-dim)",
              borderRadius: "var(--r-md)",
              minHeight: 580,
              overflow: "auto",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              padding: 16,
            }}
          >
            {focusNodes.length > 0 ? (
              <svg width={SVG_W} height={SVG_H} style={{ maxWidth: "100%" }}>
                <defs>
                  <marker id="arrow" viewBox="0 0 10 10" refX="20" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
                    <path d="M 0 0 L 10 5 L 0 10 z" fill="#3f3f46" />
                  </marker>
                  <marker id="arrow-healed" viewBox="0 0 10 10" refX="20" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
                    <path d="M 0 0 L 10 5 L 0 10 z" fill="#34d399" />
                  </marker>
                </defs>

                {focusEdges.map((edge, i) => {
                  const fromPos = nodePositions[edge.from];
                  const toPos = nodePositions[edge.to];
                  if (!fromPos || !toPos) return null;
                  const isHealed = edge.label === "REPLACED_BY";
                  return (
                    <g key={i}>
                      <line
                        x1={fromPos.x}
                        y1={fromPos.y}
                        x2={toPos.x}
                        y2={toPos.y}
                        stroke={isHealed ? "#34d399" : "#27272a"}
                        strokeWidth={isHealed ? 2 : 1}
                        strokeDasharray={isHealed ? "5 4" : "0"}
                        markerEnd={`url(#${isHealed ? "arrow-healed" : "arrow"})`}
                        opacity={0.85}
                      />
                      {isHealed && (
                        <text
                          x={(fromPos.x + toPos.x) / 2}
                          y={(fromPos.y + toPos.y) / 2 - 10}
                          fill="#34d399"
                          fontSize="10"
                          textAnchor="middle"
                          opacity={0.9}
                        >
                          REPLACED_BY
                        </text>
                      )}
                    </g>
                  );
                })}

                {focusNodes.map((node) => {
                  const pos = nodePositions[node.id];
                  if (!pos) return null;
                  const t = normalizeType(node.type);
                  const isOutdated = node.metadata?.status === "outdated";
                  const isActive = activeNode?.id === node.id;
                  const isHovered = hoveredId === node.id;
                  const showLabel =
                    isActive ||
                    isHovered ||
                    t === "equipment" ||
                    t === "tacitrule" ||
                    t === "tacit_rule";
                  const color = isOutdated ? TYPE_COLOR.outdated : TYPE_COLOR[t] || "#71717a";
                  const r = t === "equipment" ? 16 : 11;

                  return (
                    <g
                      key={node.id}
                      style={{ cursor: "pointer" }}
                      onClick={() => setActiveNode(node)}
                      onMouseEnter={() => setHoveredId(node.id)}
                      onMouseLeave={() => setHoveredId(null)}
                    >
                      {(isActive || isHovered) && (
                        <circle cx={pos.x} cy={pos.y} r={r + 6} fill="none" stroke={color} strokeWidth={1} opacity={0.35} />
                      )}
                      <circle
                        cx={pos.x}
                        cy={pos.y}
                        r={r}
                        fill={color}
                        fillOpacity={isOutdated ? 0.45 : 0.9}
                        stroke={isActive ? "#fafafa" : "var(--bg-base)"}
                        strokeWidth={isActive ? 2.5 : 1.5}
                      />
                      {showLabel && (
                        <text
                          x={pos.x}
                          y={pos.y + r + 16}
                          fill={isOutdated ? "#71717a" : "#e4e4e7"}
                          fontSize="11"
                          fontWeight={t === "equipment" ? 600 : 450}
                          textAnchor="middle"
                        >
                          {isOutdated ? `↻ ${shortLabel(node.label)}` : shortLabel(node.label)}
                        </text>
                      )}
                    </g>
                  );
                })}
              </svg>
            ) : (
              <span style={{ fontSize: 13, color: "var(--text-muted)" }}>
                {loading ? "Loading graph…" : "No knowledge graph loaded."}
              </span>
            )}
          </div>

          <div style={{
            display: "flex",
            flexWrap: "wrap",
            gap: 18,
            justifyContent: "center",
            marginTop: 22,
            paddingTop: 20,
            borderTop: "1px solid var(--border-dim)",
          }}>
            {[
              ["#22d3ee", "Equipment"],
              ["#38bdf8", "SOP / document"],
              ["#c084fc", "Component"],
              ["#fb923c", "Incident"],
              ["#34d399", "Tacit rule"],
              ["#52525b", "Outdated"],
            ].map(([c, label]) => (
              <span key={label} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12, color: "var(--text-secondary)" }}>
                <span style={{ width: 8, height: 8, borderRadius: "50%", background: c }} />
                {label}
              </span>
            ))}
          </div>
        </div>

        <div className="card card-pad" style={{ minHeight: 420 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 24 }}>
            <Cpu size={15} color="var(--accent)" />
            <span className="label" style={{ color: "var(--accent)" }}>Inspector</span>
          </div>

          {activeNode ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
              <div>
                <div className="label" style={{ marginBottom: 8 }}>Node ID</div>
                <div style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: 12,
                  padding: "12px 14px",
                  background: "var(--bg-base)",
                  border: "1px solid var(--border)",
                  borderRadius: "var(--r-sm)",
                  wordBreak: "break-all",
                  lineHeight: 1.5,
                }}>
                  {activeNode.id}
                </div>
              </div>
              <div>
                <div className="label" style={{ marginBottom: 8 }}>Class</div>
                <div style={{ fontSize: 14, color: "var(--accent)", fontWeight: 560 }}>{activeNode.type}</div>
              </div>
              <div>
                <div className="label" style={{ marginBottom: 8 }}>Label</div>
                <div style={{ fontSize: 14, lineHeight: 1.5 }}>{activeNode.label}</div>
              </div>
              {activeNode.metadata && Object.keys(activeNode.metadata).length > 0 && (
                <div style={{ borderTop: "1px solid var(--border-dim)", paddingTop: 20 }}>
                  <div className="label" style={{ marginBottom: 12 }}>Properties</div>
                  <div style={{ display: "flex", flexDirection: "column", gap: 12, maxHeight: 240, overflowY: "auto" }}>
                    {Object.entries(activeNode.metadata).map(([key, val]) => (
                      <div key={key} style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                        <span style={{ fontSize: 11, color: "var(--text-muted)" }}>{key}</span>
                        <span style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.45, wordBreak: "break-word" }}>
                          {String(val)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div style={{
              border: "1px dashed var(--border)",
              borderRadius: "var(--r-md)",
              padding: 32,
              textAlign: "center",
              color: "var(--text-muted)",
              fontSize: 13,
              lineHeight: 1.6,
            }}>
              Select a node to inspect ontology metadata.
              <div style={{ marginTop: 10, fontSize: 12, opacity: 0.8 }}>
                Hover any node to reveal its label.
              </div>
            </div>
          )}
        </div>
      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
