import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { trainApi, stationApi } from '../services/api';
import { useWebSocket } from '../contexts/WebSocketContext';
import { MapContainer, TileLayer, CircleMarker, Polyline, Tooltip, Popup } from 'react-leaflet';
import { Navigation, Radar, RefreshCw } from 'lucide-react';
import { cn } from '../utils/helpers';
import { SectionHeader } from '../components/ui/SectionHeader';
import { LoadingSkeleton } from '../components/ui/LoadingSkeleton';
import type { Station, TrainLiveResponse } from '../types';

export default function RailwayMapPage() {
  const navigate = useNavigate();
  const { isConnected, onTrainUpdate } = useWebSocket();
  const [stops, setStops] = useState<Record<number, TrainLiveResponse>>({});
  const [stations, setStations] = useState<Station[]>([]);
  const [loading, setLoading] = useState(true);
  const [focusId, setFocusId] = useState<number | null>(null);

  const fetchData = async () => {
    try {
      const [trainRes, stationRes] = await Promise.all([
        trainApi.list({ page_size: 100 }),
        stationApi.list({ page_size: 200 }).catch(() => null),
      ]);
      const list = trainRes.data.trains || [];
      const raw = stationRes?.data as unknown;
      const stList = Array.isArray(raw) ? raw : (raw as { items?: Station[] } | undefined)?.items ?? [];
      setStations(stList as Station[]);

      const map: Record<number, TrainLiveResponse> = {};
      await Promise.allSettled(list.map(async (t) => {
        const l = await trainApi.getLive(t.id).catch(() => null);
        if (l?.data?.current_position) map[t.id] = l.data;
      }));
      setStops(map);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const unsub = onTrainUpdate(() => fetchData());
    return () => unsub();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const positioned = useMemo(() => Object.values(stops).filter((s) => s.current_position), [stops]);
  const stationPoints = stations.filter((s) => Number.isFinite(s.latitude) && Number.isFinite(s.longitude));
  const routePoints = stationPoints.map((s) => [s.latitude, s.longitude] as [number, number]);
  const focused = stops[focusId ?? -1];

  return (
    <div className="space-y-5">
      <SectionHeader
        title="Railway Map"
        subtitle="Network view with live train positions"
        right={
          <span className={cn('flex items-center gap-1.5 px-3 py-1.5 rounded-full border',
            isConnected ? 'border-rail-green/30 bg-rail-green/10' : 'border-rail-red/30 bg-rail-red/10')}>
            <Radar className={cn('h-3.5 w-3.5', isConnected ? 'text-rail-green animate-pulse-slow' : 'text-rail-red')} />
            <span className={cn('text-xs font-bold', isConnected ? 'text-rail-green' : 'text-rail-red')}>
              {isConnected ? 'LIVE' : 'OFFLINE'}
            </span>
          </span>
        }
      />

      {loading ? (
        <LoadingSkeleton className="h-[480px]" />
      ) : (
        <div className="relative h-[520px] rounded-xl overflow-hidden border border-white/[0.06]">
          <MapContainer center={[13.5, 78.5]} zoom={7} scrollWheelZoom={false} className="h-full w-full">
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/">CARTO</a>'
              url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            />
            {routePoints.length > 1 && (
              <Polyline positions={routePoints} pathOptions={{ color: 'rgba(0,212,255,0.25)', weight: 1.5 }} />
            )}
            {stationPoints.map((s) => (
              <CircleMarker
                key={s.id}
                center={[s.latitude, s.longitude]}
                radius={4}
                pathOptions={{ color: '#00d4ff', fillColor: 'rgba(0,212,255,0.4)', fillOpacity: 0.5, weight: 1 }}
              >
                <Tooltip direction="top" opacity={1}><span>{s.name} ({s.code})</span></Tooltip>
              </CircleMarker>
            ))}
            {positioned.map((l) => {
              const p = l.current_position!;
              const delay = l.current_delay_minutes;
              return (
                <CircleMarker
                  key={l.train.id}
                  center={[p.latitude, p.longitude]}
                  radius={delay > 30 ? 12 : delay > 0 ? 9 : 8}
                  pathOptions={{
                    color: delay > 30 ? '#ef4444' : delay > 0 ? '#f59e0b' : '#10b981',
                    fillColor: delay > 30 ? '#ef4444' : delay > 0 ? '#f59e0b' : '#10b981',
                    fillOpacity: 0.85, weight: 2,
                  }}
                  eventHandlers={{ click: () => setFocusId(l.train.id) }}
                >
                  <Popup>
                    <div className="min-w-[140px]">
                      <p className="font-mono text-xs font-bold">{l.train.train_number} — {l.train.train_name}</p>
                      <p className="text-xs mt-1">{delay >= 0 ? '+' : ''}{delay.toFixed(0)} min · {l.current_speed_kmh.toFixed(0)} km/h</p>
                      <button className="text-xs text-accent mt-1 underline" onClick={() => navigate(`/train/${l.train.train_number}`)}>Open train →</button>
                    </div>
                  </Popup>
                </CircleMarker>
              );
            })}
          </MapContainer>

          <div className="absolute top-3 left-3 card px-3 py-2 flex items-center gap-3 bg-surface-100/90 backdrop-blur-sm">
            <span className="flex items-center gap-1.5 text-[11px] text-gray-400"><span className="w-2 h-2 rounded-full bg-rail-green" /> On time</span>
            <span className="flex items-center gap-1.5 text-[11px] text-gray-400"><span className="w-2 h-2 rounded-full bg-rail-amber" /> Delayed</span>
            <span className="flex items-center gap-1.5 text-[11px] text-gray-400"><span className="w-2 h-2 rounded-full bg-rail-red" /> Critical</span>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="card p-4 lg:col-span-2">
          <h2 className="text-sm font-semibold text-gray-200 mb-3">Positioned trains</h2>
          {positioned.length === 0 ? (
            <p className="text-sm text-gray-500 py-6 text-center">No positioned trains. Start the simulation to populate positions.</p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {positioned.slice(0, 24).map((l) => (
                <button key={l.train.id} onClick={() => setFocusId(l.train.id)}
                  className={cn('px-2.5 py-1.5 rounded-lg border font-mono text-xs transition-all',
                    focusId === l.train.id ? 'border-accent/50 bg-accent/10 text-accent' : 'border-white/10 text-gray-300 hover:border-white/25')}>
                  {l.train.train_number}
                  <span className={cn('ml-2', l.current_delay_minutes > 30 ? 'text-rail-red' : l.current_delay_minutes > 0 ? 'text-rail-amber' : 'text-rail-green')}>
                    {l.current_delay_minutes >= 0 ? '+' : ''}{l.current_delay_minutes.toFixed(0)}m
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="card p-4">
          <div className="flex items-center gap-2 mb-3">
            <Navigation className="h-4 w-4 text-accent" />
            <h2 className="text-sm font-semibold text-gray-200">Focused train</h2>
          </div>
          {focused?.current_position ? (
            <div className="space-y-2 text-sm">
              <p className="font-mono font-bold text-gray-100">{focused.train.train_number} — {focused.train.train_name}</p>
              <p className="text-xs text-gray-500 font-mono">
                {focused.current_position.latitude.toFixed(4)}, {focused.current_position.longitude.toFixed(4)}
              </p>
              <div className="flex justify-between text-xs"><span className="text-gray-500">Speed</span><span className="font-mono text-gray-300">{focused.current_speed_kmh.toFixed(0)} km/h</span></div>
              <div className="flex justify-between text-xs"><span className="text-gray-500">Delay</span><span className="font-mono text-rail-amber">{focused.current_delay_minutes >= 0 ? '+' : ''}{focused.current_delay_minutes.toFixed(0)}m</span></div>
              <div className="flex justify-between text-xs"><span className="text-gray-500">Next station</span><span className="text-gray-300">{focused.next_station?.station_name || '—'}</span></div>
              <button onClick={() => navigate(`/train/${focused.train.train_number}`)} className="btn-secondary btn-sm w-full mt-2">
                Open live view <RefreshCw className="h-3 w-3" />
              </button>
            </div>
          ) : (
            <p className="text-sm text-gray-500">Select a train marker on the map.</p>
          )}
        </div>
      </div>
    </div>
  );
}