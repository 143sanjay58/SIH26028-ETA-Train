import { useCallback, useRef, useState } from 'react';
import { stationApi, weatherApi, sihEtaApi, trainApi } from '../services/api';
import { CloudRain, Droplets, Wind, Eye, Thermometer, RefreshCw, Loader2 } from 'lucide-react';
import { cn } from '../utils/helpers';
import { SectionHeader } from '../components/ui/SectionHeader';
import { TrainPicker, type TrainOption } from '../components/train/TrainPicker';
import { EmptyState } from '../components/ui/EmptyState';
import type { WeatherResponse } from '../types';

type RouteRole = 'CURRENT' | 'UPCOMING' | 'DESTINATION';

interface RouteStation {
  code: string;
  name: string;
  position: number;
  role: RouteRole;
}

interface RouteWeatherStation extends RouteStation {
  state: 'LOADING' | 'READY' | 'UNAVAILABLE';
  weather?: WeatherResponse;
}

function WeatherMetricIcon({ icon: Icon, label, value }: { icon: typeof Droplets; label: string; value: string }) {
  return (
    <div className="flex items-center gap-2">
      <Icon className="h-4 w-4 text-gray-500" />
      <div>
        <p className="text-[11px] text-gray-600">{label}</p>
        <p className="text-sm font-medium text-gray-200">{value}</p>
      </div>
    </div>
  );
}

