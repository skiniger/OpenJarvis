export function useStatusColor(status: string, accent?: string): string {
  if (status === 'ok' || status === 'up' || status === 'connected' || status === 'active' || status === 'ready') {
    return 'var(--color-success)';
  }
  if (status === 'warning' || status === 'degraded' || status === 'demo' || status === 'paused') {
    return accent || 'var(--color-warning)';
  }
  if (status === 'error' || status === 'down' || status === 'critical' || status === 'disconnected') {
    return 'var(--color-error)';
  }
  return accent || 'var(--color-text-tertiary)';
}
