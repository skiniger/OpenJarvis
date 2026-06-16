interface MiniStatProps {
  label: string;
  value: string | number;
  color?: string;
}

export function MiniStat({ label, value, color }: MiniStatProps) {
  return (
    <div className="p-1.5 rounded text-center" style={{ background: 'var(--color-bg-secondary)' }}>
      <div className="text-[10px]" style={{ color: 'var(--color-text-tertiary)' }}>{label}</div>
      <div className="text-sm font-semibold" style={{ color: color || 'var(--color-text)' }}>{value}</div>
    </div>
  );
}
