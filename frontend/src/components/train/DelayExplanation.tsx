import { BrainCircuit, Minus, Plus, AlertCircle } from 'lucide-react';
import { cn } from '../../utils/helpers';
import type { Explanation } from '../../types';

export function DelayExplanation({ explanations, totalDelay }: { explanations?: Explanation[]; totalDelay?: number }) {
  const factors = explanations || [];
  const total = totalDelay ?? factors.reduce((sum, f) => sum + (f.contribution_minutes || 0), 0);

  if (factors.length === 0) {
    return (
      <div className="card p-5">
        <div className="flex items-center gap-2 mb-3">
          <BrainCircuit className="h-4 w-4 text-violet-400" />
          <span className="text-xs font-semibold uppercase tracking-widest text-gray-400">Why ETA changed</span>
        </div>
        <p className="text-sm text-gray-500">No factor explanation available from the model.</p>
      </div>
    );
  }

  const maxAbs = Math.max(1, ...factors.map((f) => Math.abs(f.contribution_minutes || 0)));

  return (
    <div className="card p-5">
      <div className="flex items-center gap-2 mb-4">
        <BrainCircuit className="h-4 w-4 text-violet-400" />
        <span className="text-xs font-semibold uppercase tracking-widest text-gray-400">Why ETA changed</span>
      </div>

      <div className="space-y-2.5">
        {factors.map((f, i) => {
          const contribution = f.contribution_minutes || 0;
          const width = (Math.abs(contribution) / maxAbs) * 100;
          const positive = contribution > 0;
          return (
            <div key={i} className="flex items-center gap-3">
              <span className="text-xs text-gray-400 w-32 truncate shrink-0" title={f.factor_name}>
                {f.factor_name.replace(/_/g, ' ')}
              </span>
              <div className="flex-1 h-2 rounded-full bg-white/5 overflow-hidden">
                <div
                  className={cn('h-full rounded-full transition-all duration-700', positive ? 'bg-rail-red/70' : 'bg-rail-green/70')}
                  style={{ width: `${width}%` }}
                />
              </div>
              <span className={cn('w-16 text-right text-xs font-mono font-semibold shrink-0', positive ? 'text-rail-red' : 'text-rail-green')}>
                {positive ? <Plus className="inline h-3 w-3 -mt-0.5" /> : <Minus className="inline h-3 w-3 -mt-0.5" />}
                {Math.abs(contribution).toFixed(1)}m
              </span>
            </div>
          );
        })}
      </div>

      <div className="mt-4 pt-3 border-t border-white/[0.06] flex items-center justify-between">
        <span className="text-xs text-gray-500 uppercase tracking-wider">Total net impact</span>
        <span className={cn('font-mono font-bold text-sm', total > 0 ? 'text-rail-red' : total < 0 ? 'text-rail-green' : 'text-gray-300')}>
          {total >= 0 ? '+' : ''}{total.toFixed(0)} min
        </span>
      </div>
    </div>
  );
}

export function EmptyExplanation() {
  return (
    <div className="card p-8 flex flex-col items-center text-center">
      <AlertCircle className="h-8 w-8 text-gray-600 mb-3" />
      <p className="text-sm text-gray-400">Explanation data unavailable</p>
      <p className="text-xs text-gray-600 mt-1">The ETA model did not return factor-level explanations.</p>
    </div>
  );
}