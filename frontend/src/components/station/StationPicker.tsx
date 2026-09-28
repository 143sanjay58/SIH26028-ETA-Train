import { useEffect, useMemo, useRef, useState } from 'react';
import { MapPin, Search } from 'lucide-react';
import { cn } from '../../utils/helpers';
import type { Station } from '../../types';

export interface StationOption {
  key: string;
  id?: number;
  code: string;
  name: string;
  state?: string | null;
}

type StationPickerMode = 'all' | 'route';
type RouteStatus = 'idle' | 'loading' | 'ready' | 'unavailable';

interface StationPickerProps {
  options: StationOption[] | null;
  value: StationOption | null;
  onChange: (opt: StationOption | null) => void;
  placeholder?: string;
  disabled?: boolean;
  hint?: string;
  mode?: StationPickerMode;
  routeStatus?: RouteStatus;
}

export function toStationOption(s: Station): StationOption {
  return { key: `s-${s.id}`, id: s.id, code: s.code, name: s.name, state: s.state ?? null };
}

export function StationPicker({ options, value, onChange, placeholder, disabled, hint, mode = 'all', routeStatus = 'idle' }: StationPickerProps) {
  const rootRef = useRef<HTMLDivElement>(null);
  const [query, setQuery] = useState('');
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [open]);

  const filtered = useMemo(() => {
    const base = options ?? [];
    const q = query.trim().toLowerCase();
    if (!q) return base.slice(0, 8);
    return base
      .filter((s) => s.code.toLowerCase().includes(q) || s.name.toLowerCase().includes(q))
      .slice(0, 8);
  }, [query, options]);

  if (value) {
    return (
      <div className="rounded-lg border border-white/10 bg-surface-200/60 px-3 py-2.5">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2.5 min-w-0">
            <span className="font-mono font-bold text-sm text-gray-100 shrink-0">{value.code}</span>
            <span className="text-sm text-gray-300 truncate">{value.name}</span>
            {value.state && <span className="hidden sm:inline text-xs text-gray-500 shrink-0">{value.state}</span>}
          </div>
          {!disabled && (
            <button
              type="button"
              onClick={() => { setQuery(''); onChange(null); }}
              className="btn-ghost btn-sm"
              aria-label="Change station"
            >
              <Search className="h-3.5 w-3.5" /> Change
            </button>
          )}
        </div>
        {disabled && hint && <p className="text-[11px] text-gray-600 mt-1.5">{hint}</p>}
      </div>
    );
  }

  const routeNotice =
    mode === 'route'
      ? routeStatus === 'loading'
        ? 'Loading train route...'
        : routeStatus === 'unavailable'
          ? 'Route information unavailable for this train.'
          : routeStatus === 'idle' || !options || options.length === 0
            ? 'Select a train first.'
            : null
      : null;

  if (routeNotice) {
    return (
      <div>
        <div className="rounded-lg border border-dashed border-white/10 bg-surface-200/40 px-3 py-2.5 text-sm text-gray-600">
          {routeNotice}
        </div>
        {hint && <p className="text-[11px] text-gray-600 mt-1.5">{hint}</p>}
      </div>
    );
  }

  if (mode === 'all' && options === null) {
    return (
      <div>
        <div className="rounded-lg border border-dashed border-white/10 bg-surface-200/40 px-3 py-2.5 text-sm text-gray-600">
          Loading stations…
        </div>
        {hint && <p className="text-[11px] text-gray-600 mt-1.5">{hint}</p>}
      </div>
    );
  }

  const base = options ?? [];
  if (mode === 'all' && base.length === 0) {
    return (
      <div>
        <div className="rounded-lg border border-dashed border-white/10 bg-surface-200/40 px-3 py-2.5 text-sm text-gray-600">
          No stations available.
        </div>
        {hint && <p className="text-[11px] text-gray-600 mt-1.5">{hint}</p>}
      </div>
    );
  }

  return (
    <div className="relative" ref={rootRef}>
      <div className="relative">
        <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
        <input
          type="text"
          value={query}
          disabled={disabled}
          onChange={(e) => { setQuery(e.target.value); if (!e.target.value) setOpen(false); }}
          onFocus={() => { if (base.length > 0) setOpen(true); }}
          placeholder={placeholder ?? 'Search station code or name…'}
          className={cn('input pl-9', disabled && 'opacity-60')}
          aria-label="Search stations"
        />
      </div>
      {hint && <p className="text-[11px] text-gray-600 mt-1.5">{hint}</p>}

      {open && (
        <div className="absolute top-11 left-0 right-0 max-h-64 overflow-y-auto bg-surface-200 border border-white/10 rounded-xl shadow-2xl z-50 animate-slide-up">
          {filtered.length === 0 ? (
            <div className="px-4 py-3 text-sm text-gray-500">No stations match "{query.trim()}".</div>
          ) : (
            filtered.map((s) => (
              <button
                key={s.key}
                type="button"
                onClick={() => { setOpen(false); setQuery(''); onChange(s); }}
                className="w-full flex items-center gap-3 px-4 py-3 hover:bg-white/[0.04] transition-colors text-left"
              >
                <span className="font-mono font-bold text-sm text-gray-100 shrink-0">{s.code}</span>
                <span className="text-sm text-gray-300 truncate">{s.name}</span>
                {mode === 'route' && s.id === undefined && (
                  <span className="ml-auto shrink-0 text-[11px] text-gray-600">Not registered</span>
                )}
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
}