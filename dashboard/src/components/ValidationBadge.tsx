'use client';

import { CheckCircle, XCircle } from 'lucide-react';

interface ValidationBadgeProps {
  hasClinicalTrial: boolean;
  hasLiterature: boolean;
}

export default function ValidationBadge({ hasClinicalTrial, hasLiterature }: ValidationBadgeProps) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {hasClinicalTrial ? (
        <span className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <CheckCircle className="w-3 h-3" />
          Clinical Trial
        </span>
      ) : (
        <span className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded-full bg-slate-500/10 text-slate-500 border border-slate-600/20">
          <XCircle className="w-3 h-3" />
          No Trial
        </span>
      )}
      {hasLiterature ? (
        <span className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">
          <CheckCircle className="w-3 h-3" />
          Literature
        </span>
      ) : (
        <span className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded-full bg-slate-500/10 text-slate-500 border border-slate-600/20">
          <XCircle className="w-3 h-3" />
          No Literature
        </span>
      )}
    </div>
  );
}
