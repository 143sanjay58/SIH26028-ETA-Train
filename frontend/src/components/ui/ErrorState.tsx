import { AlertTriangle, RefreshCw } from 'lucide-react';

export function ErrorState({
  title = 'Unable to retrieve data',
  message,
  onRetry,
  lastUpdate,
}: {
  title?: string;
  message?: string;
  onRetry?: () => void;
  lastUpdate?: string;
}) {
  return (
    <div className="card p-8 flex flex-col items-center justify-center text-center" role="alert">
      <div className="w-14 h-14 rounded-xl bg-rail-red/10 border border-rail-red/20 flex items-center justify-center mb-4">
        <AlertTriangle className="h-7 w-7 text-rail-red" />
      </div>
      <h3 className="text-sm font-semibold text-gray-200">{title}</h3>
      {message && <p className="text-sm text-gray-500 mt-1 max-w-md">{message}</p>}
      {onRetry && (
        <button onClick={onRetry} className="btn-secondary btn-sm mt-4">
          <RefreshCw className="h-3.5 w-3.5" /> Retry
        </button>
      )}
      {lastUpdate && (
        <p className="text-xs text-gray-600 mt-3 font-mono">Last update: {lastUpdate}</p>
      )}
    </div>
  );
}