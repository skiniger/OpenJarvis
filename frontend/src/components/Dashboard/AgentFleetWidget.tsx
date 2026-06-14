import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router';
import { Bot, AlertTriangle, Pause, Play, Activity, DollarSign } from 'lucide-react';
import { fetchManagedAgents } from '../../lib/api';
import type { ManagedAgent } from '../../lib/api';

const STATUS_ORDER = ['error', 'needs_attention', 'stalled', 'running', 'paused', 'idle', 'archived', 'budget_exceeded'];

const STATUS_META: Record<string, { label: string; color: string }> = {
  error: { label: 'Error', color: 'var(--color-error)' },
  needs_attention: { label: 'Attention', color: 'var(--color-warning)' },
  stalled: { label: 'Stalled', color: 'var(--color-warning)' },
  running: { label: 'Running', color: 'var(--color-accent)' },
  paused: { label: 'Paused', color: 'var(--color-text-tertiary)' },
  idle: { label: 'Idle', color: 'var(--color-success)' },
  archived: { label: 'Archived', color: 'var(--color-text-tertiary)' },
  budget_exceeded: { label: 'Budget', color: 'var(--color-warning)' },
};

function formatRelativeTime(ts?: number | null): string {
  if (!ts) return 'Never';
  const diff = Date.now() - ts * 1000;
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'Just now';
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

export function AgentFleetWidget() {
  const navigate = useNavigate();
  const [agents, setAgents] = useState<ManagedAgent[]>([]);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const data = await fetchManagedAgents();
      setAgents(data);
      setError(null);
    } catch {
      setError('Failed to load agents');
    }
  }, []);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 10000);
    return () => clearInterval(interval);
  }, [refresh]);

  const counts = (() => {
    const map: Record<string, number> = {};
    for (const s of STATUS_ORDER) map[s] = 0;
    for (const a of agents) {
      map[a.status] = (map[a.status] || 0) + 1;
    }
    return map;
  })();

  const mostRecent = [...agents].sort((a, b) => (b.last_run_at ?? 0) - (a.last_run_at ?? 0))[0];
  const budgetWarnings = agents.filter(
    (a) => a.budget && a.budget > 0 && (a.total_cost ?? 0) / a.budget > 0.75,
  );

  const overallStatus =
    counts.error > 0 || counts.needs_attention > 0
      ? 'critical'
      : counts.stalled > 0 || counts.budget_exceeded > 0 || budgetWarnings.length > 0
        ? 'warning'
        : 'ok';

  const borderColor =
    overallStatus === 'critical'
      ? 'var(--color-error)'
      : overallStatus === 'warning'
        ? 'var(--color-warning)'
        : 'var(--color-border)';

  return (
    <div
      className="hud-panel p-4 cursor-pointer transition-colors"
      onClick={() => navigate('/agents')}
      style={{ border: `1px solid ${borderColor}` }}
      onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'var(--color-accent)')}
      onMouseLeave={(e) => (e.currentTarget.style.borderColor = borderColor)}
    >
      <div className="flex items-center justify-between mb-3">
        <h3 className="hud-label flex items-center gap-2">
          <Bot size={12} style={{ color: 'var(--color-accent)' }} />
          Agent Fleet
        </h3>
        <span className="text-xs font-medium" style={{ color: 'var(--color-text-tertiary)' }}>
          {agents.length} total
        </span>
      </div>

      {error ? (
        <div className="text-xs" style={{ color: 'var(--color-error)' }}>{error}</div>
      ) : (
        <>
          <div className="flex flex-wrap gap-2 mb-3">
            {STATUS_ORDER.filter((s) => counts[s] > 0).map((s) => {
              const meta = STATUS_META[s];
              return (
                <span
                  key={s}
                  className="px-2 py-0.5 rounded-full text-[11px] font-medium"
                  style={{ background: meta.color + '20', color: meta.color }}
                >
                  {meta.label}: {counts[s]}
                </span>
              );
            })}
          </div>

          {mostRecent && (
            <div className="text-[11px] mb-2" style={{ color: 'var(--color-text-secondary)' }}>
              Last activity: <span style={{ color: 'var(--color-text)' }}>{mostRecent.name}</span>{' '}
              {formatRelativeTime(mostRecent.last_run_at)}
            </div>
          )}

          {budgetWarnings.length > 0 && (
            <div
              className="flex items-center gap-1.5 text-[11px]"
              style={{ color: 'var(--color-warning)' }}
            >
              <AlertTriangle size={11} />
              {budgetWarnings.length} agent{budgetWarnings.length > 1 ? 's' : ''} near budget limit
            </div>
          )}

          <div className="mt-3 pt-2 flex gap-3 text-[11px]" style={{ borderTop: '1px solid var(--color-border)' }}>
            <span className="flex items-center gap-1" style={{ color: 'var(--color-text-tertiary)' }}>
              <Activity size={10} />
              {agents.reduce((sum, a) => sum + (a.total_runs ?? 0), 0)} runs
            </span>
            <span className="flex items-center gap-1" style={{ color: 'var(--color-text-tertiary)' }}>
              <DollarSign size={10} />
              ${agents.reduce((sum, a) => sum + (a.total_cost ?? 0), 0).toFixed(4)} total
            </span>
          </div>
        </>
      )}
    </div>
  );
}
