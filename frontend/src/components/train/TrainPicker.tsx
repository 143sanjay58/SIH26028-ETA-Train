import { useEffect, useRef, useState } from 'react';
import { Loader2, Search, MapPin, ArrowRight } from 'lucide-react';
import { trainApi } from '../../services/api';
import { cn } from '../../utils/helpers';
import type { Train, CatalogueTrain } from '../../types';

export interface TrainOption {
  key: string;
  train_number: string;
  train_name: string;
  origin: string;
  destination: string;
  source: 'DB' | 'SIH_CATALOGUE';
  trainId?: number;
  catalogue?: CatalogueTrain;
}

interface TrainPickerProps {
  value: TrainOption | null;
  onChange: (opt: TrainOption | null) => void;
  placeholder?: string;
  disabled?: boolean;
  hint?: string;
}

function toOption(train: Train): TrainOption {
  return {
    key: `db-${train.id}`,
    train_number: train.train_number,
    train_name: train.train_name,
    origin: train.origin_station?.name ?? `#${train.origin_station_id}`,
    destination: train.destination_station?.name ?? `#${train.destination_station_id}`,
    source: 'DB',
    trainId: train.id,
  };
}

function toCatalogueOption(c: CatalogueTrain): TrainOption {
  return {
    key: `cat-${c.train_number}`,
    train_number: c.train_number,
    train_name: c.train_name ?? c.train_number,
    origin: c.origin_station_name ?? c.origin_station,
    destination: c.destination_station_name ?? c.destination_station,
    source: 'SIH_CATALOGUE',
    catalogue: c,
  };
}

export function TrainPicker({ value, onChange, placeholder, disabled, hint }: TrainPickerProps) {
  const rootRef = useRef<HTMLDivElement>(null);
  const [dbTrains, setDbTrains] = useState<Train[]>([]);
  const [query, setQuery] = useState('');
  const [open, setOpen] = useState(false);
  const [searching, setSearching] = useState(false);
  const [results, setResults] = useState<TrainOption[]>([]);

  useEffect(() => {
    let mounted = true;
    trainApi
      .list({ page_size: 100 })
      .then((res) => { if (mounted) setDbTrains(res.data.trains || []); })
      .catch(() => { /* ignore */ });
    return () => { mounted = false; };
  }, []);

  useEffect(() => {
    const q = query.trim();
    if (q.length < 3) {
      setSearching(false);
      if (results.length) setResults([]);
      return;
    }
    let cancelled = false;
    setSearching(true);
    const timer = setTimeout(async () => {
      const norm = q.toLowerCase();
      const dbMatches: TrainOption[] = dbTrains
        .filter((t) => t.train_number.toLowerCase().includes(norm) || t.train_name.toLowerCase().includes(norm))
        .slice(0, 6)
        .map(toOption);
      const catalogueRes = await trainApi.search(q, 10).catch(() => null);
      if (cancelled) return;
      const rows = [...dbMatches];
      (catalogueRes?.data || []).forEach((c) => {
        if (!rows.some((r) => r.train_number === c.train_number)) rows.push(toCatalogueOption(c));
      });
      setResults(rows);
      setOpen(true);
      setSearching(false);
    }, 300);
    return () => { cancelled = true; clearTimeout(timer); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query, dbTrains]);

  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [open]);

  if (value) {
    return (
      <div className="rounded-lg border border-white/10 bg-surface-200/60 px-3 py-2.5">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-3 min-w-0">
            <span className="font-mono font-bold text-sm text-gray-100 shrink-0">{value.train_number}</span>
            <span className="text-sm text-gray-300 truncate">{value.train_name}</span>
            <span className="hidden sm:flex items-center gap-1 text-xs text-gray-500 min-w-0">
              <MapPin className="h-3 w-3 shrink-0" />
              <span className="truncate">{value.origin}</span>
              <ArrowRight className="h-3 w-3 shrink-0" />
              <span className="truncate">{value.destination}</span>
            </span>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <span className={cn(value.source === 'SIH_CATALOGUE' ? 'badge-sih-eta' : 'badge-sim')}>
              {value.source === 'SIH_CATALOGUE' ? 'SIH Catalogue' : 'Registered'}
            </span>
            {!disabled && (
              <button type="button" onClick={() => { setResults([]); setQuery(''); onChange(null); }} className="btn-ghost btn-sm" aria-label="Change train">
                <Search className="h-3.5 w-3.5" /> Change
              </button>
            )}
          </div>
        </div>
        {disabled && hint && <p className="text-[11px] text-gray-600 mt-1.5">{hint}</p>}
      </div>
    );
  }

  return (
    <div className="relative" ref={rootRef}>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
        <input
          type="text"
          value={query}
          disabled={disabled}
          onChange={(e) => { setQuery(e.target.value); if (!e.target.value) setOpen(false); }}
          onFocus={() => results.length && setOpen(true)}
          placeholder={placeholder ?? 'Search train number or name…'}
          className={cn('input pl-9', disabled && 'opacity-60')}
          aria-label="Search trains"
        />
        {searching && <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-accent animate-spin" />}
      </div>
      {hint && <p className="text-[11px] text-gray-600 mt-1.5">{hint}</p>}

      {open && (
        <div className="absolute top-11 left-0 right-0 bg-surface-200 border border-white/10 rounded-xl shadow-2xl overflow-hidden z-50 animate-slide-up">
          {query.trim().length < 3 ? (
            <div className="px-4 py-3 text-sm text-gray-500">Type at least 3 characters to search trains.</div>
          ) : searching ? (
            <div className="px-4 py-3 text-sm text-gray-500 flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin text-accent" /> Searching trains…
            </div>
          ) : results.length === 0 ? (
            <div className="px-4 py-3 text-sm text-gray-500">
              <p>No trains found.</p>
              <p className="text-xs text-gray-600 mt-1">Try a train number like 02082 or 12303.</p>
            </div>
          ) : (
            results.map((r) => (
              <button
                key={r.key}
                type="button"
                onClick={() => { setOpen(false); setQuery(''); onChange(r); }}
                className="w-full flex items-center gap-3 px-4 py-3 hover:bg-white/[0.04] transition-colors text-left"
              >
                <span className="font-mono font-bold text-sm text-gray-100 shrink-0">{r.train_number}</span>
                <span className="flex items-center gap-1 text-xs text-gray-500 min-w-0 truncate">
                  <MapPin className="h-3 w-3 shrink-0" />
                  <span className="truncate">{r.origin}</span>
                  <ArrowRight className="h-3 w-3 shrink-0" />
                  <span className="truncate">{r.destination}</span>
                </span>
                <span className="ml-auto shrink-0">{r.source === 'SIH_CATALOGUE' ? <span className="badge-sih-eta">Catalogue</span> : <span className="badge-sim">Registered</span>}</span>
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
}