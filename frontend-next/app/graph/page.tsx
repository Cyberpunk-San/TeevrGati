"use client";

import React, { useState, useEffect, useRef } from "react";
import { gsap } from "gsap";
import { Layers, RefreshCw, Cpu } from "lucide-react";

interface GraphNode {
  id: string;
  label: string;
  type: string;
  metadata?: {
    status?: string;
    [key: string]: any;
  };
}

interface GraphEdge {
  from: string;
  to: string;
  label?: string;
  metadata?: any;
}

export default function GraphPage() {
  const [graphData, setGraphData] = useState<{ nodes: GraphNode[]; edges: GraphEdge[] }>({ nodes: [], edges: [] });
  const [loading, setLoading] = useState(false);
  const [activeNode, setActiveNode] = useState<GraphNode | null>(null);
  const graphContainerRef = useRef<HTMLDivElement>(null);

  const fetchGraph = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/api/graph", {
        headers: { "Authorization": "Bearer dev-key" }
      });
      if (res.ok) {
        const data = await res.json();
        setGraphData(data);
        
        // Trigger page entrance animation
        if (graphContainerRef.current) {
          gsap.fromTo(
            graphContainerRef.current,
            { opacity: 0, scale: 0.98 },
            { opacity: 1, scale: 1, duration: 0.6, ease: "power3.out" }
          );
        }
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGraph();
  }, []);

  const getGraphPositions = (nodes: GraphNode[]) => {
    const positions: { [key: string]: { x: number; y: number } } = {};
    
    // Group nodes dynamically by lowercase class type
    const procedures = nodes.filter(n => n.type.toLowerCase() === 'procedure');
    const equipments = nodes.filter(n => n.type.toLowerCase() === 'equipment');
    const components = nodes.filter(n => n.type.toLowerCase() === 'component');
    const incidents = nodes.filter(n => n.type.toLowerCase() === 'incident');
    const tacitRules = nodes.filter(n => n.type.toLowerCase() === 'tacitrule');
    const others = nodes.filter(n => !['procedure', 'equipment', 'component', 'incident', 'tacitrule'].includes(n.type.toLowerCase()));

    // Define column X boundaries for structured layout flow
    const colProceduresX = 100;
    const colEquipmentsX = 290;
    const colComponentsX = 490;
    const colRightX = 690;
    
    const svgHeight = 440;
    
    // Position helper
    const positionColumn = (items: GraphNode[], x: number) => {
      const count = items.length;
      items.forEach((item, idx) => {
        const y = count > 1 
          ? 50 + (idx / (count - 1)) * (svgHeight - 100)
          : svgHeight / 2;
        positions[item.id] = { x, y };
      });
    };
    
    positionColumn(procedures, colProceduresX);
    positionColumn(equipments, colEquipmentsX);
    positionColumn(components, colComponentsX);
    
    // Incidents at the top-right
    const countIncidents = incidents.length;
    incidents.forEach((item, idx) => {
      const y = countIncidents > 1
        ? 50 + (idx / (countIncidents - 1)) * 140
        : 100;
      positions[item.id] = { x: colRightX, y };
    });
    
    // Tacit Rules at the bottom-right
    const countTacits = tacitRules.length;
    tacitRules.forEach((item, idx) => {
      const y = countTacits > 1
        ? 280 + (idx / (countTacits - 1)) * 140
        : 350;
      positions[item.id] = { x: colRightX, y };
    });
    
    // Others
    others.forEach((item, idx) => {
      positions[item.id] = { x: colRightX, y: 220 };
    });
    
    return positions;
  };

  const nodePositions = getGraphPositions(graphData.nodes);

  return (
    <div className="flex-1 flex flex-col p-6 gap-6">
      
      {/* Page Header */}
      <div className="flex justify-between items-center bg-[#0d1527] border border-[#1e293b] p-6 rounded-xl shadow-lg">
        <div>
          <h2 className="text-xl font-bold text-white tracking-wide">SELF-HEALING ONTOLOGY KNOWLEDGE GRAPH</h2>
          <p className="text-xs text-[#64748b]">Real-time visual map of documents, sensor metrics, and operator overrides</p>
        </div>
        <button
          onClick={fetchGraph}
          disabled={loading}
          className="h-10 px-4 bg-[#1e293b] border border-[#2e374a] rounded-lg text-xs font-bold text-white hover:bg-slate-800 transition-all flex items-center gap-2 cursor-pointer disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          Refresh Ontology
        </button>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
        
        {/* SVG Graph Area (Left 8 columns) */}
        <div className="xl:col-span-8 flex flex-col gap-4 bg-[#111827]/80 border border-[#1e293b] rounded-xl p-5 shadow-xl">
          <div ref={graphContainerRef} className="bg-[#0b0f19] border border-[#1e293b] rounded-lg p-4 flex items-center justify-center min-h-[500px] overflow-auto relative">
            {graphData.nodes.length > 0 ? (
              <svg width="840" height="500" className="max-w-full">
                <defs>
                  <marker id="arrow" viewBox="0 0 10 10" refX="22" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                    <path d="M 0 0 L 10 5 L 0 10 z" fill="#5c677d" />
                  </marker>
                  <marker id="arrow-healed" viewBox="0 0 10 10" refX="22" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
                    <path d="M 0 0 L 10 5 L 0 10 z" fill="#52b788" />
                  </marker>
                </defs>

                {/* Draw edges */}
                {graphData.edges.map((edge, i) => {
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
                        stroke={isHealed ? "#52b788" : "#5c677d"}
                        strokeWidth={isHealed ? "2.5" : "1.2"}
                        strokeDasharray={isHealed ? "6,4" : "0"}
                        markerEnd={`url(#${isHealed ? "arrow-healed" : "arrow"})`}
                      />
                      {isHealed && (
                        <text
                          x={(fromPos.x + toPos.x) / 2}
                          y={(fromPos.y + toPos.y) / 2 - 8}
                          fill="#52b788"
                          fontSize="9"
                          fontWeight="bold"
                          textAnchor="middle"
                        >
                          REPLACED_BY
                        </text>
                      )}
                    </g>
                  );
                })}

                {/* Draw nodes */}
                {graphData.nodes.map((node, i) => {
                  const pos = nodePositions[node.id];
                  if (!pos) return null;
                  
                  const meta = node.metadata || {};
                  const isOutdated = meta.status === 'outdated';
                  const isActive = activeNode?.id === node.id;
                  
                  let color = "#8e9aaf";
                  const typeLower = node.type.toLowerCase();
                  if (isOutdated) {
                    color = "#4a4e69"; // Gray-blue for outdated document
                  } else if (typeLower === "equipment") {
                    color = "#00f5d4"; // Teal for equipment
                  } else if (typeLower === "procedure" || typeLower === "document") {
                    color = "#4cc9f0"; // Sky blue for procedure SOPs
                  } else if (typeLower === "component") {
                    color = "#a855f7"; // Purple for components
                  } else if (typeLower === "incident") {
                    color = "#f77f00"; // Orange for incidents
                  } else if (typeLower === "tacitrule" || typeLower === "tacit_rule") {
                    color = "#52b788"; // Green for verified tacit rule overrides
                  }
                  
                  return (
                    <g 
                      key={i} 
                      className="cursor-pointer"
                      onClick={() => setActiveNode(node)}
                    >
                      <circle
                        cx={pos.x}
                        cy={pos.y}
                        r={node.type === "EQUIPMENT" ? 22 : 17}
                        fill={color}
                        stroke={isActive ? "white" : "#2e374a"}
                        strokeWidth={isActive ? "3" : "2"}
                      />
                      <text
                        x={pos.x}
                        y={pos.y + 32}
                        fill={isOutdated ? "#64748b" : "white"}
                        fontSize="9"
                        fontWeight="bold"
                        textAnchor="middle"
                      >
                        {isOutdated ? `[OUTDATED] ${node.label.split(".")[0]}` : node.label}
                      </text>
                    </g>
                  );
                })}
              </svg>
            ) : (
              <span className="text-xs text-[#64748b]">No active knowledge graph loaded.</span>
            )}
          </div>

          {/* Legend */}
          <div className="flex gap-4 justify-center flex-wrap text-xs border-t border-[#1e293b] pt-4">
            <span className="flex items-center gap-1.5"><span className="h-3 w-3 rounded-full bg-[#00f5d4]"></span> Equipment Node</span>
            <span className="flex items-center gap-1.5"><span className="h-3 w-3 rounded-full bg-[#4cc9f0]"></span> Active SOP Document</span>
            <span className="flex items-center gap-1.5"><span className="h-3 w-3 rounded-full bg-[#a855f7]"></span> Component Node</span>
            <span className="flex items-center gap-1.5"><span className="h-3 w-3 rounded-full bg-[#f77f00]"></span> Incident Node</span>
            <span className="flex items-center gap-1.5"><span className="h-3 w-3 rounded-full bg-[#52b788]"></span> Tacit Rule / Overwrite</span>
            <span className="flex items-center gap-1.5"><span className="h-3 w-3 rounded-full bg-[#4a4e69]"></span> Outdated Document</span>
            <span className="flex items-center gap-1.5"><span className="h-2 w-6 border-t-2 border-dashed border-[#52b788]"></span> Replaced Connection</span>
          </div>
        </div>

        {/* Node Properties Panel (Right 4 columns) */}
        <div className="xl:col-span-4 flex flex-col gap-6">
          <div className="bg-[#111827]/80 border border-[#1e293b] rounded-xl p-5 shadow-xl flex-1">
            <h3 className="text-xs font-bold text-[#00f5d4] uppercase tracking-wider mb-4 flex items-center gap-2">
              <Cpu className="h-4 w-4 text-[#00f5d4]" />
              Metadata Inspector
            </h3>

            {activeNode ? (
              <div className="flex flex-col gap-4 text-xs">
                <div>
                  <span className="text-[#64748b] text-[10px] block uppercase">Node ID</span>
                  <span className="text-white font-mono font-semibold block bg-[#0d1527] p-2 rounded border border-[#1e293b]">{activeNode.id}</span>
                </div>
                <div>
                  <span className="text-[#64748b] text-[10px] block uppercase">Ontology Class</span>
                  <span className="text-[#00f5d4] font-bold">{activeNode.type}</span>
                </div>
                <div>
                  <span className="text-[#64748b] text-[10px] block uppercase">Label</span>
                  <span className="text-white font-bold">{activeNode.label}</span>
                </div>

                {activeNode.metadata && (
                  <div className="border-t border-[#1e293b] pt-4 mt-2">
                    <span className="text-[#64748b] text-[10px] block uppercase mb-2">Properties Summary</span>
                    <div className="flex flex-col gap-2 max-h-48 overflow-y-auto bg-[#0d1527]/50 p-3 rounded border border-[#1e293b] font-mono text-[10px] text-slate-300">
                      {Object.entries(activeNode.metadata).map(([key, val]) => (
                        <div key={key} className="flex justify-between border-b border-[#1e293b]/50 pb-1">
                          <span className="text-[#64748b]">{key}:</span>
                          <span className="text-white">{String(val)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center text-center h-48 border border-dashed border-[#2e374a] rounded-lg p-6">
                <span className="text-xs text-[#64748b]">Click any graph node to inspect metadata parameters</span>
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
