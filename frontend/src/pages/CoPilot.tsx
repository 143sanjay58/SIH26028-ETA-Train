import { useState, useEffect, useMemo } from 'react';
import { copilotApi, trainApi } from '../services/api';
import { useWebSocket } from '../contexts/WebSocketContext';
import { useAuth } from '../contexts/AuthContext';
import {
  RadioTower,
  Send,
  ShieldCheck,
  AlertTriangle,
  Loader2,
  Info,
  CheckCircle2,
  ListChecks,
} from 'lucide-react';
import {
  cn,
  formatDateTime,
  getCoPilotPriorityBadge,
  getCoPilotReasonLabel,
  getCoPilotStatusBadge,
} from '../utils/helpers';
import { SectionHeader } from '../components/ui/SectionHeader';
import { MetricCard } from '../components/ui/MetricCard';
import { EmptyState } from '../components/ui/EmptyState';
import type {
  CoPilotReport,
  CoPilotReportPriority,
  CoPilotReportReason,
  CoPilotReportStatus,
  Train,
} from '../types';
import toast from 'react-hot-toast';

const REASONS: { value: CoPilotReportReason; label: string }[] = [
  { value: 'SIGNAL_ISSUE', label: 'Signal Issue' },
  { value: 'TRACK_OBSTRUCTION', label: 'Track Obstruction' },
  { value: 'TECHNICAL_ISSUE', label: 'Technical Issue' },
  { value: 'OPERATIONAL_ISSUE', label: 'Operational Issue' },
  { value: 'PASSENGER_RELATED', label: 'Passenger Related' },
  { value: 'WEATHER_RELATED', label: 'Weather Related' },
  { value: 'OTHER', label: 'Other' },
];

const PRIORITIES: CoPilotReportPriority[] = ['LOW', 'MEDIUM', 'HIGH'];

const STATUS_TABS: (CoPilotReportStatus | 'ALL')[] = ['ALL', 'NEW', 'ACKNOWLEDGED', 'CLOSED'];

