import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { trainApi, alertApi, congestionApi, simulationApi, predictionApi, copilotApi } from '../services/api';
import { useWebSocket } from '../contexts/WebSocketContext';
import {
  Train as TrainIcon,
  AlertTriangle,
  Route as RouteIcon,
  Zap,
  Gauge,
  Search,
  ArrowRight,
  Radio,
  RefreshCw,
  RadioTower,
  Check,
  X,
} from 'lucide-react';
import { cn, formatTime, formatDateTime, getDataSourceBadgeClass, getCoPilotPriorityBadge, getCoPilotReasonLabel, getCoPilotStatusBadge } from '../utils/helpers';
import { SectionHeader } from '../components/ui/SectionHeader';
import { MetricCard } from '../components/ui/MetricCard';
import { LoadingSkeleton } from '../components/ui/LoadingSkeleton';
import { EmptyState } from '../components/ui/EmptyState';
import type { Train, Alert, CongestionState, SimulationStatus, SimulationScenario, TrainLiveResponse, CoPilotReport } from '../types';
import toast from 'react-hot-toast';

export default function ControlRoom() {
  const navigate = useNavigate();
  const [trains, setTrains] = useState<Train[]>([]);
  const [live, setLive] = useState<Record<number, TrainLiveResponse>>({});
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [congestion, setCongestion] = useState<CongestionState[]>([]);
  const [simulation, setSimulation] = useState<SimulationStatus | null>(null);
  const [copilotReports, setCopilotReports] = useState<CoPilotReport[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [query, setQuery] = useState('');
  const [sortKey, setSortKey] = useState<'delay' | 'speed' | 'number'>('delay');
  const { isConnected, onTrainUpdate, onAlert, onCongestionUpdate, onCopilotReport } = useWebSocket();

  useEffect(() => {
    let mounted = true;
    const fetchData = async () => {
      try {
        const [trainsRes, alertsRes, congestionRes, simRes, copilotRes] = await Promise.all([
          trainApi.list({ page_size: 100 }),
          alertApi.list({ active_only: true }),
          congestionApi.getNetwork(),
          simulationApi.getStatus(),
          copilotApi.listReports({ limit: 50 }),
        ]);
        if (!mounted) return;
        setTrains(trainsRes.data.trains || []);
        setAlerts(alertsRes.data);
        setCongestion(congestionRes.data);
        setSimulation(simRes.data);
        setCopilotReports(copilotRes.data || []);
      } catch { /* handled by error boundaries */ } finally {
        if (mounted) setIsLoading(false);
      }
    };

    fetchData();

    const liveSub = async () => {
      const ids = trains.map((t) => t.id);
      const results = await Promise.allSettled(ids.map((id) => trainApi.getLive(id)));
      const map: Record<number, TrainLiveResponse> = {};
      results.forEach((r, i) => {
        if (r.status === 'fulfilled') map[ids[i]] = r.value.data;
      });
      setLive(map);
    };
    if (trains.length > 0) liveSub();

    const unsubTrain = onTrainUpdate(() => fetchData());
    const unsubAlert = onAlert((data) => {
      if (data && typeof data === 'object' && 'id' in data) {
        setAlerts((prev) => {
          const nd = data as Alert;
          return prev.find((a) => a.id === nd.id) ? prev.map((a) => (a.id === nd.id ? nd : a)) : [nd, ...prev];
        });
      }
    });
    const unsubCongestion = onCongestionUpdate(() => fetchData());
    const unsubCopilot = onCopilotReport((data) => {
      if (!data || typeof data !== 'object' || !('id' in data)) return;
      const report = data as CoPilotReport;
      setCopilotReports((prev) =>
        prev.find((r) => r.id === report.id)
          ? prev.map((r) => (r.id === report.id ? report : r))
          : [report, ...prev]
      );
    });

    return () => {
      mounted = false;
      unsubTrain();
      unsubAlert();
      unsubCongestion();
      unsubCopilot();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [onTrainUpdate, onAlert, onCongestionUpdate, onCopilotReport]);

  const handleReportAction = async (reportId: number, action: 'acknowledge' | 'close') => {
    try {
      const res = action === 'acknowledge' ? await copilotApi.acknowledge(reportId) : await copilotApi.close(reportId);
      setCopilotReports((prev) =>
        prev.find((r) => r.id === res.data.id)
          ? prev.map((r) => (r.id === res.data.id ? res.data : r))
          : [res.data, ...prev]
      );
      toast.success(`Report #${reportId} ${action === 'acknowledge' ? 'acknowledged' : 'closed'}`);
    } catch {
      toast.error(`Failed to ${action} report`);
    }
  };

  const handleSimulationControl = async (action: string, speed?: number, scenario?: SimulationScenario) => {
    try {
      await simulationApi.control(action, speed, scenario);
      toast.success(`Simulation ${action}d`);
      if (isConnected) window.setTimeout(async () => {
        const s = await simulationApi.getStatus();
        setSimulation(s.data);
      }, 400);
    } catch {
      toast.error(`Failed to ${action} simulation`);
    }
  };

  const rows = useMemo(() => {
    const filtered = trains.filter((t) => {
      if (!query.trim()) return true;
      const q = query.toLowerCase();
      return t.train_number.toLowerCase().includes(q) || t.train_name.toLowerCase().includes(q);
    });
    return filtered
      .map((t) => ({ train: t, data: live[t.id] }))
      .sort((a, b) => {
        if (sortKey === 'number') return a.train.train_number.localeCompare(b.train.train_number);
        const da = a.data?.current_delay_minutes ?? 0;
        const db = b.data?.current_delay_minutes ?? 0;
        if (sortKey === 'speed') {
          const sa = a.data?.current_speed_kmh ?? 0;
          const sb = b.data?.current_speed_kmh ?? 0;
          return sb - sa;
        }
        return db - da;
      });
  }, [trains, live, query, sortKey]);

  const criticalDelays = trains.filter((t) => (live[t.id]?.current_delay_minutes ?? 0) > 30).length;
  const delayed = Object.values(live).filter((l) => (l.current_delay_minutes ?? 0) > 0).length;
  const congestedSections = congestion.filter((c) => c.level === 'HIGH' || c.level === 'CRITICAL').length;

  return (
    <div className="space-y-6">
      <SectionHeader
        title="Railway Operations Center"
        subtitle="Network Intelligence & Predictive Operations"
        right={
          <div className="flex items-center gap-2">
            <div className={cn('flex items-center gap-1.5 px-3 py-1.5 rounded-full border', isConnected ? 'border-rail-green/30 bg-rail-green/10' : 'border-rail-red/30 bg-rail-red/10')}>
              <Radio className={cn('h-3.5 w-3.5', isConnected ? 'text-rail-green animate-pulse-slow' : 'text-rail-red')} />
              <span className={cn('text-xs font-bold', isConnected ? 'text-rail-green' : 'text-rail-red')}>
                {isConnected ? 'LIVE FEED' : 'OFFLINE'}
              </span>
            </div>
            <button onClick={() => navigate(0)} className="btn-secondary btn-sm" title="Refresh"><RefreshCw className="h-4 w-4" /></button>
          </div>
        }
      />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <MetricCard icon={TrainIcon} label="Active trains" value={trains.length} accent="cyan" />
        <MetricCard icon={Gauge} label="Delayed trains" value={delayed} accent="amber" />
        <MetricCard icon={AlertTriangle} label="Critical delays" value={criticalDelays} accent="red" />
        <MetricCard icon={RouteIcon} label="Congested sections" value={congestedSections} accent="violet" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-3 space-y-4">
          <div className="card">
            <div className="flex items-center justify-between gap-3 px-4 py-3 border-b border-white/[0.06]">
              <h2 className="text-sm font-semibold text-gray-200">Live Train Monitor</h2>
              <div className="flex items-center gap-2">
                <div className="relative">
                  <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-gray-500" />
                  <input
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Filter trains…"
                    className="input h-8 pl-8 pr-2 text-xs w-40"
                    aria-label="Filter trains"
                  />
                </div>
                <select value={sortKey} onChange={(e) => setSortKey(e.target.value as typeof sortKey)} className="input h-8 w-auto text-xs" aria-label="Sort trains">
                  <option value="delay">Sort: Delay</option>
                  <option value="speed">Sort: Speed</option>
                  <option value="number">Sort: Number</option>
                </select>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-gray-500 border-b border-white/[0.06]">
                    <th className="table-header px-4 py-2.5">Train</th>
                    <th className="table-header px-4 py-2.5">Location</th>
                    <th className="table-header px-4 py-2.5">Speed</th>
                    <th className="table-header px-4 py-2.5">Next station</th>
                    <th className="table-header px-4 py-2.5">Delay</th>
                    <th className="table-header px-4 py-2.5">ETA</th>
                    <th className="table-header px-4 py-2.5">Source</th>
                    <th className="px-4 py-2.5" />
                  </tr>
                </thead>
                <tbody>
                  {isLoading ? (
                    <tr><td colSpan={8} className="py-6"><LoadingSkeleton className="h-24 w-full" /></td></tr>
                  ) : rows.length === 0 ? (
                    <tr><td colSpan={8}><EmptyState title="No trains match" message="Adjust filter or wait for realtime data." /></td></tr>
                  ) : rows.map(({ train, data }) => {
                    const delay = data?.current_delay_minutes ?? 0;
                    const source = data?.data_source || 'SIMULATION';
                    return (
                      <tr key={train.id} className="table-row cursor-pointer group" onClick={() => navigate(`/train/${train.train_number}`)}>
                        <td className="px-4 py-3">
                          <p className="font-mono font-bold text-gray-100">{train.train_number}</p>
                          <p className="text-xs text-gray-500">{train.train_name}</p>
                        </td>
                        <td className="px-4 py-3 text-xs text-gray-400">
                          {data?.current_position?.current_station_id ? `Stn #${data.current_position.current_station_id}` : 'En route'}
                        </td>
                        <td className="px-4 py-3 font-mono text-gray-200">
                          {data ? `${data.current_speed_kmh.toFixed(0)} km/h` : '—'}
                        </td>
                        <td className="px-4 py-3 text-xs text-gray-400">{data?.next_station?.station_name || '—'}</td>
                        <td className={cn('px-4 py-3 font-mono font-semibold', delay > 30 ? 'text-rail-red' : delay > 0 ? 'text-rail-amber' : 'text-rail-green')}>
                          {data ? (delay >= 0 ? '+' : '') + delay.toFixed(0) + 'm' : '—'}
                        </td>
                        <td className="px-4 py-3 font-mono text-gray-300">
                          {data?.eta_at_destination ? formatTime(new Date(data.eta_at_destination).toISOString()) : '—'}
                        </td>
                        <td className="px-4 py-3"><span className={cn(getDataSourceBadgeClass(source), 'text-[9px]')}>{source}</span></td>
                        <td className="px-4 py-3 text-right">
                          <ArrowRight className="h-4 w-4 text-gray-600 opacity-0 group-hover:opacity-100 transition-opacity group-hover:text-accent" />
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          <div className="card">
            <div className="px-4 py-3 border-b border-white/[0.06] flex items-center justify-between">
              <h2 className="text-sm font-semibold text-gray-200">Active Alerts</h2>
              <button onClick={() => navigate('/alerts')} className="text-xs text-accent hover:underline">Open Alert Center</button>
            </div>
            <div className="divide-y divide-white/[0.03]">
              {alerts.length === 0 ? (
                <EmptyState icon={AlertTriangle} title="No active alerts" message="The network is running normally." />
              ) : alerts.slice(0, 8).map((a) => (
                <div key={a.id} className="flex items-start gap-3 px-4 py-3 animate-slide-in">
                  <span className={cn('w-1.5 h-1.5 rounded-full mt-1.5 shrink-0', a.severity === 'CRITICAL' ? 'bg-rail-red shadow-glow-red' : a.severity === 'WARNING' ? 'bg-rail-amber' : 'bg-rail-blue')} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-300">{a.title}</p>
                    <p className="text-xs text-gray-600 mt-0.5">{a.message}</p>
                  </div>
                  <span className="text-[11px] text-gray-600 shrink-0">{formatTime(a.created_at)}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="card">
            <div className="px-4 py-3 border-b border-white/[0.06] flex items-center justify-between">
              <h2 className="text-sm font-semibold text-gray-200 flex items-center gap-2">
                <RadioTower className="h-4 w-4 text-accent" /> Co-Pilot Delay Reports
              </h2>
              {copilotReports.filter((r) => r.status === 'NEW').length > 0 && (
                <span className="badge-critical">{copilotReports.filter((r) => r.status === 'NEW').length} NEW</span>
              )}
            </div>
            <div className="divide-y divide-white/[0.03]">
              {copilotReports.length === 0 ? (
                <EmptyState icon={RadioTower} title="No co-pilot reports" message="New delay reports filed from the cab will appear here live." />
              ) : copilotReports.slice(0, 8).map((r) => (
                <div key={r.id} className="px-4 py-3 animate-slide-in">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-mono font-bold text-gray-100">#{r.id}</span>
                    <button onClick={() => navigate(`/train/${r.train_number}`)} className="font-mono text-sm text-gray-200 hover:text-accent">
                      {r.train_number}
                    </button>
                    <span className={cn(getCoPilotPriorityBadge(r.priority))}>{r.priority}</span>
                    <span className={cn(getCoPilotStatusBadge(r.status))}>{r.status}</span>
                    <span className="ml-auto text-[11px] text-gray-600">{formatDateTime(r.created_at)}</span>
                  </div>
                  <div className="mt-1.5 flex items-start gap-2">
                    <span className="badge-info shrink-0">{getCoPilotReasonLabel(r.reason)}</span>
                    <p className="text-sm text-gray-400">{r.message}</p>
                  </div>
                  <div className="mt-1.5 flex items-center gap-3 text-[11px] text-gray-600">
                    <span>Reporter: {r.reporter_call_sign || `#${r.user_id}`}</span>
                    {r.station_code && <span className="font-mono">{r.station_code}</span>}
                    {r.current_delay_minutes > 0 && <span className="font-mono text-rail-amber">+{r.current_delay_minutes} min</span>}
                    {r.status !== 'CLOSED' && (
                      <span className="ml-auto flex items-center gap-1.5">
                        {r.status === 'NEW' && (
                          <button
                            onClick={() => handleReportAction(r.id, 'acknowledge')}
                            className="p-1 rounded-md bg-rail-green/10 text-rail-green border border-rail-green/20 hover:bg-rail-green/20"
                            title="Acknowledge"
                          >
                            <Check className="h-3.5 w-3.5" />
                          </button>
                        )}
                        <button
                          onClick={() => handleReportAction(r.id, 'close')}
                          className="p-1 rounded-md bg-rail-red/10 text-rail-red border border-rail-red/20 hover:bg-rail-red/20"
                          title="Close"
                        >
                          <X className="h-3.5 w-3.5" />
                        </button>
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div className="card p-4">
            <div className="flex items-center gap-2 mb-3">
              <Zap className="h-4 w-4 text-accent" />
              <h2 className="text-sm font-semibold text-gray-200">Simulation Control</h2>
            </div>
            <div className="space-y-3 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-gray-500">Status</span>
                <span className={cn('badge', simulation?.is_running ? (simulation.is_paused ? 'badge-warning' : 'badge-success') : 'badge-neutral')}>
                  {simulation?.is_running ? (simulation.is_paused ? 'Paused' : 'Running') : 'Stopped'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-500">Speed</span>
                <span className="font-mono text-gray-200">{simulation?.speed ?? 1}x</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-500">Scenario</span>
                <span className="badge-info">{simulation?.scenario || 'NORMAL'}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-500">Active trains</span>
                <span className="font-mono text-gray-200">{simulation?.active_trains ?? 0}</span>
              </div>
              <div className="grid grid-cols-2 gap-2 pt-2">
                {!simulation?.is_running && (
                  <button onClick={() => handleSimulationControl('start')} className="btn-primary btn-sm">Start</button>
                )}
                {simulation?.is_running && !simulation?.is_paused && (
                  <button onClick={() => handleSimulationControl('pause')} className="btn-secondary btn-sm">Pause</button>
                )}
                {simulation?.is_paused && (
                  <button onClick={() => handleSimulationControl('resume')} className="btn-primary btn-sm">Resume</button>
                )}
                {simulation?.is_running && (
                  <button onClick={() => handleSimulationControl('stop')} className="btn-danger btn-sm">Stop</button>
                )}
              </div>
            </div>
          </div>

          <div className="card p-4">
            <h2 className="text-sm font-semibold text-gray-200 mb-3">Network congestion</h2>
            <div className="space-y-2.5">
              {congestion.length === 0 ? (
                <p className="text-xs text-gray-500">No congestion data available.</p>
              ) : congestion.slice(0, 6).map((c, i) => (
                <div key={i} className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-500">{c.station_id ? `Station #${c.station_id}` : `Section #${c.section_id}`}</span>
                    <span className={cn('font-semibold', c.level === 'CRITICAL' ? 'text-rail-red' : c.level === 'HIGH' ? 'text-orange-500' : c.level === 'MEDIUM' ? 'text-rail-amber' : 'text-rail-green')}>
                      {c.level}
                    </span>
                  </div>
                  <div className="h-1.5 rounded-full bg-white/5 overflow-hidden">
                    <div className={cn('h-full rounded-full transition-all', c.level === 'CRITICAL' ? 'bg-rail-red' : c.level === 'HIGH' ? 'bg-orange-500' : c.level === 'MEDIUM' ? 'bg-rail-amber' : 'bg-rail-green')}
                      style={{ width: `${Math.min(100, (c.train_count / 10) * 100)}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="card p-4">
            <h2 className="text-sm font-semibold text-gray-200 mb-3">AI ETA Engine</h2>
            <p className="text-xs text-gray-500 mb-3">Request a live prediction to demonstrate the model.</p>
            <div className="flex flex-wrap gap-2">
              {trains.slice(0, 4).map((t) => (
                <button key={t.id} onClick={async () => {
                  try {
                    const eta = await predictionApi.getETA(t.train_number, { include_explanations: true });
                    navigate(`/train/${t.train_number}`);
                    toast.success(`ETA computed: ${eta.data.predicted_arrival_delay_minutes >= 0 ? '+' : ''}${eta.data.predicted_arrival_delay_minutes.toFixed(0)} min`);
                  } catch { toast.error('Prediction request failed'); }
                }} className="btn-secondary btn-sm">
                  {t.train_number}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}