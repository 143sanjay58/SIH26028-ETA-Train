import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
} from 'recharts';
import { cn } from '../../utils/helpers';

export const tooltipStyle = {
  backgroundColor: '#161820',
  border: '1px solid rgba(255,255,255,0.1)',
  borderRadius: 8,
  fontSize: 12,
  color: '#e5e7eb',
};

export function HorizontalBars({ data, accent = '#00d4ff' }: { data: { name: string; value: number }[]; accent?: string }) {
  return (
    <ResponsiveContainer width="100%" height={Math.max(180, data.length * 42)}>
      <BarChart data={data} layout="vertical" margin={{ left: 8, right: 20 }}>
        <CartesianGrid horizontal={false} stroke="rgba(255,255,255,0.05)" />
        <XAxis type="number" stroke="#6b7280" tick={{ fill: '#6b7280', fontSize: 11 }} axisLine={false} tickLine={false} />
        <YAxis type="category" dataKey="name" width={150} stroke="transparent" tick={{ fill: '#9ca3af', fontSize: 11 }} axisLine={false} tickLine={false} />
        <Tooltip contentStyle={tooltipStyle} />
        <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={16}>
          {data.map((_, i) => (
            <Cell key={i} fill={accent} fillOpacity={0.7 + (i / Math.max(1, data.length)) * 0.3} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export function SegmentedBar({ segments }: { segments: { name: string; value: number; color: string }[] }) {
  const total = segments.reduce((s, x) => s + x.value, 0) || 1;
  return (
    <div>
      <div className="flex h-3 rounded-full overflow-hidden bg-white/5">
        {segments.map((s, i) => (
          <div key={i} className={cn('h-full transition-all duration-700')} style={{ width: `${(s.value / total) * 100}%`, backgroundColor: s.color }} title={`${s.name}: ${s.value}`} />
        ))}
      </div>
      <div className="flex flex-wrap gap-3 mt-2">
        {segments.map((s, i) => (
          <span key={i} className="flex items-center gap-1.5 text-xs text-gray-500">
            <span className="w-2 h-2 rounded-full" style={{ backgroundColor: s.color }} />
            {s.name} <span className="font-mono text-gray-300">{s.value}</span>
          </span>
        ))}
      </div>
    </div>
  );
}