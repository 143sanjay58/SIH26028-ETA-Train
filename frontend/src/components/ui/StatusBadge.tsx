import { cn, getDataSourceBadgeClass, getStatusBg } from '../../utils/helpers';

export function StatusBadge({ status, className }: { status: string; className?: string }) {
  return (
    <span className={cn(getStatusBg(status), className)}>
      {status.replace(/_/g, ' ')}
    </span>
  );
}

export function SourceBadge({ source, className }: { source: string; className?: string }) {
  const labelMap: Record<string, string> = {
    LIVE: 'LIVE RAILWAY DATA',
    CACHED: 'RAILWAY FEED',
    SIMULATION: 'SIMULATION',
    ESTIMATED: 'ESTIMATED',
    GPS_DERIVED: 'GPS-DERIVED',
    WEATHER_API: 'WEATHER API',
  };
  return (
    <span className={cn(getDataSourceBadgeClass(source), className)} title={`Data source: ${source}`}>
      {labelMap[source] || source}
    </span>
  );
}