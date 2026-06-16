interface WidgetErrorProps {
  message?: string;
  onRetry?: () => void;
}

export function WidgetError({ message = 'Failed to load', onRetry }: WidgetErrorProps) {
  return (
    <div className="flex flex-col items-center gap-2 py-4">
      <span className="text-xs" style={{ color: 'var(--color-error)' }}>{message}</span>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="px-3 py-1 rounded text-[11px] transition-colors"
          style={{
            background: 'var(--color-bg-secondary)',
            color: 'var(--color-text-secondary)',
            border: '1px solid var(--color-border)',
          }}
        >
          Retry
        </button>
      )}
    </div>
  );
}
