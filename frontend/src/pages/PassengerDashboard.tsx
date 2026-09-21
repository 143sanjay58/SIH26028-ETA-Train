import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { trainApi, sihEtaApi } from '../services/api';
import { Search, Train as TrainIcon, Loader2, ArrowRight, Navigation, Info, Flame, BrainCircuit, MapPin, RefreshCw } from 'lucide-react';
import { cn, getDataSourceBadgeClass, getTrainTypeLabel, formatTime, getDelayColor } from '../utils/helpers';
import { LoadingSkeleton } from '../components/ui/LoadingSkeleton';
import { EmptyState } from '../components/ui/EmptyState';
import type { Train, TrainLiveResponse, SIHETAResponse } from '../types';

const SIH_DEMO_TRAIN = '12303';

export default function PassengerDashboard() {
  const [trainNumber, setTrainNumber] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [recent, setRecent] = useState<Train[]>([]);
  const [live, setLive] = useState<Record<number, TrainLiveResponse>>({});
  const [loadingTrains, setLoadingTrains] = useState(true);
  const [sihDemo, setSihDemo] = useState<SIHETAResponse | null>(null);
  const [sihLoading, setSihLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    let mounted = true;
    const loadSih = async () => {
      try {
        const res = await sihEtaApi.getETA(SIH_DEMO_TRAIN);
        if (mounted) setSihDemo(res.data);
      } catch { /* core may be unavailable; card hides */ } finally {
        if (mounted) setSihLoading(false);
      }
    };
    loadSih();
    return () => { mounted = false; };
  }, []);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const res = await trainApi.list({ page_size: 100 });
        const list = res.data.trains || [];
        if (!mounted) return;
        setRecent(list);

        const map: Record<number, TrainLiveResponse> = {};
        await Promise.allSettled(list.map(async (t) => {
          const l = await trainApi.getLive(t.id).catch(() => null);
          if (l?.data) map[t.id] = l.data;
        }));
        if (mounted) setLive(map);
      } catch {
        /* handled by empty state */
      } finally {
        if (mounted) setLoadingTrains(false);
      }
    })();
    return () => { mounted = false; };
  }, []);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!trainNumber.trim()) return;
    setIsSearching(true);
    try {
      const response = await trainApi.getByNumber(trainNumber.trim().toUpperCase());
      navigate(`/train/${response.data.train_number}`);
    } catch {
      navigate(`/train/${trainNumber.trim().toUpperCase()}`, { state: { notFound: true } });
    } finally {
      setIsSearching(false);
    }
  };

  const recentSearches = JSON.parse(localStorage.getItem('railpulse_recent') || '[]') as string[];
  const hasRecents = recentSearches.length > 0;

  return (
    <div className="space-y-6">
      <div className="relative rounded-2xl border border-white/[0.06] bg-surface-100 overflow-hidden">
        <div className="absolute inset-0 bg-grid-pattern bg-grid opacity-50" aria-hidden="true" />
        <div className="absolute -top-24 -right-24 w-96 h-96 rounded-full bg-accent/10 blur-3xl" aria-hidden="true" />
        <div className="relative px-6 sm:px-10 py-10 sm:py-14">
          <div className="max-w-2xl">
            <p className="text-xs font-semibold uppercase tracking-[0.25em] text-accent mb-2">Track · Predict · Explain</p>
            <h1 className="text-display-lg text-gray-50">
              Where is your <span className="text-accent">train</span>?
            </h1>
            <p className="text-gray-500 mt-2 mb-6">
              Enter a train number for real-time position, AI ETA, speed and delay explanation.
            </p>

            <form onSubmit={handleSearch} className="flex gap-2 max-w-lg" role="search">
              <div className="relative flex-1">
                <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
                <input
                  type="text"
                  value={trainNumber}
                  onChange={(e) => setTrainNumber(e.target.value.toUpperCase())}
                  placeholder="Enter train number or name (e.g. 12627)"
                  className="input pl-10 h-12 text-base bg-surface-200/90 font-mono"
                  required
                  autoFocus
                  aria-label="Train number or name"
                />
              </div>
              <button type="submit" disabled={isSearching || !trainNumber.trim()} className="btn-primary px-6 h-12">
                {isSearching ? <Loader2 className="h-5 w-5 animate-spin" /> : <Search className="h-5 w-5" />}
                <span className="hidden sm:inline">Track Train</span>
              </button>
            </form>

            {hasRecents && (
              <div className="flex flex-wrap items-center gap-1.5 mt-4 text-sm">
                <span className="text-gray-600 text-xs uppercase tracking-wider">Recent:</span>
                {recentSearches.slice(0, 4).map((r) => (
                  <button
                    key={r}
                    onClick={() => navigate(`/train/${r}`)}
                    className="px-2.5 py-1 rounded-md bg-white/[0.05] border border-white/10 font-mono text-xs text-gray-300 hover:border-accent/40 hover:text-accent transition-colors"
                  >
                    {r}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-display-sm text-gray-100 flex items-center gap-2">
            <Flame className="h-5 w-5 text-rail-amber" />
            Running trains
          </h2>
          <span className="text-xs text-gray-600">Live network snapshot</span>
        </div>

        {loadingTrains ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {Array.from({ length: 6 }).map((_, i) => <LoadingSkeleton key={i} className="h-28" />)}
          </div>
        ) : recent.length === 0 ? (
          <div className="card">
            <EmptyState icon={TrainIcon} title="No running trains" message="Waiting for realtime train data from the network." />
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {recent.slice(0, 9).map((train) => {
              const d = live[train.id];
              const speed = d?.current_speed_kmh ?? 0;
              const delay = d?.current_delay_minutes ?? 0;
              const liveStatus = d ? (speed > 0 ? 'MOVING' : 'STOPPED') : train.status.replace(/_/g, ' ');
              return (
                <button
                  key={train.id}
                  onClick={() => navigate(`/train/${train.train_number}`)}
                  className="group card p-4 text-left hover:border-white/15 hover:bg-surface-200 transition-all duration-200 hover:shadow-glow-sm"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2.5 min-w-0">
                      <div className="w-9 h-9 rounded-lg bg-accent/10 border border-accent/20 flex items-center justify-center shrink-0">
                        <TrainIcon className="h-4 w-4 text-accent" />
                      </div>
                      <div className="min-w-0">
                        <p className="font-mono font-bold text-gray-100 text-sm">{train.train_number}</p>
                        <p className="text-sm text-gray-400 truncate">{train.train_name}</p>
                      </div>
                    </div>
                    <span className={cn('shrink-0', d && speed > 0 ? 'badge-live' : d ? 'badge-warning' : 'badge-neutral')}>{liveStatus}</span>
                  </div>
                  <div className="flex items-center gap-1.5 mt-3 text-xs text-gray-500">
                    <Navigation className="h-3 w-3" />
                    <span className="truncate">{train.origin_station?.name || '—'}</span>
                    <ArrowRight className="h-3 w-3 shrink-0 text-gray-700" />
                    <span className="truncate">{train.destination_station?.name || '—'}</span>
                  </div>
                  <div className="flex items-center justify-between mt-2">
                    <span className="text-[11px] text-gray-600">{getTrainTypeLabel(train.train_type)} · {train.total_distance_km} km</span>
                    <span className="flex items-center gap-2">
                      {d && delay > 0 && (
                        <span className="text-[11px] font-semibold text-rail-amber">+{delay.toFixed(0)} min</span>
                      )}
                      <span className={cn('text-[9px]', getDataSourceBadgeClass(d?.data_source ?? 'SIMULATION'))}>{d?.data_source ?? 'ESTIMATED'}</span>
                      <span className="text-[11px] font-semibold text-accent opacity-0 group-hover:opacity-100 transition-opacity">View →</span>
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </div>

      <div className="card p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold text-gray-200 flex items-center gap-2">
            <BrainCircuit className="h-4 w-4 text-accent" />
            SIH26028 ETA Demo — Train {SIH_DEMO_TRAIN}
          </h2>
          <button
            onClick={async () => {
              setSihLoading(true);
              try {
                const res = await sihEtaApi.getETA(SIH_DEMO_TRAIN);
                setSihDemo(res.data);
              } catch { /* no-op */ } finally {
                setSihLoading(false);
              }
            }}
            className="btn-secondary btn-sm"
            title="Recompute SIH ETA"
          >
            <RefreshCw className={cn('h-3.5 w-3.5', sihLoading && 'animate-spin')} /> Refresh
          </button>
        </div>

        {sihDemo ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-1">
              <p className="text-xs text-gray-500 uppercase tracking-wider">Predicted arrival</p>
              <p className="font-mono text-3xl font-bold text-gray-50 tabular-nums mt-1">
                {formatTime(new Date(sihDemo.predicted_arrival_time).toISOString())}
              </p>
              <p className="font-mono text-xs text-gray-500 mt-1">{sihDemo.destination_station_name || sihDemo.destination_station}</p>
              <div className="flex items-center gap-2 mt-2">
                <span className={cn('font-mono font-bold', getDelayColor(sihDemo.predicted_arrival_delay_minutes))}>
                  {sihDemo.predicted_arrival_delay_minutes >= 0 ? '+' : ''}{sihDemo.predicted_arrival_delay_minutes.toFixed(0)} min
                </span>
                <span className={cn('text-[9px]', getDataSourceBadgeClass(sihDemo.data_source))}>{sihDemo.data_source}</span>
              </div>
            </div>
            <div className="md:col-span-2">
              <p className="text-[10px] uppercase tracking-widest text-gray-600 mb-2 flex items-center gap-1.5">
                <MapPin className="h-3 w-3" /> Upcoming stations ({sihDemo.upcoming_station_count})
              </p>
              <div className="space-y-1.5">
                {sihDemo.upcoming_stations.slice(0, 5).map((s) => (
                  <div key={s.station_code} className="flex items-center justify-between text-sm">
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
          </div>
        ) : sihLoading ? (
          <LoadingSkeleton className="h-24" />
        ) : (
          <p className="text-sm text-gray-500">
            The embedded LightGBM ETA core is not available right now. Open a train to see per-train predictions when the core responds.
          </p>
        )}
      </div>

      <div className="card p-4 flex items-start gap-3">
        <Info className="h-5 w-5 text-rail-blue shrink-0 mt-0.5" />
        <p className="text-sm text-gray-500">
          This platform currently presents <strong className="text-gray-300">SIMULATION data</strong> for demonstration.
          Official railway live-data integration requires authorized access. Train positions, speeds and ETAs carry
          source badges — never claim simulated values as live railway data.
        </p>
      </div>
    </div>
  );
}