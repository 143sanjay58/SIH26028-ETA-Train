import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Bell, RefreshCw, Menu } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { useWebSocket } from '../../contexts/WebSocketContext';
import { GlobalSearch } from './GlobalSearch';
import { cn } from '../../utils/helpers';
import type { Alert } from '../../types';
import { alertApi } from '../../services/api';

function getConnectionState(isConnected: boolean, hasConnected: boolean) {
  if (isConnected) return { label: 'LIVE', dot: 'bg-rail-green shadow-glow-green', pulse: true };
  if (hasConnected) return { label: 'RECONNECTING', dot: 'bg-rail-amber shadow-glow', pulse: true };
  return { label: 'OFFLINE', dot: 'bg-rail-red', pulse: false };
}

export function TopBar({ onMenuClick, pageTitle }: { onMenuClick: () => void; pageTitle?: string }) {
  const { user } = useAuth();
  const { isConnected } = useWebSocket();
  const navigate = useNavigate();
  const location = useLocation();
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [showAlerts, setShowAlerts] = useState(false);

  useEffect(() => {
    const interval = setInterval(() => setLastUpdate(new Date()), 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    alertApi.list({ active_only: true }).then((res) => setAlerts(res.data)).catch(() => {});
  }, [location.pathname]);

  const conn = getConnectionState(isConnected, true);
  const unread = alerts.filter((a) => !a.is_acknowledged).length;

  const secondsAgo = Math.max(0, Math.round((Date.now() - lastUpdate.getTime()) / 1000));

  const titles: Record<string, string> = {
    '/': 'Overview',
    '/trains': 'Live Trains',
    '/map': 'Railway Map',
    '/eta': 'AI ETA Engine',
    '/delay-intel': 'Delay Intelligence',
    '/weather': 'Weather Intelligence',
    '/alerts': 'Operations Alert Center',
    '/analytics': 'Analytics',
    '/simulation': 'Simulation Lab',
    '/station-master': 'Station Operations',
    '/co-pilot': 'Train Co-Pilot',
    '/control-room': 'Railway Operations Center',
    '/system-health': 'System Status',
    '/settings': 'Profile',
  };

  const title = pageTitle || titles[location.pathname] || 'RailPulse';

  return (
    <header className="sticky top-0 z-40 h-14 bg-surface-100/80 backdrop-blur-md border-b border-white/[0.06]">
      <div className="flex items-center gap-3 h-full px-3 lg:px-5">
        <button onClick={onMenuClick} className="lg:hidden p-1.5 rounded-lg text-gray-400 hover:text-gray-200 hover:bg-white/[0.06]" aria-label="Toggle menu">
          <Menu className="h-5 w-5" />
        </button>

        <div className="flex items-center gap-2 text-sm font-medium text-gray-200 min-w-0">
          <span className="hidden sm:inline text-gray-600">RAILPULSE AI</span>
          <span className="hidden sm:inline text-gray-700">/</span>
          <span className="truncate">{title}</span>
        </div>

        <div className="hidden md:block flex-1 max-w-sm ml-auto">
          <GlobalSearch />
        </div>

        <div className="flex items-center gap-2 ml-auto md:ml-0 shrink-0">
          <div className={cn('hidden lg:flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-white/10 bg-surface-200/80')} aria-live="polite">
            <span className={cn('w-2 h-2 rounded-full', conn.dot, conn.pulse && 'animate-pulse-slow')} />
            <span className={cn('text-[11px] font-bold tracking-wider', conn.label === 'LIVE' ? 'text-rail-green' : conn.label === 'RECONNECTING' ? 'text-rail-amber' : 'text-rail-red')}>
              {conn.label}
            </span>
          </div>
          <div className="hidden xl:flex items-center gap-1 text-[11px] text-gray-500">
            <RefreshCw className="h-3 w-3 text-gray-600" />
            <span>Updated {secondsAgo}s ago</span>
          </div>

          <div className="relative">
            <button
              onClick={() => setShowAlerts((s) => !s)}
              className="relative p-2 rounded-lg text-gray-400 hover:text-gray-200 hover:bg-white/[0.06] transition-colors"
              aria-label={`Notifications${unread ? ` (${unread} unread)` : ''}`}
            >
              <Bell className="h-5 w-5" />
              {unread > 0 && (
                <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-rail-red shadow-glow-red" />
              )}
            </button>
            {showAlerts && (
              <div className="absolute right-0 top-11 w-80 bg-surface-200 border border-white/10 rounded-xl shadow-2xl overflow-hidden z-50 animate-slide-up" role="menu">
                <div className="px-4 py-3 border-b border-white/[0.06] flex items-center justify-between">
                  <p className="text-sm font-semibold text-gray-200">Active Alerts</p>
                  <button onClick={() => navigate('/alerts')} className="text-xs text-accent hover:underline">View all</button>
                </div>
                <div className="max-h-72 overflow-y-auto">
                  {alerts.length === 0 && (
                    <p className="px-4 py-6 text-center text-sm text-gray-500">No active alerts</p>
                  )}
                  {alerts.slice(0, 10).map((a) => (
                    <button
                      key={a.id}
                      onClick={() => { setShowAlerts(false); if (a.train_id) navigate(`/train/${a.train_id}`); }}
                      className="w-full px-4 py-3 text-left hover:bg-white/[0.04] transition-colors border-b border-white/[0.03]"
                    >
                      <div className="flex items-center gap-2 mb-0.5">
                        <span className={cn('w-1.5 h-1.5 rounded-full', a.severity === 'CRITICAL' ? 'bg-rail-red' : a.severity === 'WARNING' ? 'bg-rail-amber' : 'bg-rail-blue')} />
                        <span className="text-xs font-semibold text-gray-200">{a.alert_type.replace(/_/g, ' ')}</span>
                      </div>
                      <p className="text-xs text-gray-400">{a.title}</p>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          <button
            onClick={() => navigate('/settings')}
            className="p-2 rounded-lg text-gray-400 hover:text-gray-200 hover:bg-white/[0.06] transition-colors"
            aria-label="Profile"
          >
            <div className="w-6 h-6 rounded-md bg-violet/15 border border-violet/20 flex items-center justify-center text-[11px] font-bold text-violet-300">
              {(user?.full_name || user?.username || 'U').charAt(0).toUpperCase()}
            </div>
          </button>
        </div>
      </div>
    </header>
  );
}