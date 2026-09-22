import { ArrowDown, ArrowUp, Minus, BrainCircuit } from 'lucide-react';
import { cn, formatTime } from '../../utils/helpers';
import { ConfidenceRing } from '../ui/ConfidenceRing';
import type { ETAResponse } from '../../types';

export function ETACard({ eta }: { eta: ETAResponse | null }) {
  if (!eta) {
    return (
      <div className="card p-5">
        <p className="text-sm text-gray-500">Calculating ETA…</p>
      </div>
    );
  }

  const predicted = eta.predicted_arrival_time ? new Date(eta.predicted_arrival_time) : null;
  const lower = eta.prediction_interval_lower ? new Date(eta.prediction_interval_lower) : null;
  const upper = eta.prediction_interval_upper ? new Date(eta.prediction_interval_upper) : null;
  const deltaMin = eta.predicted_arrival_delay_minutes;
  const TrendIconCls = deltaMin > 0 ? ArrowUp : deltaMin < 0 ? ArrowDown : Minus;
  const trendLabel = deltaMin > 0 ? 'DELAY INCREASING' : deltaMin < 0 ? 'RECOVERING' : 'ON SCHEDULE';
  const trendColor = deltaMin > 0 ? 'text-rail-red' : deltaMin < 0 ? 'text-rail-green' : 'text-gray-400';

  return (
    <div className="card p-5 relative overflow-hidden">
      <div className="flex items-center gap-2 mb-4">
        <BrainCircuit className="h-4 w-4 text-violet-400" />
        <span className="text-xs font-semibold uppercase tracking-widest text-gray-400">AI ETA Prediction</span>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex-1">
          <p className="text-xs text-gray-500 uppercase tracking-wider">Predicted arrival at destination</p>
          <p className="font-mono text-4xl font-bold text-gray-50 tabular-nums mt-1.5">
            {predicted ? formatTime(predicted.toISOString()) : '--:--'}
          </p>
          <p className="text-sm text-gray-500 mt-1 font-mono">{eta.destination_station}</p>

          <div className="flex items-center gap-2 mt-3">
            <TrendIconCls className={cn('h-4 w-4', trendColor)} />
            <span className={cn('text-xs font-bold tracking-wide', trendColor)}>{trendLabel}</span>
          </div>

          <div className="mt-3 space-y-1.5">
            <div className="flex items-center justify-between text-xs">
              <span className="text-gray-500">Predicted delay</span>
              <span className={cn('font-mono font-bold', deltaMin > 0 ? 'text-rail-red' : deltaMin < 0 ? 'text-rail-green' : 'text-gray-300')}>
                {deltaMin >= 0 ? '+' : ''}{deltaMin.toFixed(0)} min
              </span>
            </div>
            {(lower && upper) && (
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-500">Prediction interval</span>
                <span className="font-mono text-gray-300">
                  {formatTime(lower.toISOString())} – {formatTime(upper.toISOString())}
                </span>
              </div>
            )}
            {eta.model_type && (
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-500">Model</span>
                <span className="font-mono text-violet-300">{eta.model_type}</span>
              </div>
            )}
          </div>
        </div>

        {eta.confidence_score !== undefined && (
          <div className="shrink-0">
            <ConfidenceRing confidence={eta.confidence_score} />
          </div>
        )}
      </div>
    </div>
  );
}