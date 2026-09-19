import { useState, useEffect } from 'react';
import { simulationApi } from '../services/api';
import { FlaskConical, Play, Pause, Square, Loader2, Zap } from 'lucide-react';
import { cn, getScenarioLabel } from '../utils/helpers';
import { SectionHeader } from '../components/ui/SectionHeader';
import type { SimulationStatus, SimulationScenario } from '../types';
import toast from 'react-hot-toast';

const SCENARIOS: SimulationScenario[] = [
  'NORMAL',
  'CONGESTION',
  'SIGNAL_DELAY',
  'EXTENDED_HALT',
  'SPEED_RESTRICTION',
  'HEAVY_RAIN',
  'LOW_VISIBILITY',
  'PRECEDING_TRAIN_DELAY',
  'UNSCHEDULED_STOP',
  'CASCADING_DELAY',
  'RECOVERY',
];

const SPEEDS = [1, 2, 5, 10];

export default function SimulationLab() {
  const [status, setStatus] = useState<SimulationStatus | null>(null);
  const [scenario, setScenario] = useState<SimulationScenario>('NORMAL');
  const [busy, setBusy] = useState(false);

  const refresh = async () => {
    try {
      const res = await simulationApi.getStatus();
      setStatus(res.data);
    } catch { /* backend may be off */ }
  };

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 4000);
    return () => clearInterval(interval);
  }, []);

  const control = async (action: string, payload?: { speed?: number; scenario?: SimulationScenario }) => {
    setBusy(true);
    try {
      await simulationApi.control(action, payload?.speed, payload?.scenario);
      toast.success(`Simulation ${action}${action === 'start' ? 'ed' : ''}`.replace('stop', 'stopped'));
      setTimeout(refresh, 500);
    } catch {
      toast.error('Simulation request failed — is the backend running?');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-6">
      <SectionHeader
        title="Simulation Lab — Railway Digital Twin"
        subtitle="Drive the simulation engine to demonstrate delays, propagation and recovery"
        right={<span className="badge-sim flex items-center gap-1.5"><FlaskConical className="h-3 w-3" /> Simulation Environment</span>}
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="card p-5 lg:col-span-2">
          <h2 className="text-sm font-semibold text-gray-200 mb-3">Scenario</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {SCENARIOS.map((s) => (
              <button
                key={s}
                onClick={() => setScenario(s)}
                className={cn('px-3 py-2 rounded-lg border text-xs font-medium transition-all text-left',
                  scenario === s ? 'border-accent/50 bg-accent/10 text-accent' : 'border-white/10 bg-white/[0.03] text-gray-400 hover:border-white/20 hover:text-gray-200')}
              >
                {getScenarioLabel(s)}
              </button>
            ))}
          </div>

          <h2 className="text-sm font-semibold text-gray-200 mt-6 mb-3">Controls</h2>
          <div className="flex flex-wrap items-center gap-2">
            <button onClick={() => control('start', { scenario })} disabled={busy || status?.is_running} className="btn-primary btn-sm">
              {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />} Start
            </button>
            <button onClick={() => control('pause')} disabled={busy || !status?.is_running || status?.is_paused} className="btn-secondary btn-sm">
              <Pause className="h-4 w-4" /> Pause
            </button>
            <button onClick={() => control('resume')} disabled={busy || !status?.is_paused} className="btn-secondary btn-sm">
              <Play className="h-4 w-4" /> Resume
            </button>
            <button onClick={() => control('stop')} disabled={busy || !status?.is_running} className="btn-danger btn-sm">
              <Square className="h-4 w-4" /> Stop
            </button>
            <button onClick={() => control('set_scenario', { scenario })} disabled={busy} className="btn-secondary btn-sm">
              <Zap className="h-4 w-4" /> Apply scenario
            </button>
          </div>

          <h2 className="text-sm font-semibold text-gray-200 mt-6 mb-3">Simulation speed</h2>
          <div className="flex items-center gap-2">
            {SPEEDS.map((sp) => (
              <button
                key={sp}
                onClick={() => control('set_speed', { speed: sp })}
                className={cn('px-3 py-1.5 rounded-lg border font-mono text-sm transition-all',
                  status?.speed === sp ? 'border-accent/50 bg-accent/10 text-accent' : 'border-white/10 text-gray-400 hover:border-white/20')}
              >
                {sp}x
              </button>
            ))}
            <span className="text-xs text-gray-600 ml-2">current: <span className="font-mono text-gray-300">{status?.speed ?? 1}x</span></span>
          </div>
        </div>

        <div className="space-y-4">
          <div className="card p-5">
            <h2 className="text-sm font-semibold text-gray-200 mb-4">Live state</h2>
            <dl className="space-y-2.5 text-sm">
              <div className="flex justify-between">
                <dt className="text-gray-500">Status</dt>
                <dd className={cn('badge', !status?.is_running ? 'badge-neutral' : status.is_paused ? 'badge-warning' : 'badge-success')}>
                  {status?.is_running ? (status.is_paused ? 'Paused' : 'Running') : 'Stopped'}
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Scenario</dt>
                <dd className="badge-info">{status ? getScenarioLabel(status.scenario) : '—'}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Sim time</dt>
                <dd className="font-mono text-gray-200">{status?.current_simulation_time ? new Date(status.current_simulation_time).toLocaleTimeString() : '—'}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Active trains</dt>
                <dd className="font-mono text-gray-200">{status?.active_trains ?? 0}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Speed</dt>
                <dd className="font-mono text-gray-200">{status?.speed ?? 1}x</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Last update</dt>
                <dd className="text-[11px] text-gray-500">{status ? new Date(status.last_update).toLocaleTimeString() : '—'}</dd>
              </div>
            </dl>
          </div>

          <div className="card p-5">
            <h2 className="text-sm font-semibold text-gray-200 mb-3">How to run the SIH demo</h2>
            <ol className="list-decimal list-inside space-y-1.5 text-xs text-gray-500">
              <li>Select a scenario (e.g. <span className="text-amber-300">SIGNAL_DELAY</span>)</li>
              <li>Press <span className="text-accent">Start</span> — the engine injects the delay</li>
              <li>Watch the train ETA drift on the train view</li>
              <li>Switch to a passenger view to see "Why ETA changed"</li>
              <li>Press <span className="text-rail-amber">Pause</span>/<span className="text-rail-green">Resume</span> to freeze/resume</li>
              <li>Select <span className="text-rail-green">RECOVERY</span> and Apply to restore schedule</li>
            </ol>
            <p className="text-[11px] text-gray-600 mt-3">
              All simulation behaviour is driven by the backend simulation engine — the UI never fabricates train movements.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}