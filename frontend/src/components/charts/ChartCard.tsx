import { CardHeader } from './CardHeader';

export function ChartCard({ title, subtitle, right, children, className }: {
  title: string;
  subtitle?: string;
  right?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`card p-5 ${className || ''}`}>
      <CardHeader title={title} subtitle={subtitle} right={right} />
      <div className="mt-4">{children}</div>
    </div>
  );
}