interface MiniStatProps {
  label: string;
  value: string | number;
  color?: string;
  icon?: React.ComponentType<{ size?: number; style?: React.CSSProperties }>;
}

export function MiniStat({ label, value, color, icon: Icon }: MiniStatProps) {
  return (
    <div className="flex flex-col items-center gap-1 p-2 rounded" style={{ background: 'var(--color-bg-secondary)' }}>
      {Icon && <Icon size={12} style={{ color: color || 'var(--color-accent)' }} />}
      <span className="text-[10px] font-medium" style={{ color: 'var(--color-text-tertiary)' }}>{label}</span>
      <span className="text-sm font-semibold" style={{ color: color || 'var(--color-text)' }}>{value}</span>
    </div>
  );
}
