import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Train as TrainIcon, Loader2, Navigation, Clock, MapPin } from 'lucide-react';
import { trainApi } from '../../services/api';

interface SearchResult {
  train_number: string;
  train_name: string;
  origin?: string;
  destination?: string;
}

export function GlobalSearch() {
  const [query, setQuery] = useState('');
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await trainApi.getByNumber(query.trim().toUpperCase());
      const t = res.data;
      setResults([{
        train_number: t.train_number,
        train_name: t.train_name,
        origin: t.origin_station?.name,
        destination: t.destination_station?.name,
      }]);
      setOpen(true);
    } catch {
      setResults([]);
      setError('No train found with that number.');
      setOpen(true);
    } finally {
      setLoading(false);
    }
  };

  const select = (number: string) => {
    setOpen(false);
    setQuery('');
    navigate(`/train/${number}`);
  };

  return (
    <div className="relative w-full max-w-md">
      <form onSubmit={handleSearch} role="search">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
          <input
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              if (!e.target.value) setOpen(false);
            }}
            onFocus={() => results.length && setOpen(true)}
            placeholder="Search train number… e.g. 12627"
            className="input pl-9 h-9 text-sm bg-surface-200/80"
            aria-label="Search trains"
          />
          {loading && <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-accent animate-spin" />}
        </div>
      </form>

      {open && (
        <div className="absolute top-11 left-0 right-0 bg-surface-200 border border-white/10 rounded-xl shadow-2xl overflow-hidden z-50 animate-slide-up">
          {error && (
            <div className="px-4 py-3 text-sm text-rail-red">
              <p>{error}</p>
              <p className="text-xs text-gray-500 mt-1">Try a train number like 12627.</p>
            </div>
          )}
          {results.length === 0 && !error && (
            <div className="px-4 py-3 text-sm text-gray-500">Waiting for search…</div>
          )}
          {results.map((r) => (
            <button
              key={r.train_number}
              onClick={() => select(r.train_number)}
              className="w-full flex items-center gap-3 px-4 py-3 hover:bg-white/[0.04] transition-colors text-left"
            >
              <div className="w-9 h-9 rounded-lg bg-accent/10 border border-accent/20 flex items-center justify-center shrink-0">
                <TrainIcon className="h-4 w-4 text-accent" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-mono font-bold text-sm text-gray-100">{r.train_number}</span>
                  <span className="text-sm text-gray-300 truncate">{r.train_name}</span>
                </div>
                <div className="flex items-center gap-3 text-xs text-gray-500 mt-0.5">
                  <span className="flex items-center gap-1"><MapPin className="h-3 w-3" />{r.origin || '—'}</span>
                  <span className="flex items-center gap-1"><Navigation className="h-3 w-3" />{r.destination || '—'}</span>
                </div>
              </div>
              <Clock className="h-4 w-4 text-gray-600" />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}