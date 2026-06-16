import { useStatusColor } from './useStatusColor';

interface StatusPillProps {
  icon: React.ComponentType<{ size?: number; style?: React.CSSProperties }>;
  label: string;
  status: string;
  accent?: string;
}

export function StatusPill({ icon: Icon, label, status, accent }: StatusPillProps) {
  const color = useStatusColor(status, accent);

  return (
    <div
      className="flex flex-col items-center gap-1 p-2 rounded"
      style={{ background: 'var(--color-bg-secondary)' }}
    >
      <Icon size={14} style={{ color }} />
      <span className="text-[10px] font-medium" style={{ color }}>{label}</span>
    </div>
  );
}
