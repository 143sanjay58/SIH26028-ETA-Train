import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { trainApi, stationApi } from '../services/api';
import { Train as TrainIcon, Search, MapPin } from 'lucide-react';
import { cn, getDataSourceBadgeClass, getTrainTypeLabel } from '../utils/helpers';
import { SectionHeader } from '../components/ui/SectionHeader';
import { EmptyState } from '../components/ui/EmptyState';
import { LoadingSkeleton } from '../components/ui/LoadingSkeleton';
import type { Train, Station, TrainLiveResponse } from '../types';
import { RailwayMap } from '../components/train/RailwayMap';

export default function LiveTrains() {
  const navigate = useNavigate();
  const [trains, setTrains] = useState<Train[]>([]);
  const [live, setLive] = useState<Record<number, TrainLiveResponse>>({});
  const [stations, setStations] = useState<Station[]>([]);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const [trainRes, stationRes] = await Promise.all([
          trainApi.list({ page_size: 100 }),
          stationApi.list({ page_size: 200 }).catch(() => null),
        ]);
        const list = trainRes.data.trains || [];
        if (!mounted) return;
        setTrains(list);
        const raw = stationRes?.data as unknown;
        const stList = Array.isArray(raw) ? raw : (raw as { items?: Station[] } | undefined)?.items ?? [];
        setStations(stList as Station[]);

        const map: Record<number, TrainLiveResponse> = {};
        await Promise.allSettled(list.map(async (t) => {
          const l = await trainApi.getLive(t.id).catch(() => null);
          if (l?.data) map[t.id] = l.data;
        }));
        if (mounted) setLive(map);
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => { mounted = false; };
  }, []);

  const filtered = useMemo(() =>
    trains.filter((t) => {
      const q = query.trim().toLowerCase();
      if (!q) return true;
      return t.train_number.toLowerCase().includes(q) || t.train_name.toLowerCase().includes(q);
    }),
    [trains, query]
  );

  const positioned = Object.values(live).filter((l) => l.current_position).slice(0, 20);

  return (
    <div className="space-y-6">
      <SectionHeader title="Live Trains" subtitle="All running trains with realtime positions" />

      <div className="card p-5">
        <div className="flex items-center justify-between gap-3 mb-3">
          <h2 className="text-sm font-semibold text-gray-200">Network view</h2>
          <span className="text-xs text-gray-600">{positioned.length} positioned trains</span>
        </div>
        <RailwayMap stations={stations} position={positioned[0]?.current_position} />
      </div>

      <div className="card">
        <div className="flex items-center justify-between gap-3 px-4 py-3 border-b border-white/[0.06]">
          <h2 className="text-sm font-semibold text-gray-200">Fleet</h2>
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-gray-500" />
            <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search…" className="input h-8 pl-8 w-44 text-sm" aria-label="Search trains" />
          </div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 p-4">
          {loading ? (
            Array.from({ length: 6 }).map((_, i) => <LoadingSkeleton key={i} className="h-32" />)
          ) : filtered.length === 0 ? (
            <div className="col-span-full"><EmptyState icon={TrainIcon} title="No trains found" /></div>
          ) : filtered.map((t) => {
            const d = live[t.id];
            const delay = d?.current_delay_minutes ?? 0;
            const source = d?.data_source ?? 'SIMULATION';
            return (
              <button key={t.id} onClick={() => navigate(`/train/${t.train_number}`)}
                className="card p-4 text-left hover:border-white/15 hover:bg-surface-200 transition-all duration-200">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="font-mono font-bold text-gray-100">{t.train_number}</p>
                    <p className="text-sm text-gray-400 truncate">{t.train_name}</p>
                  </div>
                  <div className="text-right shrink-0">
                    <span className={cn(delay > 0 ? 'badge-warning' : 'badge-success')}>{delay > 0 ? `${delay.toFixed(0)}m` : 'On time'}</span>
                    <span className={cn('block mt-1 text-[9px]', getDataSourceBadgeClass(source))}>{source}</span>
                  </div>
                </div>
                <div className="flex items-center gap-1.5 mt-3 text-xs text-gray-500">
                  <MapPin className="h-3 w-3" />
                  {d?.next_station?.station_name || 'En route'}
                  <span className="ml-auto text-[11px] text-gray-600">{getTrainTypeLabel(t.train_type)}</span>
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}