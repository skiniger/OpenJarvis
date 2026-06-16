export function WidgetSkeleton() {
  return (
    <div className="hud-panel p-4 animate-pulse">
      <div className="flex items-center justify-between mb-3">
        <div className="h-4 w-32 rounded" style={{ background: 'var(--color-bg-secondary)' }} />
        <div className="h-4 w-12 rounded" style={{ background: 'var(--color-bg-secondary)' }} />
      </div>
      <div className="grid grid-cols-2 gap-2 mb-3">
        <div className="h-12 rounded" style={{ background: 'var(--color-bg-secondary)' }} />
        <div className="h-12 rounded" style={{ background: 'var(--color-bg-secondary)' }} />
        <div className="h-12 rounded" style={{ background: 'var(--color-bg-secondary)' }} />
        <div className="h-12 rounded" style={{ background: 'var(--color-bg-secondary)' }} />
      </div>
      <div className="h-16 rounded" style={{ background: 'var(--color-bg-secondary)' }} />
    </div>
  );
}
