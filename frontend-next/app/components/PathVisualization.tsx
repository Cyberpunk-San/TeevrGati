"use client";
import React from "react";
import { ArrowRight, GitBranch } from "lucide-react";

interface TraversalStep {
  from: string;
  to: string;
  relation: string;
}

const clean = (s: string) =>
  s.replace("EQ_", "").replace("DOC_", "").replace("PHYS_", "").replace("PERSON_", "");

const typeOf = (s: string) => {
  if (s.startsWith("EQ_"))            return "EQUIPMENT";
  if (s.startsWith("doc_") || s.startsWith("DOC_")) return "DOCUMENT";
  if (s.startsWith("PERSON_"))        return "PERSON";
  if (s.startsWith("TACIT_"))         return "TACIT";
  return "NODE";
};

const nodeStyle: Record<string, string> = {
  EQUIPMENT: "border-[#22d3ee]/30 bg-[#22d3ee]/5 text-[#22d3ee]",
  DOCUMENT:  "border-sky-500/30    bg-sky-500/5    text-sky-400",
  PERSON:    "border-violet-500/30 bg-violet-500/5 text-violet-400",
  TACIT:     "border-emerald-500/30 bg-emerald-500/5 text-emerald-400",
  NODE:      "border-[#27272a]     bg-[#18181b]    text-[#71717a]",
};

export function PathVisualization({ paths }: { paths: TraversalStep[] }) {
  if (!paths || paths.length === 0) return null;

  const nodes: { label: string; type: string }[] = [];
  paths.forEach((step, i) => {
    if (i === 0) nodes.push({ label: clean(step.from), type: typeOf(step.from) });
    nodes.push({ label: clean(step.to), type: typeOf(step.to) });
  });

  return (
    <div className="card px-4 py-3 flex flex-col gap-3">
      <div className="flex items-center gap-1.5">
        <GitBranch className="h-3 w-3 text-[#52525b]" />
        <p className="text-[10px] font-semibold tracking-[.15em] text-[#52525b] uppercase">
          Knowledge Graph Path
        </p>
      </div>
      <div className="flex items-center gap-1.5 overflow-x-auto py-1 flex-wrap">
        {nodes.map((n, i) => (
          <React.Fragment key={i}>
            <div
              className={`px-2.5 py-1 rounded-[4px] border text-[11px] font-medium mono shrink-0 ${nodeStyle[n.type]}`}
            >
              <span className="block text-[9px] text-[#52525b] uppercase leading-none mb-0.5">
                {n.type}
              </span>
              {n.label.split(".")[0]}
            </div>
            {i < nodes.length - 1 && (
              <ArrowRight className="h-3.5 w-3.5 text-[#3f3f46] shrink-0" />
            )}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
}
