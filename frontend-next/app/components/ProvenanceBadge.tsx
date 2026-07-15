'use client';
import { Clock, ShieldAlert, CheckCircle, ArrowRight } from 'lucide-react';

export function ProvenanceBadge({ document }: { document: any }) {
  const age = document.year ? new Date().getFullYear() - document.year : 3;
  const isOutdated = document.status === 'outdated';
  
  return (
    <div className={`p-3.5 rounded-lg border transition-all duration-300 flex flex-col gap-2 ${
      isOutdated 
        ? 'bg-slate-900/40 border-[#384252]/80 text-[#64748b]' 
        : 'bg-emerald-950/10 border-emerald-900/30 text-emerald-300'
    }`}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className={`text-xs font-bold ${isOutdated ? 'text-slate-500 line-through' : 'text-white'}`}>
            {document.name}
          </span>
          {isOutdated ? (
            <span className="text-[9px] bg-[#384252] text-slate-300 px-1.5 py-0.5 rounded font-bold tracking-wide uppercase">
              OUTDATED
            </span>
          ) : (
            <span className="text-[9px] bg-emerald-950 text-emerald-400 px-1.5 py-0.5 rounded font-bold tracking-wide uppercase border border-emerald-900/30">
              ACTIVE
            </span>
          )}
        </div>
        <span className="text-[10px] text-slate-500 flex items-center gap-1">
          <Clock className="h-3 w-3" />
          {age} years old
        </span>
      </div>

      <div className="text-[10px] text-slate-500">
        Last Verified: {document.last_updated || '2026-07-14'}
      </div>

      {isOutdated && document.replaced_by && (
        <div className="text-[10px] text-amber-500 flex items-center gap-1 bg-amber-950/15 p-2 rounded border border-amber-900/20 font-medium">
          <ArrowRight className="h-3.5 w-3.5 flex-shrink-0" />
          <span>Superseded by: <strong>{document.replaced_by}</strong></span>
        </div>
      )}
      
      {isOutdated && document.reason && (
        <div className="text-[9px] text-[#64748b] italic">
          Reason: "{document.reason}"
        </div>
      )}
    </div>
  );
}
