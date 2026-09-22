import { cn } from '../../utils/helpers';

export function SpeedGauge({
  speed,
  max = 130,
  source,
}: {
  speed?: number;
  max?: number;
  source?: string;
}) {
  const safeSpeed = speed !== undefined && Number.isFinite(speed) ? speed : 0;
  const pct = Math.min(1, safeSpeed / max);
  const angle = -90 + pct * 180;

  const polygonPoints = (() => {
    const center = 90;
    const len = 68;
    const rad = (angle * Math.PI) / 180;
    const x2 = center + len * Math.cos(rad);
    const y2 = center + len * Math.sin(rad);
    return `${center},${center} ${center + 14 * Math.cos(((-90 + 15) * Math.PI) / 180)},${center + 14 * Math.sin(((-90 + 15) * Math.PI) / 180)} ${x2},${y2}`;
  })();

  return (
    <div className="flex flex-col items-center">
      <div className="relative" style={{ width: 180, height: 110 }}>
        <svg viewBox="0 0 180 110" className="w-full h-full overflow-visible">
          <path
            d="M 20 105 A 70 70 0 0 1 160 105"
            fill="none"
            stroke="rgba(255,255,255,0.08)"
            strokeWidth="10"
            strokeLinecap="round"
          />
          <path
            d="M 20 105 A 70 70 0 0 1 160 105"
            fill="none"
            stroke="url(#gaugeGrad)"
            strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray="220"
            strokeDashoffset={220 - 220 * pct}
            style={{ transition: 'stroke-dashoffset 0.8s cubic-bezier(0.4,0,0.2,1)' }}
          />
          <defs>
            <linearGradient id="gaugeGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#10b981" />
              <stop offset="60%" stopColor="#00d4ff" />
              <stop offset="100%" stopColor="#8b5cf6" />
            </linearGradient>
          </defs>
          <polygon points={polygonPoints} fill="#00d4ff" style={{ transition: 'all 0.8s cubic-bezier(0.4,0,0.2,1)' }}>
            <animate attributeName="opacity" values="0.6;1;0.6" dur="2s" repeatCount="indefinite" />
          </polygon>
          <circle cx="90" cy="90" r="6" fill="#e5e7eb" />
        </svg>
        <div className="absolute inset-x-0 bottom-0 text-center">
          <span className="font-mono text-3xl font-bold text-gray-100 tabular-nums">
            {speed !== undefined && Number.isFinite(speed) ? speed.toFixed(0) : '--'}
          </span>
          <span className="text-sm text-gray-500 ml-1">km/h</span>
        </div>
      </div>
      <div className="flex justify-between w-full px-6 text-[10px] font-mono text-gray-600 mt-1">
        <span>0</span>
        <span>{max}</span>
      </div>
      {source && (
        <span className={cn('mt-2 badge-neutral')}>{source}</span>
      )}
    </div>
  );
}