export default function CoPilot() {
  const { user } = useAuth();
  const { onCopilotReport } = useWebSocket();

  const [trains, setTrains] = useState<Train[]>([]);
  const [reports, setReports] = useState<CoPilotReport[]>([]);
  const [statusTab, setStatusTab] = useState<CoPilotReportStatus | 'ALL'>('ALL');
  const [isLoading, setIsLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const [trainNumber, setTrainNumber] = useState('');
  const [trainId, setTrainId] = useState<number | undefined>();
  const [stationCode, setStationCode] = useState('');
  const [reason, setReason] = useState<CoPilotReportReason>('SIGNAL_ISSUE');
  const [priority, setPriority] = useState<CoPilotReportPriority>('MEDIUM');
  const [delayMinutes, setDelayMinutes] = useState('');
  const [message, setMessage] = useState('');

  useEffect(() => {
    let mounted = true;
    const fetchAll = async () => {
      setIsLoading(true);
      try {
        const [mineRes, trainsRes] = await Promise.all([
          copilotApi.myReports({ limit: 100 }),
          trainApi.list({ page_size: 100 }),
        ]);
        if (!mounted) return;
        setReports(mineRes.data || []);
        setTrains(trainsRes.data.trains || []);
      } catch { /* handled by empty state */ } finally {
        if (mounted) setIsLoading(false);
      }
    };
    fetchAll();

    const unsub = onCopilotReport((data) => {
      if (!data || typeof data !== 'object' || !('id' in data)) return;
      const report = data as CoPilotReport;
      if (report.user_id !== user?.id) return;
      setReports((prev) =>
        prev.find((r) => r.id === report.id)
          ? prev.map((r) => (r.id === report.id ? report : r))
          : [report, ...prev]
      );
    });

    return () => { mounted = false; unsub(); };
  }, [onCopilotReport, user?.id]);

  useEffect(() => {
    const selected = trainNumber
      ? trains.find((t) => t.train_number.toUpperCase() === trainNumber.toUpperCase())
      : undefined;
    setTrainId(selected?.id);
  }, [trainNumber, trains]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!trainNumber.trim() || !message.trim()) return;
    setSubmitting(true);
    try {
      const res = await copilotApi.createReport({
        train_number: trainNumber.trim().toUpperCase(),
        station_code: stationCode.trim().toUpperCase() || undefined,
        reason,
        priority,
        message: message.trim(),
        current_delay_minutes: delayMinutes ? parseInt(delayMinutes) : 0,
      });
      toast.success(`Delay report #${res.data.id} filed`);
      setReports((prev) => [res.data, ...prev]);
      setTrainNumber('');
      setStationCode('');
      setReason('SIGNAL_ISSUE');
      setPriority('MEDIUM');
      setDelayMinutes('');
      setMessage('');
    } catch {
      toast.error('Failed to file report');
    } finally {
      setSubmitting(false);
    }
  };

  const filtered = useMemo(
    () => (statusTab === 'ALL' ? reports : reports.filter((r) => r.status === statusTab)),
    [reports, statusTab]
  );

  const newCount = reports.filter((r) => r.status === 'NEW').length;
  const ackCount = reports.filter((r) => r.status === 'ACKNOWLEDGED').length;
  const activeTrains = trains.length;

  return (
    <div className="space-y-6">
      <SectionHeader
        title="Train Co-Pilot Terminal"
        subtitle="Operational delay reporting from the cab — surfaced live to the Control Room"
        right={
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <span className="badge-neutral">STATION STAFF</span>
            <span className="hidden sm:inline">{user?.station_id ? `Station ${user.station_id}` : 'En route'}</span>
          </div>
        }
      />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <MetricCard icon={RadioTower} label="My reports" value={reports.length} accent="cyan" />
        <MetricCard icon={AlertTriangle} label="Pending in control room" value={newCount} accent="red" />
        <MetricCard icon={CheckCircle2} label="Acknowledged" value={ackCount} accent="amber" />
        <MetricCard icon={ListChecks} label="Active trains" value={activeTrains} accent="violet" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="card p-5">
          <div className="flex items-center gap-2 mb-4">
            <Send className="h-4 w-4 text-accent" />
            <h2 className="text-sm font-semibold text-gray-200">File a delay report</h2>
          </div>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1.5">Train number</label>
              <input
                type="text"
                value={trainNumber}
                onChange={(e) => setTrainNumber(e.target.value.toUpperCase())}
                placeholder="e.g. 12303"
                className="input font-mono"
                required
                aria-label="Train number"
              />
              {trainId && <p className="text-[11px] text-accent mt-1">Matches {trains.find((t) => t.id === trainId)?.train_name}</p>}
              {trainNumber && !trainId && <p className="text-[11px] text-rail-amber mt-1">Unknown to network — report still accepted.</p>}
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1.5">Reason</label>
                <select value={reason} onChange={(e) => setReason(e.target.value as CoPilotReportReason)} className="input" required>
                  {REASONS.map((r) => <option key={r.value} value={r.value}>{r.label}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1.5">Priority</label>
                <select value={priority} onChange={(e) => setPriority(e.target.value as CoPilotReportPriority)} className="input" required>
                  {PRIORITIES.map((p) => <option key={p} value={p}>{p.charAt(0) + p.slice(1).toLowerCase()}</option>)}
                </select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1.5">Station code</label>
                <input
                  type="text"
                  value={stationCode}
                  onChange={(e) => setStationCode(e.target.value.toUpperCase())}
                  placeholder="e.g. BEQ"
                  className="input font-mono"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1.5">Delay (min)</label>
                <input
                  type="number"
                  min="0"
                  value={delayMinutes}
                  onChange={(e) => setDelayMinutes(e.target.value)}
                  className="input font-mono"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1.5">What happened?</label>
              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                className="input min-h-[100px]"
                placeholder="Describe the signal, track, technical or operational cause…"
                required
              />
            </div>
            <button type="submit" disabled={submitting || !trainNumber.trim() || !message.trim()} className="btn-primary w-full">
              {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
              File Report
            </button>
          </form>
          <div className="flex items-start gap-2 mt-4 px-3 py-2.5 rounded-lg bg-white/[0.03]">
            <Info className="h-4 w-4 text-rail-blue shrink-0 mt-0.5" />
            <p className="text-[11px] text-gray-500">
              Reports create an operational alert and appear live in the Control Room. They are recorded for model
              retraining but are <strong className="text-gray-300">not</strong> injected into the frozen SIH26028 ML features.
            </p>
          </div>
        </div>

        <div className="lg:col-span-2 card">
          <div className="flex flex-wrap items-center gap-2 px-4 py-3 border-b border-white/[0.06]">
            <h2 className="text-sm font-semibold text-gray-200 mr-auto">My reports</h2>
            <div className="flex gap-1">
              {STATUS_TABS.map((tab) => (
                <button
                  key={tab}
                  onClick={() => setStatusTab(tab)}
                  className={cn(
                    'px-2.5 py-1 rounded-md text-[11px] font-semibold transition-colors',
                    statusTab === tab ? 'bg-accent/15 text-accent border border-accent/30' : 'text-gray-500 hover:text-gray-300'
                  )}
                >
                  {tab === 'ALL' ? 'All' : tab.charAt(0) + tab.slice(1).toLowerCase()}
                </button>
              ))}
            </div>
          </div>

          <div className="divide-y divide-white/[0.03] max-h-[560px] overflow-y-auto">
            {isLoading ? (
              <div className="py-10 text-center"><Loader2 className="h-6 w-6 animate-spin mx-auto text-accent" /></div>
            ) : filtered.length === 0 ? (
              <EmptyState icon={ShieldCheck} title="No reports yet" message="File your first delay report from the form." />
            ) : filtered.map((report) => (
              <div key={report.id} className="px-4 py-3.5 animate-slide-in">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-mono font-bold text-gray-100">#{report.id}</span>
                  <span className="font-mono text-sm text-gray-200">{report.train_number}</span>
                  {report.station_code && <span className="font-mono text-xs text-gray-500">{report.station_code}</span>}
                  <span className={cn(getCoPilotPriorityBadge(report.priority))}>{report.priority}</span>
                  <span className={cn(getCoPilotStatusBadge(report.status))}>{report.status}</span>
                  <span className="ml-auto text-[11px] text-gray-600">{formatDateTime(report.created_at)}</span>
                </div>
                <div className="mt-1.5 flex items-start gap-2">
                  <span className="badge-info shrink-0">{getCoPilotReasonLabel(report.reason)}</span>
                  <p className="text-sm text-gray-400">{report.message}</p>
                </div>
                <div className="mt-1.5 flex items-center gap-3 text-[11px] text-gray-600">
                  {report.current_delay_minutes > 0 && <span className="font-mono text-rail-amber">+{report.current_delay_minutes} min</span>}
                  <span>Reporter: {report.reporter_call_sign || `#${report.user_id}`}</span>
                  {report.acknowledged_at && <span>Acknowledged {formatDateTime(report.acknowledged_at)}</span>}
                  {report.closed_at && <span>Closed {formatDateTime(report.closed_at)}</span>}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}