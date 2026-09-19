import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatTime(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true }).toUpperCase();
}

export function formatTime24(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false });
}

export function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
}

export function formatDateTime(dateString: string): string {
  return `${formatDate(dateString)} ${formatTime(dateString)}`;
}

export function formatDuration(minutes: number): string {
  if (minutes < 60) return `${minutes} min`;
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
}

export function timeAgo(dateString: string): string {
  const seconds = Math.floor((Date.now() - new Date(dateString).getTime()) / 1000);
  if (seconds < 5) return 'just now';
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export function getDelayColor(delayMinutes: number): string {
  if (delayMinutes <= 0) return 'text-rail-green';
  if (delayMinutes <= 10) return 'text-rail-amber';
  if (delayMinutes <= 30) return 'text-orange-500';
  return 'text-rail-red';
}

export function getDelayBg(delayMinutes: number): string {
  if (delayMinutes <= 0) return 'bg-rail-green/10 border-rail-green/20';
  if (delayMinutes <= 10) return 'bg-rail-amber/10 border-rail-amber/20';
  if (delayMinutes <= 30) return 'bg-orange-500/10 border-orange-500/20';
  return 'bg-rail-red/10 border-rail-red/20';
}

export function getSeverityColor(severity: string): string {
  switch (severity) {
    case 'LOW': return 'text-rail-green';
    case 'MEDIUM': return 'text-rail-amber';
    case 'HIGH': return 'text-orange-500';
    case 'CRITICAL': return 'text-rail-red';
    case 'NORMAL': return 'text-rail-green';
    case 'CAUTION': return 'text-rail-amber';
    case 'SEVERE': return 'text-rail-red';
    case 'INFO': return 'text-rail-blue';
    case 'WARNING': return 'text-rail-amber';
    default: return 'text-gray-500';
  }
}

export function getSeverityBg(severity: string): string {
  switch (severity) {
    case 'LOW': return 'badge-success';
    case 'MEDIUM': return 'badge-warning';
    case 'HIGH': return 'bg-orange-500/15 text-orange-500 border border-orange-500/20';
    case 'CRITICAL': return 'badge-critical';
    case 'NORMAL': return 'badge-success';
    case 'CAUTION': return 'badge-warning';
    case 'SEVERE': return 'badge-critical';
    case 'INFO': return 'badge-info';
    case 'WARNING': return 'badge-warning';
    default: return 'badge-neutral';
  }
}

export function getTrainTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    EXPRESS: 'Express',
    SUPERFAST: 'Superfast',
    MAIL: 'Mail',
    PASSENGER: 'Passenger',
    SUBURBAN: 'Suburban',
    FREIGHT: 'Freight',
    RAJDHANI: 'Rajdhani',
    SHATABDI: 'Shatabdi',
    DURONTO: 'Duronto',
    VANDE_BHARAT: 'Vande Bharat',
  };
  return labels[type] || type;
}

export function getStatusColor(status: string): string {
  switch (status) {
    case 'SCHEDULED': return 'text-rail-blue';
    case 'RUNNING': return 'text-rail-green';
    case 'DELAYED': return 'text-rail-amber';
    case 'ARRIVED': return 'text-gray-500';
    case 'CANCELLED': return 'text-rail-red';
    case 'DIVERTED': return 'text-violet-400';
    case 'TERMINATED': return 'text-rail-red';
    default: return 'text-gray-500';
  }
}

export function getStatusBg(status: string): string {
  switch (status) {
    case 'SCHEDULED': return 'badge-info';
    case 'RUNNING': return 'badge-success';
    case 'DELAYED': return 'badge-warning';
    case 'ARRIVED': return 'badge-neutral';
    case 'CANCELLED': return 'badge-critical';
    case 'DIVERTED': return 'bg-violet-500/15 text-violet-300 border border-violet-500/20';
    case 'TERMINATED': return 'badge-critical';
    default: return 'badge-neutral';
  }
}

export function getDataSourceLabel(source: string): string {
  const labels: Record<string, string> = {
    LIVE: 'Live Railway',
    CACHED: 'Cached',
    SIMULATION: 'Simulation',
    ESTIMATED: 'Estimated',
    GPS_DERIVED: 'GPS Derived',
    WEATHER_API: 'Weather API',
  };
  return labels[source] || source;
}

export function getDataSourceBadgeClass(source: string): string {
  switch (source) {
    case 'LIVE': return 'badge-live';
    case 'CACHED': return 'bg-rail-blue/15 text-rail-blue border border-rail-blue/20';
    case 'SIMULATION': return 'badge-sim';
    case 'ESTIMATED': return 'bg-rail-amber/15 text-rail-amber border border-rail-amber/20';
    case 'GPS_DERIVED': return 'bg-accent/15 text-accent border border-accent/20';
    case 'WEATHER_API': return 'bg-violet/15 text-violet-300 border border-violet/20';
    default: return 'badge-neutral';
  }
}

export function getRiskBadge(risk: string): string {
  switch (risk?.toUpperCase()) {
    case 'LOW': return 'badge-success';
    case 'MEDIUM': return 'badge-warning';
    case 'HIGH': return 'bg-orange-500/15 text-orange-500 border border-orange-500/20';
    case 'CRITICAL': return 'badge-critical';
    default: return 'badge-neutral';
  }
}

export function getScenarioLabel(scenario: string): string {
  const labels: Record<string, string> = {
    NORMAL: 'Normal',
    CONGESTION: 'Congestion',
    SIGNAL_DELAY: 'Signal Delay',
    EXTENDED_HALT: 'Extended Halt',
    SPEED_RESTRICTION: 'Speed Restriction',
    HEAVY_RAIN: 'Heavy Rain',
    LOW_VISIBILITY: 'Low Visibility',
    PRECEDING_TRAIN_DELAY: 'Preceding Train Delay',
    UNSCHEDULED_STOP: 'Unscheduled Stop',
    CASCADING_DELAY: 'Cascade Delay',
    RECOVERY: 'Recovery',
  };
  return labels[scenario] || scenario;
}

export function getEventTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    SIGNAL_WAIT: 'Signal Wait',
    PLATFORM_OCCUPIED: 'Platform Occupied',
    PRECEDING_TRAIN: 'Preceding Train',
    CROSSING_TRAIN: 'Crossing Train',
    CREW_CHANGE: 'Crew Change',
    TECHNICAL_CHECK: 'Technical Check',
    PASSENGER_ASSISTANCE: 'Passenger Assistance',
    MEDICAL_EMERGENCY: 'Medical Emergency',
    TRACK_WORK: 'Track Work',
    MAINTENANCE_BLOCK: 'Maintenance Block',
    LOCOMOTIVE_ISSUE: 'Locomotive Issue',
    COACH_ISSUE: 'Coach Issue',
    WATER_CLEANING: 'Water / Cleaning',
    WEATHER: 'Weather',
    SECURITY_CHECK: 'Security Check',
    OPERATIONAL_HOLD: 'Operational Hold',
    OTHER: 'Other',
  };
  return labels[type] || type;
}

export function formatNumberLocale(n: number): string {
  return n.toLocaleString('en-IN');
}