export default function WeatherIntelligence() {
  const [selected, setSelected] = useState<TrainOption | null>(null);
  const [stations, setStations] = useState<RouteWeatherStation[]>([]);
  const [totalRouteStations, setTotalRouteStations] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const reqRef = useRef(0);

  const loadRoute = useCallback(async (opt: TrainOption) => {
    const id = ++reqRef.current;
    setLoading(true);
    setError(null);
    setStations([]);
    setTotalRouteStations(0);
    try {
      const etaRes = await sihEtaApi.getETA(opt.train_number).catch(() => null);
      let route: RouteStation[] = [];
      const push = (code: string | undefined, name: string | undefined, position: number, role: RouteRole) => {
        if (!code) return;
        route.push({ code, name: name || code, position, role });
      };

      if (etaRes?.data) {
        const eta = etaRes.data;
        push(eta.current_station, eta.current_station_name, eta.current_route_position, 'CURRENT');
        (eta.upcoming_stations || []).forEach((u) => push(u.station_code, u.station_name || u.station_code, u.route_position, 'UPCOMING'));
        push(eta.destination_station, eta.destination_station_name, eta.current_route_position + eta.upcoming_station_count + 1, 'DESTINATION');
      } else if (opt.trainId) {
        const routeRes = await trainApi.getRoute(opt.trainId).catch(() => null);
        if (routeRes?.data) {
          const rd = routeRes.data;
          (rd.passed_stations || []).forEach((s) => push(s.station_code, s.station_name, s.sequence, 'UPCOMING'));
          (rd.upcoming_stations || []).forEach((s) => push(s.station_code, s.station_name, s.sequence, 'UPCOMING'));
          if (rd.destination) push(rd.destination.station_code, rd.destination.station_name, rd.destination.sequence, 'DESTINATION');
        }
      }

      if (!route.length) {
        if (id === reqRef.current) setError('Route information is currently unavailable for this train.');
        return;
      }

      const byCode = new Map<string, RouteStation>();
      [...route].sort((a, b) => a.position - b.position).forEach((s) => {
        const prev = byCode.get(s.code);
        if (!prev) byCode.set(s.code, s);
        else if (s.role === 'DESTINATION') byCode.set(s.code, { ...s });
      });
      const ordered = [...byCode.values()].sort((a, b) => a.position - b.position);
      if (id !== reqRef.current) return;
      setTotalRouteStations(ordered.length);

      const currentIdx = ordered.findIndex((s) => s.role === 'CURRENT');
      const start = currentIdx >= 0 ? currentIdx : 0;
      let cols = ordered.slice(start, start + 6);
      const dest = [...ordered].reverse().find((s) => s.role === 'DESTINATION');
      if (dest && !cols.some((c) => c.code === dest.code)) cols = [...cols, dest];

      setStations(cols.map((s) => ({ ...s, state: 'LOADING' as const })));

      await Promise.allSettled(cols.map(async (st) => {
        let weather: WeatherResponse | null = null;
        try {
          const stationRes = await stationApi.getByCode(st.code);
          const wRes = await weatherApi.getStationWeather(stationRes.data.id);
          weather = wRes.data;
        } catch { weather = null; }
        if (id !== reqRef.current) return;
        setStations((prev) => prev.map((p) =>
          p.code === st.code ? { ...p, weather: weather ?? undefined, state: weather ? 'READY' : 'UNAVAILABLE' } : p
        ));
      }));
    } finally {
      if (id === reqRef.current) setLoading(false);
    }
  }, []);

  const handleSelect = (opt: TrainOption | null) => {
    setSelected(opt);
    if (!opt) {
      reqRef.current++;
      setStations([]);
      setError(null);
      setTotalRouteStations(0);
      return;
    }
    void loadRoute(opt);
  };

  const refresh = () => { if (selected) void loadRoute(selected); };

  const ready = stations.filter((s) => s.state === 'READY' && s.weather?.current);
  const caution = ready.filter((s) => s.weather?.current?.severity === 'CAUTION').length;
  const severe = ready.filter((s) => s.weather?.current?.severity === 'SEVERE').length;

  return (
    <div className="space-y-6">
      <SectionHeader
        title="Weather Intelligence"
        subtitle="Route-level conditions for the train you select"
        right={
          selected && (
            <button onClick={refresh} className="btn-secondary btn-sm" title="Refresh weather">
              <RefreshCw className="h-4 w-4" /> Refresh
            </button>
          )
        }
      />

      <div className="card p-5">
        <div className="flex items-center gap-2 mb-3">
          <CloudRain className="h-5 w-5 text-rail-blue" />
          <h2 className="text-sm font-semibold text-gray-200">Train weather along the route</h2>
        </div>
        <TrainPicker
          value={selected}
          onChange={handleSelect}
          placeholder="Search train number or name…"
          hint="Pick any train to see weather at its current, upcoming and destination stations."
        />
        {!selected && (
          <p className="text-sm text-gray-500 mt-4 pl-1">Select a train to view weather along its route.</p>
        )}
        {selected && !loading && !error && (
          <p className="text-xs text-gray-500 mt-3 pl-1">
            Route: {selected.origin} → {selected.destination} · {selected.source === 'SIH_CATALOGUE' ? 'SIH catalogue train' : 'Registered train'}
          </p>
        )}
      </div>

      {error && !loading && (
        <div className="card"><EmptyState icon={CloudRain} title="Weather along route unavailable" message={error} /></div>
      )}

      {loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {Array.from({ length: 3 }).map((_, i) => <div key={i} className="animate-pulse rounded-xl bg-white/[0.05] h-52" />)}
          <p className="text-sm text-gray-500 col-span-full">Fetching route &amp; weather…</p>
        </div>
      )}

      {!loading && selected && !error && (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
            <div className="metric-card">
              <p className="text-xs font-medium uppercase tracking-wider text-gray-500">Stations with weather</p>
              <p className="text-3xl font-bold font-mono text-accent mt-1.5">{ready.length}<span className="text-base text-gray-500"> / {stations.length}</span></p>
            </div>
            <div className="metric-card">
              <p className="text-xs font-medium uppercase tracking-wider text-gray-500">Caution conditions</p>
              <p className="text-3xl font-bold font-mono text-rail-amber mt-1.5">{caution}</p>
            </div>
            <div className="metric-card">
              <p className="text-xs font-medium uppercase tracking-wider text-gray-500">Severe conditions</p>
              <p className="text-3xl font-bold font-mono text-rail-red mt-1.5">{severe}</p>
            </div>
          </div>

          {stations.length === 0 ? (
            <div className="card"><EmptyState icon={CloudRain} title="No route weather" message="No weather could be determined for this train's route." /></div>
          ) : (
            <>
              <p className="text-xs text-gray-500 px-1">
                Showing weather for {stations.length} of {totalRouteStations} route stations (current, next upcoming and destination).
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {stations.map((st) => {
                  const c = st.weather?.current;
                  return (
                    <div key={st.code} className={cn('card p-4 transition-all', c?.severity === 'SEVERE' && 'border-rail-red/30 shadow-glow-red', c?.severity === 'CAUTION' && 'border-rail-amber/20')}>
                      <div className="flex items-center justify-between mb-3 gap-2">
                        <div className="min-w-0">
                          <p className="text-sm font-semibold text-gray-200 truncate">{st.name}</p>
                          <p className="text-[11px] font-mono text-gray-600">{st.code}</p>
                        </div>
                        <div className="flex items-center gap-1.5 shrink-0">
                          <span className={cn(st.role === 'CURRENT' ? 'badge-live' : st.role === 'DESTINATION' ? 'badge-sim' : 'badge-info')}>{st.role}</span>
                          {c && (
                            <span className={cn(c.severity === 'SEVERE' ? 'badge-critical' : c.severity === 'CAUTION' ? 'badge-warning' : 'badge-success')}>{c.severity}</span>
                          )}
                        </div>
                      </div>
                      {st.state === 'LOADING' ? (
                        <div className="flex items-center justify-center py-8"><Loader2 className="h-5 w-5 animate-spin text-accent" /></div>
                      ) : st.state === 'UNAVAILABLE' || !c ? (
                        <div className="flex items-center gap-2 py-6 text-sm text-gray-500">
                          <CloudRain className="h-4 w-4 shrink-0" />
                          <p>Weather information is currently unavailable</p>
                        </div>
                      ) : (
                        <>
                          <div className="flex items-center gap-3">
                            <Thermometer className="h-8 w-8 text-rail-amber" />
                            <p className="font-mono text-3xl font-bold text-gray-100">{c.temperature_celsius.toFixed(0)}<span className="text-lg text-gray-400">°C</span></p>
                            <p className="text-sm text-gray-400 capitalize ml-auto text-right">{c.weather_description}</p>
                          </div>
                          <div className="grid grid-cols-2 gap-2 mt-3 border-t border-white/[0.06] pt-3">
                            <WeatherMetricIcon icon={Droplets} label="Humidity" value={`${c.humidity_percent ?? 0}%`} />
                            <WeatherMetricIcon icon={Wind} label="Wind" value={`${c.wind_speed_kmh ?? 0} km/h`} />
                            <WeatherMetricIcon icon={Eye} label="Visibility" value={`${c.visibility_km?.toFixed(1) ?? '—'} km`} />
                            <WeatherMetricIcon icon={Droplets} label="Rain prob." value={`${c.precipitation_probability ?? 0}%`} />
                          </div>
                        </>
                      )}
                    </div>
                  );
                })}
              </div>
            </>
          )}

          <div className="card p-4 flex items-center gap-3">
            <CloudRain className="h-5 w-5 text-rail-blue shrink-0" />
            <p className="text-sm text-gray-500">
              Weather is resolved per route station via the operational weather provider. Stations not registered in the operational network
              (typical for SIH catalogue routes) are shown as unavailable. Severe conditions feed the operations alert centre.
            </p>
          </div>
        </>
      )}
    </div>
  );
}