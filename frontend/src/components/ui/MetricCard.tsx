import type { LucideIcon } from 'lucide-react';
import { cn } from '../../utils/helpers';

export function MetricCard({
  icon: Icon,
  label,
  value,
  subValue,
  accent = 'cyan',
  className,
}: {
  icon: LucideIcon;
  label: string;
  value: string | number;
  subValue?: string;
  accent?: 'cyan' | 'violet' | 'green' | 'amber' | 'red' | 'blue';
  className?: string;
}) {
  const accentMap: Record<string, string> = {
    cyan: 'text-accent',
    violet: 'text-violet-400',
    green: 'text-rail-green',
    amber: 'text-rail-amber',
    red: 'text-rail-red',
    blue: 'text-rail-blue',
  };

  const iconBgMap: Record<string, string> = {
    cyan: 'bg-accent/10 border-accent/20',
    violet: 'bg-violet-500/10 border-violet-500/20',
    green: 'bg-rail-green/10 border-rail-green/20',
    amber: 'bg-rail-amber/10 border-rail-amber/20',
    red: 'bg-rail-red/10 border-rail-red/20',
    blue: 'bg-rail-blue/10 border-rail-blue/20',
  };

  return (
    <div className={cn('metric-card', className)}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-xs font-medium uppercase tracking-wider text-gray-500">{label}</p>
          <p className={cn('text-3xl font-bold mt-1.5 font-mono', accentMap[accent])}>{value}</p>
          {subValue && <p className="text-xs text-gray-500 mt-1">{subValue}</p>}
        </div>
        <div className={cn('w-10 h-10 rounded-lg border flex items-center justify-center shrink-0', iconBgMap[accent])}>
          <Icon className={cn('h-5 w-5', accentMap[accent])} />
        </div>
      </div>
    </div>
  );
}