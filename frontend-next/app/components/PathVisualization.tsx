'use client';
import React from 'react';
import { ArrowRight, Layers } from 'lucide-react';

interface TraversalStep {
  from: string;
  to: string;
  relation: string;
}

export function PathVisualization({ paths }: { paths: TraversalStep[] }) {
  if (!paths || paths.length === 0) return null;

  const nodes: { label: string; type: string }[] = [];
  
  paths.forEach((step, idx) => {
    const fromLabel = step.from.replace('EQ_', '').replace('DOC_', '').replace('PHYS_', '').replace('PERSON_', '');
    const toLabel = step.to.replace('EQ_', '').replace('DOC_', '').replace('PHYS_', '').replace('PERSON_', '');
    
    let fromType = 'UNKNOWN';
    if (step.from.startsWith('EQ_')) fromType = 'EQUIPMENT';
    else if (step.from.startsWith('doc_') || step.from.startsWith('DOC_')) fromType = 'DOCUMENT';
    else if (step.from.startsWith('PERSON_')) fromType = 'PERSON';
    else if (step.from.startsWith('TACIT_')) fromType = 'TACIT_RULE';

    let toType = 'UNKNOWN';
    if (step.to.startsWith('EQ_')) toType = 'EQUIPMENT';
    else if (step.to.startsWith('doc_') || step.to.startsWith('DOC_')) toType = 'DOCUMENT';
    else if (step.to.startsWith('PERSON_')) toType = 'PERSON';
    else if (step.to.startsWith('TACIT_')) toType = 'TACIT_RULE';

    if (idx === 0) {
      nodes.push({ label: fromLabel, type: fromType });
    }
    nodes.push({ label: toLabel, type: toType });
  });

  const getColor = (type: string) => {
    switch (type) {
      case 'EQUIPMENT':
        return 'bg-[#00f5d4]/10 border-[#00f5d4]/20 text-[#00f5d4]';
      case 'DOCUMENT':
        return 'bg-[#4cc9f0]/10 border-[#4cc9f0]/20 text-[#4cc9f0]';
      case 'TACIT_RULE':
        return 'bg-emerald-950/15 border-emerald-900/30 text-emerald-400';
      case 'PERSON':
        return 'bg-pink-950/15 border-pink-900/30 text-pink-400';
      default:
        return 'bg-slate-900 border-[#2e374a] text-slate-400';
    }
  };

  return (
    <div className="bg-[#0b0f19] border border-[#1e293b] rounded-xl p-4 flex flex-col gap-3 shadow-inner">
      <h4 className="text-[10px] font-bold text-[#64748b] uppercase tracking-wider flex items-center gap-1.5">
        <Layers className="h-3.5 w-3.5" />
        Semantic Traversed Path (Multi-Hop Proof)
      </h4>

      <div className="flex items-center gap-2 overflow-x-auto py-1 scrollbar-none flex-wrap">
        {nodes.map((node, i) => (
          <React.Fragment key={i}>
            <div className={`px-2.5 py-1.5 rounded-lg border text-xs font-semibold font-mono ${getColor(node.type)}`}>
              <span className="text-[9px] block text-[#64748b] leading-none uppercase mb-0.5">{node.type}</span>
              {node.label.split('.')[0]}
            </div>
            {i < nodes.length - 1 && (
              <ArrowRight className="h-4 w-4 text-[#475569] flex-shrink-0" />
            )}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
}
