import { useState, useEffect, useMemo } from 'react';
import { trainApi, predictionApi } from '../services/api';
import { Gauge } from 'lucide-react';
import { SectionHeader } from '../components/ui/SectionHeader';
import { MetricCard } from '../components/ui/MetricCard';
import { ChartCard } from '../components/charts/ChartCard';
import { HorizontalBars } from '../components/charts/chartBits';
import { LoadingSkeleton } from '../components/ui/LoadingSkeleton';
import type { TrainLiveResponse, ETAResponse } from '../types';

export default function DelayIntelligence() {
  const [live, setLive] = useState<Record<number, TrainLiveResponse>>({});
  const [explanations, setExplanations] = useState<Record<string, ETAResponse>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const res = await trainApi.list({ page_size: 100 });
        const list = res.data.trains || [];
        if (!mounted) return;

        const liveMap: Record<number, TrainLiveResponse> = {};
        const expMap: Record<string, ETAResponse> = {};
        await Promise.allSettled(list.map(async (t) => {
          const [l, e] = await Promise.all([
            trainApi.getLive(t.id).catch(() => null),
            predictionApi.getETA(t.train_number, { include_explanations: true }).catch(() => null),
          ]);
          if (l?.data) liveMap[t.id] = l.data;
          if (e?.data && e.data.explanations?.length) expMap[t.train_number] = e.data;
        }));
        if (!mounted) return;
        setLive(liveMap);
        setExplanations(expMap);
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => { mounted = false; };
  }, []);

  const delayed = useMemo(() => Object.values(live).filter((l) => l.current_delay_minutes > 0), [live]);

  const byTrain = useMemo(() =>
    delayed
      .map((l) => ({ name: `${l.train.train_number}\u00A0${l.train.train_name}`, value: Math.round(l.current_delay_minutes) }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 8),
    [delayed]
  );

  const byCause = useMemo(() => {
    const counts: Record<string, number> = {};
    Object.values(explanations).forEach((e) => {
      e.explanations.forEach((x) => {
        if (x.direction !== 'NEUTRAL') counts[x.factor_name] = (counts[x.factor_name] || 0) + Math.round(Math.abs(x.contribution_minutes));
      });
    });
    return Object.entries(counts).map(([name, value]) => ({ name: name.replace(/_/g, ' '), value })).sort((a, b) => b.value - a.value).slice(0, 6);
  }, [explanations]);

  const maxDelay = delayed.reduce((m, l) => Math.max(m, l.current_delay_minutes), 0);
  const avgDelay = delayed.length ? delayed.reduce((s, l) => s + l.current_delay_minutes, 0) / delayed.length : 0;
  const critical = delayed.filter((l) => l.current_delay_minutes > 30).length;

  return (
    <div className="space-y-6">
      <SectionHeader title="Delay Intelligence" subtitle="Network, train and section-level delay analytics" />

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3"><LoadingSkeleton className="h-24" /><LoadingSkeleton className="h-24" /><LoadingSkeleton className="h-24" /><LoadingSkeleton className="h-24" /></div>
      ) : (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <MetricCard icon={Gauge} label="Delayed trains" value={delayed.length} accent="amber" />
          <MetricCard icon={Gauge} label="Avg delay" value={`${avgDelay.toFixed(0)}m`} accent="cyan" />
          <MetricCard icon={Gauge} label="Max delay" value={`${maxDelay.toFixed(0)}m`} accent="red" />
          <MetricCard icon={Gauge} label="Critical (>30m)" value={critical} accent="violet" />
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ChartCard title="Delay by train" subtitle="Current running delay for active trains">
          {byTrain.length === 0 ? (
            <p className="text-sm text-gray-500 py-8 text-center">No delayed trains. <span className="text-xs text-gray-600">Run the simulation to generate congestion.</span></p>
          ) : (
            <HorizontalBars data={byTrain} accent="#f59e0b" />
          )}
        </ChartCard>

        <ChartCard title="Delay contribution by cause" subtitle="Model-attributed delay minutes (positive factors)">
          {byCause.length === 0 ? (
            <p className="text-sm text-gray-500 py-8 text-center">No factor explanations available yet. Run predictions to populate.</p>
          ) : (
            <HorizontalBars data={byCause} accent="#00d4ff" />
          )}
        </ChartCard>
      </div>

      <ChartCard title="Live delay snapshot" subtitle="Currently running trains and their delay in minutes">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b border-white/[0.06]">
                <th className="table-header px-2 py-2">Train</th>
                {Object.values(live).slice(0, 14).map((l) => (
                  <th key={l.train.id} className="px-2 py-2 text-center">
                    <p className="font-mono text-[10px] font-bold text-gray-300">{l.train.train_number}</p>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="px-2 py-2 text-xs text-gray-500">Delay (min)</td>
                {Object.values(live).slice(0, 14).map((l) => (
                  <td key={l.train.id} className="px-2 py-2">
                    <div className="h-6 rounded-md overflow-hidden bg-white/5 flex items-center justify-center">
                      <div className={`h-full transition-all duration-700 ${l.current_delay_minutes > 30 ? 'bg-rail-red/70' : l.current_delay_minutes > 0 ? 'bg-rail-amber/70' : 'bg-rail-green/60'}`}
                        style={{ width: `${Math.min(100, (l.current_delay_minutes / (maxDelay || 1)) * 100)}%` }} />
                    </div>
                    <span className="block text-center text-[10px] font-mono text-gray-400 mt-0.5">
                      {l.current_delay_minutes > 0 ? `+${Math.round(l.current_delay_minutes)}m` : '0m'}
                    </span>
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      </ChartCard>
    </div>
  );
}