import type { ReactNode } from 'react';

interface WidgetCardProps {
  title: string;
  icon: React.ComponentType<{ size?: number; style?: React.CSSProperties }>;
  accent: string;
  badge?: ReactNode;
  children: ReactNode;
  onClick?: () => void;
  borderColor?: string;
}

export function WidgetCard({
  title,
  icon: Icon,
  accent,
  badge,
  children,
  onClick,
  borderColor = 'var(--color-border)',
}: WidgetCardProps) {
  return (
    <div
      className="hud-panel p-0 overflow-hidden transition-colors"
      onClick={onClick}
      style={{ border: `1px solid ${borderColor}`, cursor: onClick ? 'pointer' : 'default' }}
      onMouseEnter={(e) => {
        if (onClick) e.currentTarget.style.borderColor = accent;
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = borderColor;
      }}
    >
      <div
        className="px-4 py-3 flex items-center justify-between"
        style={{
          background: `linear-gradient(135deg, ${accent}22 0%, ${accent}11 100%)`,
          borderBottom: `1px solid ${accent}33`,
        }}
      >
        <h3 className="hud-label flex items-center gap-2 font-semibold">
          <Icon size={14} style={{ color: accent }} />
          <span style={{ color: accent }}>{title}</span>
        </h3>
        {badge}
      </div>
      <div className="p-4">{children}</div>
    </div>
  );
}
