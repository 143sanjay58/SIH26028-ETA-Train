import { ArrowUp, ArrowDown, Minus, BrainCircuit, MapPin, Loader2 } from 'lucide-react';
import { cn, formatTime, getDelayColor } from '../../utils/helpers';
import { ConfidenceRing } from '../ui/ConfidenceRing';
import { SourceBadge } from '../ui/StatusBadge';
import type { SIHETAResponse } from '../../types';

export function SIHETACard({ eta, loading }: { eta: SIHETAResponse | null; loading?: boolean }) {
  if (loading) {
    return (
      <div className="card p-5" role="status">
        <div className="flex items-center gap-2 mb-3">
          <BrainCircuit className="h-4 w-4 text-accent" />
          <span className="text-xs font-semibold uppercase tracking-widest text-gray-400">SIH26028 ETA Core</span>
        </div>
        <div className="flex items-center gap-3 text-sm text-gray-500">
          <Loader2 className="h-4 w-4 animate-spin text-accent" />
          Running LightGBM inference across upcoming stations…
        </div>
        <p className="text-[11px] text-gray-600 mt-2">First computation builds 21 features per station and can take a minute.</p>
      </div>
    );
  }

  if (!eta) {
    return (
      <div className="card p-5">
        <p className="text-sm text-gray-500">SIH26028 ETA core not available for this train.</p>
      </div>
    );
  }

  const predicted = eta.predicted_arrival_time ? new Date(eta.predicted_arrival_time) : null;
  const deltaMin = eta.predicted_arrival_delay_minutes;
  const TrendIcon = deltaMin > 0 ? ArrowUp : deltaMin < 0 ? ArrowDown : Minus;
  const trendColor = deltaMin > 0 ? 'text-rail-red' : deltaMin < 0 ? 'text-rail-green' : 'text-gray-400';
  const conf0to1 = eta.confidence_score !== undefined ? eta.confidence_score / 100 : undefined;

  return (
    <div className="card p-5 relative overflow-hidden">
      <div className="flex items-center gap-2 mb-1">
        <BrainCircuit className="h-4 w-4 text-accent" />
        <span className="text-xs font-semibold uppercase tracking-widest text-gray-400">SIH26028 ETA Core</span>
        <SourceBadge source={eta.data_source} className="ml-auto" />
      </div>
      <p className="text-[11px] text-gray-600 mb-4">
        LightGBM pipeline · {eta.model_version} · position from {eta.position_source || eta.current_station}
      </p>

      <div className="flex items-center gap-4">
        <div className="flex-1">
          <p className="text-xs text-gray-500 uppercase tracking-wider">Predicted arrival at destination</p>
          <p className="font-mono text-3xl font-bold text-gray-50 tabular-nums mt-1.5">
            {predicted ? formatTime(predicted.toISOString()) : '--:--'}
          </p>
          <p className="text-sm text-gray-500 mt-1 font-mono">{eta.destination_station_name || eta.destination_station || '—'}</p>

          <div className="flex items-center gap-2 mt-2.5">
            <TrendIcon className={cn('h-4 w-4', trendColor)} />
            <span className="text-xs font-bold text-gray-300">{Math.abs(deltaMin).toFixed(0)} min {deltaMin >= 0 ? 'late' : 'early'}</span>
            <span className={cn('text-[10px] uppercase tracking-wider', trendColor)}>
              {eta.delay_trend || 'STABLE'}
            </span>
          </div>

          <div className="mt-3 space-y-1.5">
            <div className="flex items-center justify-between text-xs">
              <span className="text-gray-500">Remaining</span>
              <span className="font-mono text-gray-300">
                {new Date(eta.predicted_remaining_minutes * 60000).toISOString().slice(11, 16)} h
              </span>
            </div>
            {eta.confidence_level && (
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-500">Confidence</span>
                <span className="font-mono text-gray-300">{eta.confidence_level} · {eta.confidence_score?.toFixed(0) ?? '—'}%</span>
              </div>
            )}
            {eta.impact_severity && (
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-500">Impact</span>
                <span className={cn('font-mono', getDelayColor(deltaMin))}>{eta.impact_severity}</span>
              </div>
            )}
            {eta.route_impact && (
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-500">Route</span>
                <span className="font-mono text-gray-300">{eta.route_impact}</span>
              </div>
            )}
          </div>

          {eta.upcoming_stations.length > 0 && (
            <div className="mt-4 pt-3 border-t border-white/[0.06]">
              <p className="text-[10px] uppercase tracking-widest text-gray-600 mb-2 flex items-center gap-1.5">
                <MapPin className="h-3 w-3" /> Upcoming stations ({eta.upcoming_station_count})
              </p>
              <div className="space-y-1.5">
                {eta.upcoming_stations.slice(0, 5).map((s) => (
                  <div key={s.station_code} className="flex items-center justify-between text-xs">
                    <span className="text-gray-300 flex items-center gap-2 min-w-0">
                      <span className="font-mono text-gray-500">{s.station_code}</span>
                      <span className="truncate">{s.station_name}</span>
                    </span>
                    <span className="flex items-center gap-2 shrink-0">
                      <span className="font-mono text-gray-400">{formatTime(new Date(s.predicted_eta).toISOString())}</span>
                      <span className={cn('font-mono', getDelayColor(s.predicted_arrival_delay_minutes))}>
                        {s.predicted_arrival_delay_minutes >= 0 ? '+' : ''}{s.predicted_arrival_delay_minutes.toFixed(0)}m
                      </span>
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {conf0to1 !== undefined && (
          <div className="shrink-0">
            <ConfidenceRing confidence={conf0to1} />
          </div>
        )}
      </div>
    </div>
  );
}