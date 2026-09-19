import { useEffect, useRef, useState } from 'react';

export function Tooltip({ label, children, position = 'top' }: { label: string; children: React.ReactNode; position?: 'top' | 'bottom' }) {
  const [visible, setVisible] = useState(false);
  const [coords, setCoords] = useState({ x: 0, y: 0 });
  const ref = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    if (!visible || !ref.current) return;
    const rect = ref.current.getBoundingClientRect();
    setCoords({
      x: rect.left + rect.width / 2,
      y: position === 'top' ? rect.top - 8 : rect.bottom + 8,
    });
  }, [visible, position]);

  return (
    <span
      ref={ref}
      className="relative inline-flex"
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
      onFocus={() => setVisible(true)}
      onBlur={() => setVisible(false)}
    >
      {children}
      {visible && (
        <span
          role="tooltip"
          className="fixed z-[200] px-2.5 py-1 text-xs font-medium text-surface-50 bg-gray-100 rounded-md shadow-lg whitespace-nowrap pointer-events-none"
          style={{
            left: coords.x,
            top: coords.y,
            transform: 'translate(-50%, -100%)',
          }}
        >
          {label}
        </span>
      )}
    </span>
  );
}