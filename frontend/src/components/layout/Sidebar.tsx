import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutGrid,
  Train,
  Navigation,
  Brain,
  Gauge,
  CloudRain,
  Bell,
  BarChart3,
  FlaskConical,
  Building2,
  Activity as ActivityIcon,
  User,
  LogOut,
  Radio,
  RadioTower,
  PanelLeftClose,
  PanelLeft,
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { cn, roleLabel } from '../../utils/helpers';
import type { LucideIcon } from 'lucide-react';

interface NavItem {
  path: string;
  label: string;
  icon: LucideIcon;
  roles?: string[];
  match?: (path: string) => boolean;
}

const passengerItems: NavItem[] = [
  { path: '/', label: 'Overview', icon: LayoutGrid, match: (p) => p === '/' },
  { path: '/trains', label: 'Live Trains', icon: Train },
  { path: '/map', label: 'Railway Map', icon: Navigation },
  { path: '/eta', label: 'AI ETA', icon: Brain },
];

const railwayItems: NavItem[] = [
  { path: '/delay-intel', label: 'Delay Intelligence', icon: Gauge, roles: ['STATION_STAFF', 'SUPERVISOR', 'OPERATOR', 'ADMIN'] },
  { path: '/weather', label: 'Weather', icon: CloudRain },
  { path: '/alerts', label: 'Alerts', icon: Bell, roles: ['STATION_STAFF', 'SUPERVISOR', 'OPERATOR', 'ADMIN'] },
  { path: '/analytics', label: 'Analytics', icon: BarChart3, roles: ['STATION_STAFF', 'SUPERVISOR', 'OPERATOR', 'ADMIN'] },
  { path: '/simulation', label: 'Simulation Lab', icon: FlaskConical, roles: ['STATION_STAFF', 'SUPERVISOR', 'OPERATOR', 'ADMIN'] },
  { path: '/station-master', label: 'Station Operations', icon: Building2, roles: ['STATION_STAFF', 'SUPERVISOR', 'OPERATOR', 'ADMIN'] },
  { path: '/co-pilot', label: 'Train Co-Pilot', icon: RadioTower, roles: ['STATION_STAFF'] },
  { path: '/control-room', label: 'Control Room', icon: Radio, roles: ['SUPERVISOR', 'OPERATOR', 'ADMIN'] },
];

const bottomItems: NavItem[] = [
  { path: '/system-health', label: 'System Status', icon: ActivityIcon },
];

export function Logo({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' }) {
  const dims = size === 'lg' ? 'h-10 w-10' : size === 'sm' ? 'h-8 w-8' : 'h-9 w-9';
  const textSize = size === 'lg' ? 'text-xl' : 'text-base';
  return (
    <div className="flex items-center gap-2.5 select-none">
      <div className={cn(dims, 'rounded-lg bg-gradient-to-br from-accent to-violet-500 flex items-center justify-center relative shadow-glow-sm shrink-0')}>
        <Train className={cn(size === 'lg' ? 'h-5 w-5' : 'h-4 w-4', 'text-surface-50')} strokeWidth={2.5} />
      </div>
      <div className="min-w-0">
        <p className={cn(textSize, 'font-extrabold tracking-tight text-gray-100 leading-none')}>
          RAIL<span className="text-accent">PULSE</span>
        </p>
        <p className="text-[9px] font-semibold tracking-[0.22em] text-gray-500 mt-0.5 uppercase">
          Real-Time Railway Intelligence
        </p>
      </div>
    </div>
  );
}

export function Sidebar({ collapsed, onToggle, onNavigate }: { collapsed: boolean; onToggle: () => void; onNavigate?: () => void }) {
  const { user, logout } = useAuth();
  const location = useLocation();
  const role = user?.role || '';

  const canSee = (item: NavItem) => !item.roles || item.roles.includes(role);

  const isActive = (item: NavItem) => (item.match ? item.match(location.pathname) : location.pathname.startsWith(item.path));

  const renderItem = (item: NavItem) => {
    if (!canSee(item)) return null;
    const active = isActive(item);
    return (
      <NavLink
        key={item.path}
        to={item.path}
        onClick={onNavigate}
        className={cn('sidebar-item', active && 'active')}
        aria-current={active ? 'page' : undefined}
        title={collapsed ? item.label : undefined}
      >
        <item.icon className="h-5 w-5 shrink-0" />
        {!collapsed && <span className="truncate">{item.label}</span>}
      </NavLink>
    );
  };

  return (
    <aside
      className={cn(
        'fixed inset-y-0 left-0 z-50 flex flex-col bg-surface-100 border-r border-white/[0.06]',
        'transition-[width] duration-300 ease-in-out',
        collapsed ? 'w-[68px]' : 'w-60'
      )}
    >
      <div className="h-14 flex items-center justify-between px-3 border-b border-white/[0.06]">
        {!collapsed && <Logo />}
        <button
          onClick={onToggle}
          className="p-1.5 rounded-lg text-gray-500 hover:text-gray-200 hover:bg-white/[0.06] transition-colors mx-auto"
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          title={collapsed ? 'Expand' : 'Collapse'}
        >
          {collapsed ? <PanelLeft className="h-4 w-4" /> : <PanelLeftClose className="h-4 w-4" />}
        </button>
      </div>

      <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-0.5">
        {!collapsed && (
          <p className="px-3 py-1.5 text-[10px] font-semibold uppercase tracking-widest text-gray-600">Passenger Mode</p>
        )}
        {!collapsed && passengerItems.map(renderItem)}

        {!collapsed && (
          <p className="px-3 pt-4 pb-1.5 text-[10px] font-semibold uppercase tracking-widest text-gray-600">Railway Mode</p>
        )}
        {!collapsed && railwayItems.map(renderItem)}

        <div className={cn(collapsed ? 'border-t border-white/[0.06] mt-2 pt-2' : 'hidden')} />
        {!collapsed && (
          <p className="px-3 pt-4 pb-1.5 text-[10px] font-semibold uppercase tracking-widest text-gray-600">System</p>
        )}
        {bottomItems.map(renderItem)}
      </nav>

      <div className="p-2 border-t border-white/[0.06] space-y-1">
        {!collapsed && user && (
          <div className="px-3 py-2 flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-violet/15 border border-violet/20 flex items-center justify-center shrink-0">
              <User className="h-4 w-4 text-violet-300" />
            </div>
            <div className="min-w-0">
              <p className="text-sm font-medium text-gray-200 truncate">{user.full_name || user.username}</p>
              <p className="text-[11px] text-gray-500 capitalize">{roleLabel(user.role)}</p>
            </div>
          </div>
        )}
        <button
          onClick={logout}
          className={cn('sidebar-item w-full text-rail-red/80 hover:text-rail-red hover:bg-rail-red/10')}
          title={collapsed ? 'Logout' : undefined}
        >
          <LogOut className="h-5 w-5 shrink-0" />
          {!collapsed && <span>Logout</span>}
        </button>
      </div>
    </aside>
  );
}