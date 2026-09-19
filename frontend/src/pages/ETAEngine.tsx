import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { trainApi, predictionApi } from '../services/api';
import { BrainCircuit, Sparkles, ArrowRight } from 'lucide-react';
import { cn } from '../utils/helpers';
import { SectionHeader } from '../components/ui/SectionHeader';
import { MetricCard } from '../components/ui/MetricCard';
import { ConfidenceRing } from '../components/ui/ConfidenceRing';
import { DelayExplanation } from '../components/train/DelayExplanation';
import { LoadingSkeleton } from '../components/ui/LoadingSkeleton';
import type { Train, ETAResponse } from '../types';

export default function ETAEngine() {
  const navigate = useNavigate();
  const [trains, setTrains] = useState<Train[]>([]);
  const [selected, setSelected] = useState<string>('');
  const [eta, setEta] = useState<ETAResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [recentEta, setRecentEta] = useState<ETAResponse[]>([]);

  useEffect(() => {
    trainApi.list({ page_size: 100 }).then((res) => setTrains(res.data.trains || [])).catch(() => {});
  }, []);

  const runPrediction = async (trainNumber: string) => {
    setSelected(trainNumber);
    setLoading(true);
    setEta(null);
    try {
      const res = await predictionApi.getETA(trainNumber, { include_explanations: true, include_uncertainty: true });
      setEta(res.data);
      setRecentEta((prev) => [res.data, ...prev].slice(0, 6));
    } catch {
      setEta(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <SectionHeader
        title="AI ETA Engine"
        subtitle="On-demand arrival prediction with confidence and explainability"
        right={
          <span className="badge-info flex items-center gap-1.5"><Sparkles className="h-3 w-3" /> Machine Learning</span>
        }
      />

      <div className="card p-5">
        <p className="text-sm text-gray-400 mb-3">Select a train to run a live prediction.</p>
        <div className="flex flex-wrap gap-2">
          {trains.slice(0, 12).map((t) => (
            <button
              key={t.id}
              onClick={() => runPrediction(t.train_number)}
              className={cn('px-3 py-1.5 rounded-lg border text-sm font-mono transition-all',
                selected === t.train_number ? 'border-accent/50 bg-accent/10 text-accent' : 'border-white/10 bg-white/[0.03] text-gray-300 hover:border-white/20')}
            >
              {t.train_number}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <LoadingSkeleton className="h-56 lg:col-span-2" />
          <LoadingSkeleton className="h-56" />
        </div>
      ) : eta ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 animate-fade-in">
          <div className="lg:col-span-2 space-y-4">
            <MetricCard
              icon={BrainCircuit}
              label="Predicted delay at destination"
              value={`${eta.predicted_arrival_delay_minutes >= 0 ? '+' : ''}${eta.predicted_arrival_delay_minutes.toFixed(0)}m`}
              accent={eta.predicted_arrival_delay_minutes > 0 ? 'red' : 'green'}
              subValue={`${eta.train_name} · ${eta.destination_station}`}
            />
            <DelayExplanation explanations={eta.explanations} totalDelay={eta.predicted_arrival_delay_minutes} />
          </div>
          <div className="card p-5 flex flex-col items-center justify-center gap-3">
            <ConfidenceRing confidence={eta.confidence_score} size={140} stroke={10} />
            <dl className="w-full space-y-2 text-sm">
              <div className="flex justify-between">
                <dt className="text-gray-500">Model</dt>
                <dd className="font-mono text-violet-300">{eta.model_type}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Version</dt>
                <dd className="font-mono text-gray-300">{eta.model_version}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Source</dt>
                <dd className="text-gray-300">{eta.data_source}</dd>
              </div>
            </dl>
            <button onClick={() => navigate(`/train/${selected}`)} className="btn-secondary btn-sm w-full mt-1">
              Open train view <ArrowRight className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      ) : (
        <div className="card p-10 flex flex-col items-center text-center">
          <BrainCircuit className="h-10 w-10 text-gray-600 mb-3" />
          <p className="text-sm text-gray-400">No prediction run yet. Select a train above to compute an AI ETA.</p>
        </div>
      )}

      {recentEta.length > 1 && (
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-gray-200 mb-4">Recent predictions in this session</h3>
          <div className="space-y-2">
            {recentEta.map((r, i) => (
              <div key={i} className="flex items-center gap-3 text-sm animate-fade-in">
                <span className="font-mono font-bold text-gray-100 w-16">{r.train_number}</span>
                <span className="text-gray-400 flex-1 truncate">{r.train_name}</span>
                <span className={cn('font-mono font-semibold', r.predicted_arrival_delay_minutes > 0 ? 'text-rail-amber' : 'text-rail-green')}>
                  {r.predicted_arrival_delay_minutes >= 0 ? '+' : ''}{r.predicted_arrival_delay_minutes.toFixed(0)}m
                </span>
                <span className="text-xs text-gray-600">conf {(r.confidence_score ?? 0) * 100}%</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="card p-5">
        <h3 className="text-sm font-semibold text-gray-200 mb-2">About this engine</h3>
        <p className="text-sm text-gray-500 leading-relaxed">
          The ETA engine combines live/simulated position, schedule adherence and operational factors into an arrival
          prediction. Confidence reflects model agreement; the prediction interval bounds the expected arrival window.
          Factor explanations are provided by the model directly — they are never invented in the UI.
        </p>
        {recentEta.length === 0 && (
          <p className="text-xs text-gray-600 mt-2">
            {loaderNote(loading)}
          </p>
        )}
      </div>
    </div>
  );
}

function loaderNote(loading: boolean) {
  return loading ? 'Processing prediction…' : 'Awaiting a prediction request.';
}