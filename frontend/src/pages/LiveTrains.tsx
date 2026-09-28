import { useState, useEffect, useMemo, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { trainApi, stationApi } from '../services/api';
import { loadTrainRoute } from '../utils/trainRoute';
import { useWebSocket } from '../contexts/WebSocketContext';
import { Train as TrainIcon, Search, MapPin, ArrowRight, LocateFixed } from 'lucide-react';
import { cn, getDataSourceBadgeClass, getTrainTypeLabel } from '../utils/helpers';
import { SectionHeader } from '../components/ui/SectionHeader';
import { EmptyState } from '../components/ui/EmptyState';
import { LoadingSkeleton } from '../components/ui/LoadingSkeleton';
import { TrainPicker, type TrainOption } from '../components/train/TrainPicker';
import { RailwayMap } from '../components/train/RailwayMap';
import type { Train, Station, TrainLiveResponse, CatalogueTrain } from '../types';

function stationCoord(s: Station): { lat: number; lng: number } | null {
  if (s?.code && Number.isFinite(s.latitude) && Number.isFinite(s.longitude)) {
    return { lat: s.latitude, lng: s.longitude };
  }
  return null;
}

export default function LiveTrains() {
  const navigate = useNavigate();
  const { subscribeToTrain, unsubscribeFromTrain, onTrainUpdate } = useWebSocket();
  const [trains, setTrains] = useState<Train[]>([]);
  const [live, setLive] = useState<Record<number, TrainLiveResponse>>({});
  const [stations, setStations] = useState<Station[]>([]);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [catalogueResult, setCatalogueResult] = useState<CatalogueTrain | null>(null);
  const [catalogueSearching, setCatalogueSearching] = useState(false);

  const [selected, setSelected] = useState<TrainOption | null>(null);
  const [selectedLive, setSelectedLive] = useState<TrainLiveResponse | null>(null);
  const [routePoints, setRoutePoints] = useState<[number, number][]>([]);
  const [routeStatus, setRouteStatus] = useState<'idle' | 'loading' | 'loaded' | 'error'>('idle');
  const [positionStatus, setPositionStatus] = useState<'idle' | 'available' | 'unavailable'>('idle');

  const coordCacheRef = useRef<Map<string, { lat: number; lng: number }>>(new Map());
  const routeCacheRef = useRef<Map<string, [number, number][]>>(new Map());

  useEffect(() => {
    for (const s of stations) {
      const c = stationCoord(s);
      if (c) coordCacheRef.current.set(s.code.toUpperCase(), c);
    }
  }, [stations]);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const [trainRes, stationRes] = await Promise.all([
          trainApi.list({ page_size: 100 }),
          stationApi.list({ page_size: 100 }).catch(() => null),
        ]);
        const list = trainRes.data.trains || [];
        if (!mounted) return;
        setTrains(list);
        const raw = stationRes?.data as unknown;
        const stList = Array.isArray(raw) ? raw : (raw as { stations?: Station[] } | undefined)?.stations ?? [];
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

  useEffect(() => {
    const q = query.trim();
    if (q.length < 3) {
      setCatalogueResult(null);
      setCatalogueSearching(false);
      return;
    }
    setCatalogueSearching(true);
    let cancelled = false;
    const timer = setTimeout(() => {
      trainApi
        .getByNumber(q)
        .then((res) => {
          if (cancelled) return;
          const data = res.data;
          setCatalogueResult(
            'source' in data && (data as CatalogueTrain).source === 'SIH_CATALOGUE' ? (data as CatalogueTrain) : null
          );
        })
        .catch(() => { if (!cancelled) setCatalogueResult(null); })
        .finally(() => { if (!cancelled) setCatalogueSearching(false); });
    }, 300);
    return () => { cancelled = true; clearTimeout(timer); };
  }, [query]);

  const lookupCoord = async (code: string): Promise<{ lat: number; lng: number } | null> => {
    const upper = code.trim().toUpperCase();
    const cached = coordCacheRef.current.get(upper);
    if (cached) return cached;
    try {
      const res = await stationApi.getByCode(code);
      const c = stationCoord(res.data);
      if (c) {
        coordCacheRef.current.set(upper, c);
        return c;
      }
    } catch {
      // station not in the database
    }
    return null;
  };

  useEffect(() => {
    if (!selected) {
      setRoutePoints([]);
      setSelectedLive(null);
      setRouteStatus('idle');
      setPositionStatus('idle');
      return;
    }

    let cancelled = false;
    const cacheKey = `${selected.source}:${selected.train_number}`;

    const loadRoute = async () => {
      const cachedPts = routeCacheRef.current.get(cacheKey);
      if (cachedPts) {
        if (!cancelled) {
          setRoutePoints(cachedPts);
          setRouteStatus('loaded');
        }
        return;
      }
      try {
        const order = await loadTrainRoute(selected.train_number, selected.trainId);
        const points: [number, number][] = [];
        const seen = new Set<string>();
        for (const stop of order) {
          const c = await lookupCoord(stop.code);
          if (!c) continue;
          const key = `${c.lat.toFixed(3)},${c.lng.toFixed(3)}`;
          if (seen.has(key)) continue;
          seen.add(key);
          points.push([c.lat, c.lng]);
        }
        if (cancelled) return;
        if (points.length >= 2) {
          routeCacheRef.current.set(cacheKey, points);
          setRoutePoints(points);
          setRouteStatus('loaded');
        } else {
          setRouteStatus('error');
        }
      } catch {
        if (!cancelled) setRouteStatus('error');
      }
    };

    const loadPosition = async () => {
      if (selected.trainId == null) {
        if (!cancelled) setPositionStatus('unavailable');
        return;
      }
      const res = await trainApi.getLive(selected.trainId).catch(() => null);
      if (cancelled) return;
      if (res?.data) {
        setSelectedLive(res.data);
        setPositionStatus('available');
      } else {
        setPositionStatus('unavailable');
      }
    };

    setRouteStatus('loading');
    setRoutePoints([]);
    setSelectedLive(null);
    setPositionStatus('idle');

    void loadRoute();
    void loadPosition();

    return () => { cancelled = true; };
  }, [selected]);

  useEffect(() => {
    const trainId = selected?.trainId;
    if (!trainId) return;

    const refreshLive = () => {
      trainApi.getLive(trainId).then((res) => {
        if (res?.data) setSelectedLive(res.data);
      }).catch(() => { /* keep last known position */ });
    };

    const unsub = onTrainUpdate((data) => {
      if (data && typeof data === 'object' && 'train_id' in data && (data as { train_id: number }).train_id === trainId) {
        refreshLive();
      }
    });

    subscribeToTrain(trainId);
    const interval = setInterval(refreshLive, 15000);

    return () => {
      unsub();
      clearInterval(interval);
      unsubscribeFromTrain(trainId);
    };
  }, [selected?.trainId, subscribeToTrain, unsubscribeFromTrain, onTrainUpdate]);

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
      <SectionHeader title="Live Trains" subtitle="Track one selected train in realtime" />

      <div className="card p-5">
        <div className="flex items-center justify-between gap-3 mb-3">
          <h2 className="text-sm font-semibold text-gray-200">Train tracking</h2>
          <span className="text-xs text-gray-600">{positioned.length} positioned trains</span>
        </div>

        <TrainPicker
          value={selected}
          onChange={setSelected}
          placeholder="Search and select a train to track…"
          hint="Select a train to show its route and current position. Only the selected train is tracked."
        />

        <div className="relative mt-4">
          <RailwayMap
            stations={selected ? stations : []}
            position={selectedLive?.current_position}
            route={routePoints.length >= 2 ? routePoints : undefined}
          />

          {!selected && (
            <div className="absolute inset-0 z-20 flex flex-col items-center justify-center gap-2 pointer-events-none">
              <LocateFixed className="h-8 w-8 text-gray-600" />
              <p className="text-sm font-medium text-gray-400">Select a train to track</p>
            </div>
          )}

          {selected && routeStatus === 'loading' && (
            <div className="absolute top-3 left-1/2 -translate-x-1/2 z-20 card px-4 py-2 bg-surface-100/95 backdrop-blur-sm">
              <span className="text-xs text-gray-400">Loading route…</span>
            </div>
          )}

          {selected && routeStatus === 'error' && routePoints.length < 2 && (
            <div className="absolute top-3 left-1/2 -translate-x-1/2 z-20 card px-4 py-2 bg-surface-100/95 backdrop-blur-sm">
              <span className="text-xs text-rail-red">Route information unavailable for this train.</span>
            </div>
          )}

          {selected && positionStatus === 'unavailable' && (
            <div className="absolute bottom-3 right-3 z-20 card px-4 py-2 bg-surface-100/95 backdrop-blur-sm">
              <span className="text-xs text-gray-400">Live position unavailable.</span>
            </div>
          )}
        </div>

        {selected && (
          <div className="mt-4 space-y-3">
            <div className="flex flex-wrap items-center gap-2">
              <span className="px-2.5 py-1 rounded-lg border border-white/10 bg-surface-200/60 text-xs">
                <span className="text-gray-500">Tracking train </span>
                <span className="font-mono font-bold text-gray-100">{selected.train_number}</span>
              </span>
              {selectedLive && (
                <>
                  <span className={cn('px-2.5 py-1 rounded-lg border text-xs font-mono',
                    selectedLive.current_delay_minutes > 30 ? 'border-rail-red/30 bg-rail-red/10 text-rail-red'
                      : selectedLive.current_delay_minutes > 0 ? 'border-rail-amber/30 bg-rail-amber/10 text-rail-amber'
                        : 'border-rail-green/30 bg-rail-green/10 text-rail-green')}>
                    {selectedLive.current_delay_minutes > 0 ? '+' : ''}{selectedLive.current_delay_minutes.toFixed(0)} min
                  </span>
                  <span className="px-2.5 py-1 rounded-lg border border-white/10 bg-surface-200/60 text-xs font-mono text-gray-300">
                    {selectedLive.current_speed_kmh.toFixed(0)} km/h
                  </span>
                  <span className="px-2.5 py-1 rounded-lg border border-white/10 bg-surface-200/60 text-xs text-gray-300">
                    Next station: {selectedLive.next_station?.station_name || '—'}
                  </span>
                </>
              )}
              {!selectedLive && positionStatus === 'unavailable' && (
                <span className="px-2.5 py-1 rounded-lg border border-white/10 bg-surface-200/60 text-xs text-gray-500">
                  No live position for catalogue train
                </span>
              )}
            </div>
          </div>
        )}
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
          ) : (
            <>
              {filtered.map((t) => {
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
              {catalogueResult && (
                <button key={`catalogue-${catalogueResult.train_number}`} onClick={() => navigate(`/train/${catalogueResult.train_number}`)}
                  className="card p-4 text-left hover:border-white/15 hover:bg-surface-200 transition-all duration-200">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <p className="font-mono font-bold text-gray-100">{catalogueResult.train_number}</p>
                      <p className="text-sm text-gray-400 truncate">{catalogueResult.train_name || catalogueResult.train_number}</p>
                    </div>
                    <div className="text-right shrink-0">
                      <span className="badge-sih-eta">SIH CATALOGUE</span>
                      <span className="block mt-1 text-[9px] text-gray-500">{catalogueResult.route_segments} segments</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-1.5 mt-3 text-xs text-gray-500">
                    <MapPin className="h-3 w-3" />
                    {catalogueResult.origin_station_name || catalogueResult.origin_station}
                    <ArrowRight className="h-3 w-3" />
                    {catalogueResult.destination_station_name || catalogueResult.destination_station}
                  </div>
                </button>
              )}
              {filtered.length === 0 && !catalogueResult && !catalogueSearching && (
                <div className="col-span-full"><EmptyState icon={TrainIcon} title={query.trim() ? 'No train found' : 'No trains found'} /></div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}