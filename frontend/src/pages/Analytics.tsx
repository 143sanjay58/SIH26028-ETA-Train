import { useState, useEffect, useMemo } from 'react';
import { trainApi, congestionApi } from '../services/api';
import { BarChart3, Clock, Route as RouteIcon, Timer } from 'lucide-react';
import { SectionHeader } from '../components/ui/SectionHeader';
import { MetricCard } from '../components/ui/MetricCard';
import { ChartCard } from '../components/charts/ChartCard';
import { HorizontalBars, SegmentedBar, tooltipStyle } from '../components/charts/chartBits';
import {
  ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, LineChart, Line,
} from 'recharts';
import { LoadingSkeleton } from '../components/ui/LoadingSkeleton';
import { cn } from '../utils/helpers';
import type { Train, TrainLiveResponse, CongestionState } from '../types';

export default function Analytics() {
  const [trains, setTrains] = useState<Train[]>([]);
  const [live, setLive] = useState<Record<number, TrainLiveResponse>>({});
  const [congestion, setCongestion] = useState<CongestionState[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const [trainRes, congRes] = await Promise.all([
          trainApi.list({ page_size: 100 }),
          congestionApi.getNetwork().catch(() => [] as CongestionState[]),
        ]);
        const list = trainRes.data.trains || [];
        if (!mounted) return;
        setTrains(list);
        setCongestion(Array.isArray(congRes) ? congRes : []);

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

  const delayed = Object.values(live).filter((l) => l.current_delay_minutes > 0);
  const onTime = Object.values(live).filter((l) => l.current_delay_minutes <= 0);

  const distribution = useMemo(() => {
    const buckets = [
      { name: 'On time / early', value: onTime.length },
      { name: '0–10m', value: delayed.filter((l) => l.current_delay_minutes <= 10).length },
      { name: '10–30m', value: delayed.filter((l) => l.current_delay_minutes > 10 && l.current_delay_minutes <= 30).length },
      { name: '>30m', value: delayed.filter((l) => l.current_delay_minutes > 30).length },
    ];
    return buckets.filter((b) => b.value > 0);
  }, [delayed, onTime]);

  const dwell = useMemo(() =>
    Object.values(live).slice(0, 10).map((l) => ({
      name: l.train.train_number,
      'Avg speed': Math.round(l.average_speed_kmh),
    })),
    [live]
  );

  const speedSeries = useMemo(() =>
    Object.values(live).slice(0, 12).map((l) => ({
      name: l.train.train_number,
      speed: Math.round(l.current_speed_kmh),
      delay: Math.round(l.current_delay_minutes),
    })),
    [live]
  );

  const congestionLevels = useMemo(() => ({
    LOW: congestion.filter((c) => c.level === 'LOW').length,
    MEDIUM: congestion.filter((c) => c.level === 'MEDIUM').length,
    HIGH: congestion.filter((c) => c.level === 'HIGH').length,
    CRITICAL: congestion.filter((c) => c.level === 'CRITICAL').length,
  }), [congestion]);

  const onTimePct = Object.values(live).length ? (onTime.length / Object.values(live).length) * 100 : 0;
  const avgSpeed = Object.values(live).length ? Object.values(live).reduce((s, l) => s + l.current_speed_kmh, 0) / Object.values(live).length : 0;

  return (
    <div className="space-y-6">
      <SectionHeader title="Network Analytics" subtitle="Operational performance derived from live train data" />

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <LoadingSkeleton className="h-24" /><LoadingSkeleton className="h-24" /><LoadingSkeleton className="h-24" /><LoadingSkeleton className="h-24" />
        </div>
      ) : (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <MetricCard icon={BarChart3} label="On-time rate" value={`${onTimePct.toFixed(0)}%`} accent="green" />
          <MetricCard icon={Timer} label="Avg active speed" value={`${avgSpeed.toFixed(0)} km/h`} accent="cyan" />
          <MetricCard icon={Clock} label="Avg delay (delayed only)" value={`${delayed.length ? (delayed.reduce((s, l) => s + l.current_delay_minutes, 0) / delayed.length).toFixed(0) : '0'}m`} accent="amber" />
          <MetricCard icon={RouteIcon} label="Congested sections" value={congestion.filter((c) => c.level === 'HIGH' || c.level === 'CRITICAL').length} accent="violet" />
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ChartCard title="Delay distribution" subtitle="How the network's active trains distribute by delay">
          {distribution.length === 0 ? (
            <p className="text-sm text-gray-500 py-8 text-center">No live delay data to chart.</p>
          ) : (
            <SegmentedBar segments={distribution.map((d) => ({ name: d.name, value: d.value, color: d.name === 'On time / early' ? '#10b981' : d.name === '0–10m' ? '#00d4ff' : d.name === '10–30m' ? '#f59e0b' : '#ef4444' }))} />
          )}
        </ChartCard>

        <ChartCard title="Congestion by level" subtitle="Section congestion across the network">
          {congestion.length === 0 ? (
            <p className="text-sm text-gray-500 py-8 text-center">No congestion measurements available.</p>
          ) : (
            <SegmentedBar segments={[
              { name: 'Low', value: congestionLevels.LOW, color: '#10b981' },
              { name: 'Medium', value: congestionLevels.MEDIUM, color: '#f59e0b' },
              { name: 'High', value: congestionLevels.HIGH, color: '#fb923c' },
              { name: 'Critical', value: congestionLevels.CRITICAL, color: '#ef4444' },
            ]} />
          )}
        </ChartCard>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ChartCard title="Average speed by train" subtitle="Running-average speed for active trains">
          {dwell.length === 0 ? (
            <p className="text-sm text-gray-500 py-8 text-center">No live data to chart.</p>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={dwell} margin={{ left: -20 }}>
                <CartesianGrid vertical={false} stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="name" stroke="#6b7280" tick={{ fill: '#6b7280', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis stroke="#6b7280" tick={{ fill: '#6b7280', fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={tooltipStyle} />
                <Bar dataKey="Avg speed" fill="#00d4ff" radius={[4, 4, 0, 0]} barSize={18} fillOpacity={0.75} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        <ChartCard title="Speed vs delay" subtitle="Current speed and running delay per active train">
          {speedSeries.length === 0 ? (
            <p className="text-sm text-gray-500 py-8 text-center">No live data to chart.</p>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={speedSeries} margin={{ left: -20 }}>
                <CartesianGrid stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis dataKey="name" stroke="#6b7280" tick={{ fill: '#6b7280', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis yAxisId="speed" stroke="#6b7280" tick={{ fill: '#6b7280', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis yAxisId="delay" orientation="right" stroke="#6b7280" tick={{ fill: '#6b7280', fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={tooltipStyle} />
                <Line yAxisId="speed" type="monotone" dataKey="speed" stroke="#00d4ff" strokeWidth={2} dot={{ r: 3 }} />
                <Line yAxisId="delay" type="monotone" dataKey="delay" stroke="#f59e0b" strokeWidth={2} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
      </div>

      <ChartCard title="Top performers / risks" subtitle="Delayed trains ranked by running delay">
        {delayed.length === 0 ? (
          <p className="text-sm text-gray-500 py-8 text-center">No delayed trains currently.</p>
        ) : (
          <HorizontalBars
            data={delayed.slice(0, 8).map((l) => ({ name: l.train.train_number, value: Math.round(l.current_delay_minutes) }))}
            accent="#f59e0b"
          />
        )}
      </ChartCard>

      <div className="card p-4">
        <p className="text-xs text-gray-500">
          All metrics on this page are computed from the <span className="text-gray-300 font-mono">/trains/{'{id}'}/live</span> and{' '}
          <span className="text-gray-300 font-mono">/congestion/network</span> endpoints. Values update with realtime WebSocket pushes.
          <span className={cn('ml-2 inline-block')}>{loading ? 'Refreshing…' : `${trains.length} trains tracked`}</span>
        </p>
      </div>
    </div>
  );
}