import { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { trainApi, predictionApi, weatherApi, alertApi, stationApi, sihEtaApi } from '../services/api';
import { useWebSocket } from '../contexts/WebSocketContext';
import {
  ArrowLeft,
  Gauge,
  Cloud,
  AlertTriangle,
  Route as RouteIcon,
  Layers,
  SearchX,
  RefreshCw,
} from 'lucide-react';
import { cn, formatTime } from '../utils/helpers';
import { SectionHeader } from '../components/ui/SectionHeader';
import { StatusBadge, SourceBadge } from '../components/ui/StatusBadge';
import { ETACard } from '../components/train/ETACard';
import { SIHETACard } from '../components/train/SIHETACard';
import { SpeedGauge } from '../components/ui/SpeedGauge';
import { RailwayMap } from '../components/train/RailwayMap';
import { StationTimeline } from '../components/train/StationTimeline';
import { DelayExplanation } from '../components/train/DelayExplanation';
import { LoadingSkeleton } from '../components/ui/LoadingSkeleton';
import { EmptyState } from '../components/ui/EmptyState';
import { ErrorState } from '../components/ui/ErrorState';
import type { TrainLiveResponse, ETAResponse, WeatherResponse, Alert, Train, TrainSchedule, Station, SIHETAResponse } from '../types';

function useStateExport(trainNumber: string) {
  useEffect(() => {
    try {
      const recents = JSON.parse(localStorage.getItem('railpulse_recent') || '[]') as string[];
      const next = [trainNumber, ...recents.filter((r) => r !== trainNumber)].slice(0, 5);
      localStorage.setItem('railpulse_recent', JSON.stringify(next));
    } catch { /* ignore */ }
  }, [trainNumber]);
}

export default function TrainDetail() {
  const { trainNumber } = useParams<{ trainNumber: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const wasNotFound = (location.state as { notFound?: boolean } | null)?.notFound;
  const { subscribeToTrain, unsubscribeFromTrain, onTrainUpdate, onEtaUpdate, isConnected } = useWebSocket();

  const [train, setTrain] = useState<Train | null>(null);
  const [liveData, setLiveData] = useState<TrainLiveResponse | null>(null);
  const [etaData, setEtaData] = useState<ETAResponse | null>(null);
  const [sihEta, setSihEta] = useState<SIHETAResponse | null>(null);
  const [sihEtaLoading, setSihEtaLoading] = useState(false);
  const [route, setRoute] = useState<TrainSchedule[]>([]);
  const [weather, setWeather] = useState<WeatherResponse | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [stations, setStations] = useState<Station[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate] = useState(new Date());

  useStateExport(trainNumber || '');

  useEffect(() => {
    if (!trainNumber) return;

    let cancelled = false;
    let trainId = 0;

    const fetchAll = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const tr = await trainApi.getByNumber(trainNumber);
        if (cancelled) return;
        trainId = tr.data.id;
        setTrain(tr.data);
        subscribeToTrain(trainId);

        const routeRes = await trainApi.getRoute(trainId).catch(() => null);
        const positions = trainApi.getPositions(trainId, { limit: 1 }).then((r) => r.data).catch(() => []);

        const [liveRes, etaRes, weatherRes, alertsRes, stationRes, pos] = await Promise.all([
          trainApi.getLive(trainId).catch(() => null),
          predictionApi.getETA(trainNumber, { include_explanations: true, include_uncertainty: true }).catch(() => null),
          weatherApi.getRouteWeather(trainId, 5).catch(() => null),
          alertApi.list({ train_id: trainId, active_only: true }).catch(() => null),
          stationApi.list({ page_size: 200 }).catch(() => null),
          positions,
        ]);

        if (cancelled) return;
        if (liveRes?.data) setLiveData(liveRes.data);
        if (etaRes?.data) setEtaData(etaRes.data);
        if (routeRes?.data) {
          const items = Array.isArray(routeRes.data) ? routeRes.data : (routeRes.data as { items?: TrainSchedule[] }).items || [];
          setRoute(items);
        }
        if (weatherRes?.data) setWeather(Array.isArray(weatherRes.data) ? weatherRes.data[0] || null : weatherRes.data);
        if (alertsRes?.data) setAlerts(alertsRes.data);
        if (stationRes?.data) setStations(Array.isArray(stationRes.data) ? stationRes.data : stationRes.data.items || []);
        if (pos && pos[0] && !liveRes?.data) {
          setLiveData({ train: tr.data, current_position: pos[0], current_speed_kmh: pos[0].speed_kmh, average_speed_kmh: pos[0].speed_kmh, distance_travelled_km: pos[0].distance_travelled_km, distance_remaining_km: 0, current_delay_minutes: pos[0].delay_minutes, delay_trend: 'STABLE', data_source: pos[0].source } as TrainLiveResponse);
        }

        setSihEtaLoading(true);
        void sihEtaApi.getETA(trainNumber).then((res) => {
          if (!cancelled) setSihEta(res.data);
        }).catch(() => {
          if (!cancelled) setSihEta(null);
        }).finally(() => {
          if (!cancelled) setSihEtaLoading(false);
        });
      } catch {
        if (!cancelled) setError('Train not found. Check the number and try again.');
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    };

    fetchAll();

    const unsub = onTrainUpdate((data) => {
      if (data && typeof data === 'object' && 'train_id' in data && (data as { train_id: number }).train_id === trainId) {
        fetchAll();
      }
    });

    const unsubEta = onEtaUpdate((data) => {
      if (data && typeof data === 'object' && 'train_id' in data && (data as { train_id: number }).train_id === trainId) {
        fetchAll();
      }
    });

    return () => {
      cancelled = true;
      if (trainId) unsubscribeFromTrain(trainId);
      unsub();
      unsubEta();
    };
  }, [trainNumber]);

  const timelineStops = useMemo(() => {
    if (!route.length) return [];
    const currentSeq = liveData?.current_position?.current_station_id;
    const nextSeq = liveData?.next_station?.sequence;
    return route.map((s, i) => ({
      schedule: s,
      isCurrent: currentSeq !== undefined && currentSeq !== null && s.station_id === currentSeq,
      isNext: nextSeq !== undefined && nextSeq !== null && s.sequence === nextSeq,
      delayMin: i >= (nextSeq ?? 0) - 1 ? liveData?.current_delay_minutes ?? 0 : 0,
    }));
  }, [route, liveData]);

  if (isLoading) {
    return (
      <div className="space-y-5" role="status" aria-label="Loading train data">
        <LoadingSkeleton className="h-7 w-64" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <LoadingSkeleton className="h-56" />
          <LoadingSkeleton className="h-56" />
          <LoadingSkeleton className="h-56" />
        </div>
        <LoadingSkeleton className="h-96" />
      </div>
    );
  }

  if (error || !train) {
    if (wasNotFound) {
      return (
        <div className="card p-10 flex flex-col items-center text-center">
          <SearchX className="h-12 w-12 text-gray-600 mb-4" />
          <h2 className="text-lg font-semibold text-gray-200">Train not found</h2>
          <p className="text-sm text-gray-500 mt-1 mb-5">We could not find train {trainNumber}. Check the number and try again.</p>
          <button onClick={() => navigate('/')} className="btn-primary">Track another train</button>
        </div>
      );
    }
    return (
      <ErrorState title={error ?? undefined} message="Position, ETA and weather data could not be loaded." onRetry={() => navigate(0)} lastUpdate={lastUpdate.toLocaleTimeString()} />
    );
  }

  const position = liveData?.current_position;
  const speed = liveData?.current_speed_kmh;
  const delay = liveData?.current_delay_minutes ?? etaData?.current_delay_minutes ?? 0;
  const source = liveData?.data_source || 'SIMULATION';

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate('/')} className="p-2 rounded-lg text-gray-500 hover:text-gray-200 hover:bg-white/[0.06] transition-colors" aria-label="Back">
          <ArrowLeft className="h-5 w-5" />
        </button>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="font-mono text-2xl font-bold text-gray-50">{train.train_number}</h1>
            <span className="text-gray-300 font-medium text-lg">{train.train_name}</span>
            <StatusBadge status={liveData?.data_source === 'LIVE' ? 'RUNNING' : train.status} />
            {source && <SourceBadge source={source} />}
          </div>
          <p className="text-sm text-gray-500 mt-0.5 flex items-center gap-1.5">
            {train.origin_station?.name || '—'} <ArrowLeft className="h-3 w-3 rotate-180 text-gray-700" /> {train.destination_station?.name || '—'}
          </p>
        </div>
        <button onClick={() => navigate(0)} className="btn-secondary btn-sm" title="Refresh data">
          <RefreshCw className="h-4 w-4" /> Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="card p-5 lg:col-span-1">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold uppercase tracking-widest text-gray-400">Train status</span>
            <span className={cn('w-2 h-2 rounded-full', isConnected ? 'bg-rail-green shadow-glow-green animate-pulse-slow' : 'bg-rail-red')} />
          </div>
          <dl className="space-y-2.5 text-sm">
            <div className="flex justify-between">
              <dt className="text-gray-500">Current station</dt>
              <dd className="font-medium text-gray-200">
                {position?.current_station_id ? `Station #${position.current_station_id}` : 'Between stations'}
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-500">Next station</dt>
              <dd className="font-medium text-gray-200">{liveData?.next_station?.station_name || '—'}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-500">Delay</dt>
              <dd className={cn('font-mono font-bold', delay > 0 ? 'text-rail-amber' : 'text-rail-green')}>
                {delay >= 0 ? '+' : ''}{delay.toFixed(0)} min
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-500">Travelled</dt>
              <dd className="font-mono text-gray-300">
                {liveData?.distance_travelled_km?.toFixed(1) ?? position?.distance_travelled_km.toFixed(1) ?? 'N/A'} km
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-500">Remaining</dt>
              <dd className="font-mono text-gray-300">
                {liveData?.distance_remaining_km ? `${liveData.distance_remaining_km.toFixed(1)} km` : '—'}
              </dd>
            </div>
            {train.scheduled_departure && (
              <div className="flex justify-between">
                <dt className="text-gray-500">Scheduled dep.</dt>
                <dd className="font-medium text-gray-200">{formatTime(train.scheduled_departure)}</dd>
              </div>
            )}
          </dl>
        </div>

        <div className="lg:col-span-2 space-y-4">
          <SIHETACard eta={sihEta} loading={sihEtaLoading} />
          <ETACard eta={etaData} />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="card p-5 flex flex-col items-center justify-center">
          <div className="w-full flex items-center justify-between mb-3 px-2">
            <span className="text-xs font-semibold uppercase tracking-widest text-gray-400 flex items-center gap-1.5">
              <Gauge className="h-4 w-4 text-accent" /> Speed
            </span>
            {position?.source && <SourceBadge source={position.source} className="text-[9px]" />}
          </div>
          <SpeedGauge speed={speed} max={160} />
        </div>

        <div className="lg:col-span-2">
          <DelayExplanation explanations={etaData?.explanations} totalDelay={etaData?.predicted_arrival_delay_minutes} />
        </div>
      </div>

      <div>
        <SectionHeader
          title={<span className="flex items-center gap-2"><RouteIcon className="h-5 w-5 text-accent" /> Route & position</span>}
          subtitle="Live map with station nodes along the route"
        />
        <RailwayMap stations={stations} position={position} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="card p-5">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-semibold uppercase tracking-widest text-gray-400 flex items-center gap-1.5">
              <Layers className="h-4 w-4 text-violet-400" /> Station timeline
            </span>
          </div>
          {timelineStops.length > 0 ? (
            <StationTimeline stops={timelineStops} />
          ) : (
            <EmptyState title="Route schedule unavailable" message="The route schedule for this train could not be loaded." />
          )}
        </div>

        <div className="space-y-4">
          <div className="card p-5">
            <div className="flex items-center gap-2 mb-3">
              <Cloud className="h-4 w-4 text-rail-blue" />
              <span className="text-xs font-semibold uppercase tracking-widest text-gray-400">Weather at next station</span>
            </div>
            {weather?.current ? (
              <div className="flex items-center gap-4">
                <div className="text-4xl font-bold font-mono text-gray-100">
                  {weather.current.temperature_celsius.toFixed(0)}<span className="text-xl text-gray-400">°C</span>
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-200 capitalize">{weather.current.weather_description}</p>
                  <div className="grid grid-cols-3 gap-2 mt-2 text-xs text-gray-500">
                    <span>💧 {weather.current.humidity_percent}%<br /><span className="text-gray-600">Humidity</span></span>
                    <span>🌬 {weather.current.wind_speed_kmh} km/h<br /><span className="text-gray-600">Wind</span></span>
                    <span>👁 {weather.current.visibility_km?.toFixed(1) ?? '—'} km<br /><span className="text-gray-600">Visibility</span></span>
                  </div>
                </div>
                <span className="badge-warning">{weather.current.severity}</span>
              </div>
            ) : (
              <p className="text-sm text-gray-500">Weather temporarily unavailable for this route.</p>
            )}
          </div>

          <div className="card p-5">
            <div className="flex items-center gap-2 mb-3">
              <AlertTriangle className="h-4 w-4 text-rail-amber" />
              <span className="text-xs font-semibold uppercase tracking-widest text-gray-400">Operational alerts</span>
              {alerts.length > 0 && <span className="badge-warning ml-auto">{alerts.length}</span>}
            </div>
            {alerts.length === 0 ? (
              <p className="text-sm text-gray-500">No active alerts for this train.</p>
            ) : (
              <ul className="space-y-2">
                {alerts.slice(0, 5).map((a) => (
                  <li key={a.id} className="flex items-start gap-2 text-sm animate-slide-in">
                    <span className={cn('w-1.5 h-1.5 rounded-full mt-1.5 shrink-0', a.severity === 'CRITICAL' ? 'bg-rail-red' : a.severity === 'WARNING' ? 'bg-rail-amber' : 'bg-rail-blue')} />
                    <div className="flex-1 min-w-0">
                      <p className="text-gray-300 text-xs font-medium">{a.title}</p>
                      <p className="text-[11px] text-gray-500">{formatTime(a.created_at)}</p>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}