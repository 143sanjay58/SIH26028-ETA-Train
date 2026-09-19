import { useState, useEffect } from 'react';
import { healthApi, simulationApi } from '../services/api';
import { useWebSocket } from '../contexts/WebSocketContext';
import { Server, Database, BrainCircuit, FlaskConical, Wifi, Cloud, Activity, CheckCircle2, AlertTriangle, XCircle } from 'lucide-react';
import { cn } from '../utils/helpers';
import { SectionHeader } from '../components/ui/SectionHeader';
import type { LucideIcon } from 'lucide-react';

type ServiceStatus = 'ONLINE' | 'DEGRADED' | 'OFFLINE';

function StatusPill({ status }: { status: ServiceStatus }) {
  return (
    <span className={cn('badge', status === 'ONLINE' ? 'badge-success' : status === 'DEGRADED' ? 'badge-warning' : 'badge-critical')}>
      {status}
    </span>
  );
}

function Service({ icon: Icon, name, status, detail }: { icon: LucideIcon; name: string; status: ServiceStatus; detail?: string }) {
  return (
    <div className="card p-4 flex items-center gap-3">
      <div className={cn('w-10 h-10 rounded-lg border flex items-center justify-center shrink-0',
        status === 'ONLINE' ? 'bg-rail-green/10 border-rail-green/25' : status === 'DEGRADED' ? 'bg-rail-amber/10 border-rail-amber/25' : 'bg-rail-red/10 border-rail-red/25')}>
        <Icon className={cn('h-5 w-5', status === 'ONLINE' ? 'text-rail-green' : status === 'DEGRADED' ? 'text-rail-amber' : 'text-rail-red')} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between">
          <p className="text-sm font-semibold text-gray-200">{name}</p>
          <StatusPill status={status} />
        </div>
        {detail && <p className="text-xs text-gray-500 mt-0.5 truncate">{detail}</p>}
      </div>
    </div>
  );
}

export default function SystemHealth() {
  const { isConnected } = useWebSocket();
  const [health, setHealth] = useState<Awaited<ReturnType<typeof healthApi.check>>['data'] | null>(null);
  const [sim, setSim] = useState<'ONLINE' | 'DEGRADED' | 'OFFLINE'>('OFFLINE');
  const [boot] = useState<Date>(new Date());
  const [apiOk, setApiOk] = useState<boolean | null>(null);

  useEffect(() => {
    let mounted = true;
    healthApi.check().then((res) => {
      if (!mounted) return;
      setHealth(res.data);
      setApiOk(res.data.status === 'healthy');
    }).catch(() => mounted && setApiOk(false));

    simulationApi.getStatus().then(() => mounted && setSim('ONLINE')).catch(() => mounted && setSim('OFFLINE'));
    return () => { mounted = false; };
  }, []);

  return (
    <div className="space-y-6">
      <SectionHeader title="System Status" subtitle="Health of the platform services powering RAILPULSE AI" />

      <div className="card p-5 flex items-center gap-4">
        <div className="w-12 h-12 rounded-xl bg-rail-green/10 border border-rail-green/25 flex items-center justify-center">
          <Activity className="h-6 w-6 text-rail-green animate-pulse-slow" />
        </div>
        <div>
          <p className="text-sm font-semibold text-gray-100">API Gateway</p>
          <p className="text-xs text-gray-500 mt-0.5">
            {apiOk === null ? 'Probing…' : apiOk ? `Healthy · ${health?.version ?? ''} · ${health?.environment ?? ''}` : 'Unreachable — check backend on port 8000'}
          </p>
        </div>
        <div className="ml-auto text-right">
          <p className="text-[11px] font-mono text-gray-500">booted {boot.toLocaleTimeString()}</p>
          <p className="text-[11px] font-mono text-gray-600">{health?.timestamp ? new Date(health.timestamp).toLocaleTimeString() : ''}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <Service
          icon={Server}
          name="FastAPI backend"
          status={apiOk === null ? 'DEGRADED' : apiOk ? 'ONLINE' : 'OFFLINE'}
          detail={apiOk ? health?.status : 'No response from /api/health'}
        />
        <Service
          icon={Wifi}
          name="WebSocket realtime"
          status={isConnected ? 'ONLINE' : 'DEGRADED'}
          detail={isConnected ? 'Connected to realtime feed' : 'Disconnected — reconnecting'}
        />
        <Service
          icon={Database}
          name="Database"
          status={apiOk ? (health?.database === 'ok' || health?.database === 'connected' ? 'ONLINE' : 'DEGRADED') : 'OFFLINE'}
          detail={health?.database ?? 'Unknown'}
        />
        <Service
          icon={FlaskConical}
          name="Simulation engine"
          status={sim}
          detail={sim === 'ONLINE' ? 'Simulation service responding' : 'No response — start backend'}
        />
        <Service
          icon={BrainCircuit}
          name="ML / ETA engine"
          status={apiOk ? 'ONLINE' : 'OFFLINE'}
          detail="ETA prediction endpoints available"
        />
        <Service
          icon={Cloud}
          name="Weather provider"
          status={apiOk ? 'ONLINE' : 'OFFLINE'}
          detail="Weather endpoints available via backend"
        />
      </div>

      <div className="card p-5">
        <h2 className="text-sm font-semibold text-gray-200 mb-3">Endpoint probes</h2>
        <ul className="space-y-1.5 text-xs font-mono text-gray-500">
          <li className="flex items-center gap-2">
            <CheckCircle2 className="h-3.5 w-3.5 text-rail-green" /> GET /api/health {apiOk === false && '— failed'}
          </li>
          <li className="flex items-center gap-2">
            {sim === 'ONLINE' ? <CheckCircle2 className="h-3.5 w-3.5 text-rail-green" /> : <XCircle className="h-3.5 w-3.5 text-rail-red" />} GET /api/simulation/status
          </li>
          <li className="flex items-center gap-2">
            {isConnected ? <CheckCircle2 className="h-3.5 w-3.5 text-rail-green" /> : <AlertTriangle className="h-3.5 w-3.5 text-rail-amber" />} WS /ws/{'{channel}'}
          </li>
        </ul>
      </div>
    </div>
  );
}