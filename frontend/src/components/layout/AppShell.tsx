import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { cn } from '../../utils/helpers';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';

export function AppShell() {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="min-h-screen bg-surface-50">
      <div className="fixed inset-0 bg-grid-pattern bg-grid pointer-events-none" aria-hidden="true" />
      <div className="fixed inset-0 bg-radial-glow pointer-events-none" aria-hidden="true" />

      <div
        className={cn(
          'relative z-10 flex min-h-screen transition-all duration-300',
          collapsed ? 'lg:pl-[68px]' : 'lg:pl-60'
        )}
      >
        <div className="hidden lg:block fixed inset-y-0 left-0 z-50">
          <Sidebar collapsed={collapsed} onToggle={() => setCollapsed((c) => !c)} />
        </div>

        {mobileOpen && (
          <div className="fixed inset-0 z-40 lg:hidden">
            <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setMobileOpen(false)} />
            <div className="absolute inset-y-0 left-0">
              <Sidebar collapsed={false} onToggle={() => setMobileOpen(false)} onNavigate={() => setMobileOpen(false)} />
            </div>
          </div>
        )}

        <div className="flex-1 flex flex-col min-w-0">
          <TopBar onMenuClick={() => setMobileOpen(true)} />
          <main className="flex-1 px-4 lg:px-6 py-5 overflow-x-hidden">
            <div className="max-w-[1600px] mx-auto">
              <Outlet />
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}