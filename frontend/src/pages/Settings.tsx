import { useAuth } from '../contexts/AuthContext';
import { useWebSocket } from '../contexts/WebSocketContext';
import { User, Wifi, WifiOff, Shield, Construction } from 'lucide-react';
import { cn } from '../utils/helpers';
import { SectionHeader } from '../components/ui/SectionHeader';

export default function Settings() {
  const { user } = useAuth();
  const { isConnected } = useWebSocket();

  return (
    <div className="space-y-6 max-w-3xl">
      <SectionHeader title="Profile" subtitle="Account details and platform status" />

      <div className="card p-5">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-xl bg-violet/15 border border-violet/25 flex items-center justify-center">
            <User className="h-7 w-7 text-violet-300" />
          </div>
          <div className="min-w-0">
            <p className="text-lg font-semibold text-gray-100">{user?.full_name || user?.username}</p>
            <p className="text-sm text-gray-500 capitalize">{user?.role?.toLowerCase().replace('_', ' ')}</p>
            <p className="text-xs text-gray-600 font-mono mt-0.5">{user?.email}</p>
          </div>
        </div>
        <dl className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-6 text-sm">
          <div className="p-3 rounded-lg bg-white/[0.03] flex justify-between">
            <dt className="text-gray-500">Username</dt>
            <dd className="font-mono text-gray-200">{user?.username}</dd>
          </div>
          <div className="p-3 rounded-lg bg-white/[0.03] flex justify-between">
            <dt className="text-gray-500">Assigned station</dt>
            <dd className="font-mono text-gray-200">{user?.station_id ?? 'Not assigned'}</dd>
          </div>
          <div className="p-3 rounded-lg bg-white/[0.03] flex justify-between">
            <dt className="text-gray-500">Realtime channel</dt>
            <dd className="font-mono text-gray-200">{user?.role === 'PASSENGER' ? 'trains' : 'control-room'}</dd>
          </div>
          <div className="p-3 rounded-lg bg-white/[0.03] flex justify-between">
            <dt className="text-gray-500">Verified</dt>
            <dd className="text-gray-200">{user?.is_verified ? 'Yes' : 'No'}</dd>
          </div>
        </dl>
      </div>

      <div className="card p-5">
        <h2 className="text-sm font-semibold text-gray-200 mb-3">Connection status</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="flex items-center gap-3 p-3 rounded-lg bg-white/[0.03]">
            {isConnected ? <Wifi className="h-5 w-5 text-rail-green" /> : <WifiOff className="h-5 w-5 text-rail-red" />}
            <div>
              <p className="text-xs text-gray-500">WebSocket</p>
              <p className="text-sm font-medium text-gray-200">{isConnected ? 'Connected' : 'Disconnected'}</p>
            </div>
          </div>
          <div className="flex items-center gap-3 p-3 rounded-lg bg-white/[0.03]">
            <Shield className="h-5 w-5 text-rail-green" />
            <div>
              <p className="text-xs text-gray-500">Authentication</p>
              <p className="text-sm font-medium text-gray-200">Authenticated</p>
            </div>
          </div>
        </div>
      </div>

      <div className="card border-dashed border-white/10 p-5 flex items-start gap-3">
        <Construction className={cn('h-5 w-5 text-rail-amber shrink-0 mt-0.5')} />
        <div>
          <h2 className="text-sm font-semibold text-gray-200">Preferences — prototype</h2>
          <p className="text-sm text-gray-500 mt-1">
            Notification and appearance preferences are <strong className="text-gray-300">not saved</strong> because the
            backend does not yet expose a settings endpoint. This section is shown for demonstration only.
          </p>
        </div>
      </div>
    </div>
  );
}