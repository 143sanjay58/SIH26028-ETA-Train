import { CheckCircle2, Circle, Clock, AlertTriangle, TrainFront } from 'lucide-react';
import { cn } from '../../utils/helpers';
import type { TrainSchedule } from '../../types';

interface TimelineStop {
  schedule?: TrainSchedule;
  isCurrent?: boolean;
  isNext?: boolean;
  delayMin?: number;
}

function fmtTime(value?: string): string | null {
  if (!value) return null;
  if (/^\d{2}:\d{2}$/.test(value)) return value;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true }).toUpperCase();
}

export function StationTimeline({ stops }: { stops: TimelineStop[] }) {
  return (
    <ol className="relative" aria-label="Route timeline">
      {stops.map((stop, i) => {
        const s = stop.schedule;
        const isLast = i === stops.length - 1;
        const arrival = fmtTime(s?.scheduled_arrival);
        const dep = fmtTime(s?.scheduled_departure);

        return (
          <li key={s?.id ?? `${i}`} className="relative flex gap-3 pb-5 last:pb-0">
            {!isLast && (
              <span className={cn('absolute left-[13px] top-7 bottom-0 w-px', stop.isCurrent ? 'bg-accent/40' : 'bg-white/10')} aria-hidden="true" />
            )}

            <div className="relative shrink-0">
              {stop.isCurrent ? (
                <span className="w-7 h-7 rounded-full bg-accent/20 border border-accent flex items-center justify-center animate-pulse-slow">
                  <TrainFront className="h-3.5 w-3.5 text-accent" />
                </span>
              ) : stop.isNext ? (
                <span className="w-7 h-7 rounded-full bg-violet/15 border border-violet flex items-center justify-center">
                  <Clock className="h-3.5 w-3.5 text-violet-300" />
                </span>
              ) : (stop.delayMin ?? 0) > 0 ? (
                <span className="w-7 h-7 rounded-full bg-rail-amber/15 border border-rail-amber flex items-center justify-center">
                  <AlertTriangle className="h-3.5 w-3.5 text-rail-amber" />
                </span>
              ) : s?.is_origin ? (
                <span className="w-7 h-7 rounded-full bg-rail-green/15 border border-rail-green flex items-center justify-center">
                  <CheckCircle2 className="h-3.5 w-3.5 text-rail-green" />
                </span>
              ) : (
                <span className="w-7 h-7 rounded-full bg-white/5 border border-white/10 flex items-center justify-center">
                  <Circle className="h-3.5 w-3.5 text-gray-500" />
                </span>
              )}
            </div>

            <div className="flex-1 min-w-0 -mt-0.5">
              <div className="flex items-center justify-between gap-2 flex-wrap">
                <div className="flex items-center gap-2 min-w-0">
                  <p className={cn('text-sm font-medium truncate', stop.isCurrent || stop.isNext ? 'text-gray-100' : 'text-gray-400')}>
                    {s?.station_name || `Station ${s?.sequence}`}
                  </p>
                  {s?.station_code && <span className="text-[10px] font-mono text-gray-600 uppercase">{s.station_code}</span>}
                </div>
                <div className="flex items-center gap-2 text-xs font-mono shrink-0">
                  {arrival && <span className="text-gray-500">{arrival}</span>}
                  {stop.isNext && <span className="text-violet-300 font-bold">ETA</span>}
                  {(stop.delayMin ?? 0) > 0 && (
                    <span className="text-rail-amber font-semibold">+{stop.delayMin}m</span>
                  )}
                </div>
              </div>
              {dep && i < stops.length - 1 && (
                <p className="text-[11px] text-gray-600 mt-0.5">Dep {dep}</p>
              )}
            </div>
          </li>
        );
      })}
    </ol>
  );
}