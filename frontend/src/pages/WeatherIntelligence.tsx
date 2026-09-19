import { useState, useEffect } from 'react';
import { stationApi, weatherApi } from '../services/api';
import { CloudRain, Droplets, Wind, Eye, Thermometer } from 'lucide-react';
import { cn } from '../utils/helpers';
import { SectionHeader } from '../components/ui/SectionHeader';
import { EmptyState } from '../components/ui/EmptyState';
import type { Station, WeatherResponse } from '../types';

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
  const [stations, setStations] = useState<Station[]>([]);
  const [weather, setWeather] = useState<Record<number, WeatherResponse | null>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const stationRes = await stationApi.list({ page_size: 100 });
        const stationsList = (stationRes.data.items || []).slice(0, 12);
        if (!mounted) return;
        setStations(stationsList);

        const map: Record<number, WeatherResponse | null> = {};
        await Promise.allSettled(stationsList.map(async (s) => {
          const w = await weatherApi.getStationWeather(s.id).catch(() => null);
          if (mounted && w?.data) map[s.id] = w.data;
        }));
        if (mounted) setWeather(map);
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => { mounted = false; };
  }, []);

  const severeCount = Object.values(weather).filter((w) => w?.current?.severity === 'SEVERE').length;
  const cautionCount = Object.values(weather).filter((w) => w?.current?.severity === 'CAUTION').length;

  return (
    <div className="space-y-6">
      <SectionHeader title="Weather Intelligence" subtitle="Station-level conditions fed by the weather provider" />

      <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
        <div className="metric-card">
          <p className="text-xs font-medium uppercase tracking-wider text-gray-500">Stations reporting</p>
          <p className="text-3xl font-bold font-mono text-accent mt-1.5">{Object.keys(weather).length}<span className="text-base text-gray-500"> / {stations.length}</span></p>
        </div>
        <div className="metric-card">
          <p className="text-xs font-medium uppercase tracking-wider text-gray-500">Caution conditions</p>
          <p className="text-3xl font-bold font-mono text-rail-amber mt-1.5">{cautionCount}</p>
        </div>
        <div className="metric-card">
          <p className="text-xs font-medium uppercase tracking-wider text-gray-500">Severe conditions</p>
          <p className="text-3xl font-bold font-mono text-rail-red mt-1.5">{severeCount}</p>
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {Array.from({ length: 6 }).map((_, i) => <div key={i} className="animate-pulse rounded-xl bg-white/[0.05] h-48" />)}
        </div>
      ) : stations.length === 0 ? (
        <div className="card"><EmptyState icon={CloudRain} title="No station weather" message="Weather data could not be retrieved." /></div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {stations.map((s) => {
            const w = weather[s.id];
            const c = w?.current;
            return (
              <div key={s.id} className={cn('card p-4 transition-all', c?.severity === 'SEVERE' && 'border-rail-red/30 shadow-glow-red')}>
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <p className="text-sm font-semibold text-gray-200">{s.name}</p>
                    <p className="text-[11px] font-mono text-gray-600">{s.code}</p>
                  </div>
                  {c ? (
                    <span className={cn(c.severity === 'SEVERE' ? 'badge-critical' : c.severity === 'CAUTION' ? 'badge-warning' : 'badge-success')}>{c.severity}</span>
                  ) : (
                    <span className="badge-neutral">No data</span>
                  )}
                </div>
                {c ? (
                  <div className="space-y-3">
                    <div className="flex items-center gap-3">
                      <Thermometer className="h-8 w-8 text-rail-amber" />
                      <p className="font-mono text-3xl font-bold text-gray-100">{c.temperature_celsius.toFixed(0)}<span className="text-lg text-gray-400">°C</span></p>
                      <p className="text-sm text-gray-400 capitalize ml-auto">{c.weather_description}</p>
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <WeatherMetricIcon icon={Droplets} label="Humidity" value={`${c.humidity_percent}%`} />
                      <WeatherMetricIcon icon={Wind} label="Wind" value={`${c.wind_speed_kmh} km/h`} />
                      <WeatherMetricIcon icon={Eye} label="Visibility" value={`${c.visibility_km?.toFixed(1) ?? '—'} km`} />
                      <WeatherMetricIcon icon={Droplets} label="Rain prob." value={`${c.precipitation_probability ?? 0}%`} />
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-gray-600">WEATHER TEMPORARILY UNAVAILABLE</p>
                )}
              </div>
            );
          })}
        </div>
      )}

      <div className="card p-4 flex items-center gap-3">
        <CloudRain className="h-5 w-5 text-rail-blue shrink-0" />
        <p className="text-sm text-gray-500">
          Route-level weather for a specific train is shown on the train detail page. Severe conditions at any station are reflected
          in the operations alert center when the backend generates them.
        </p>
      </div>
    </div>
  );
}