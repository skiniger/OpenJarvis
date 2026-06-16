import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router';
import { Bot, AlertTriangle, Activity, DollarSign, Play, Pause } from 'lucide-react';
import { fetchManagedAgents, pauseManagedAgent, resumeManagedAgent, runManagedAgent } from '../../lib/api';
import type { ManagedAgent } from '../../lib/api';
import { WidgetCard, MiniStat, WIDGET_ACCENT, WidgetError, WidgetSkeleton } from './shared';

const ACCENT = WIDGET_ACCENT.agent;

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
  const [loading, setLoading] = useState(true);
  const [actingId, setActingId] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setLoading((prev) => prev && agents.length === 0);
      const data = await fetchManagedAgents();
      setAgents(data);
      setError(null);
    } catch {
      setError('Failed to load agents');
    } finally {
      setLoading(false);
    }
  }, [agents.length]);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 10000);
    return () => clearInterval(interval);
  }, [refresh]);

  const handleAction = async (agentId: string, action: 'run' | 'pause' | 'resume') => {
    setActingId(agentId);
    try {
      if (action === 'run') await runManagedAgent(agentId);
      else if (action === 'pause') await pauseManagedAgent(agentId);
      else if (action === 'resume') await resumeManagedAgent(agentId);
      await refresh();
    } catch {
      /* ignore — toast or error could be added later */
    } finally {
      setActingId(null);
    }
  };

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

  const topAgents = agents.slice(0, 3);

  const badge = agents.length > 0 ? (
    <span
      className="px-1.5 py-0.5 rounded text-[10px] font-medium"
      style={{ background: `${ACCENT}22`, color: ACCENT, border: `1px solid ${ACCENT}40` }}
    >
      {agents.length} total
    </span>
  ) : undefined;

  return (
    <WidgetCard
      title="Agent Fleet"
      icon={Bot}
      accent={ACCENT}
      badge={badge}
      borderColor={borderColor}
      onClick={() => navigate('/agents')}
    >
      {loading ? (
        <WidgetSkeleton />
      ) : error ? (
        <WidgetError message={error} onRetry={refresh} />
      ) : (
        <>
          <div className="grid grid-cols-3 gap-2 mb-3">
            <MiniStat
              icon={Activity}
              label="Running"
              value={String(counts.running)}
              color={counts.running > 0 ? 'var(--color-accent)' : 'var(--color-text-tertiary)'}
            />
            <MiniStat
              icon={AlertTriangle}
              label="Issues"
              value={String(counts.error + counts.needs_attention + counts.stalled)}
              color={counts.error + counts.needs_attention + counts.stalled > 0 ? 'var(--color-error)' : 'var(--color-success)'}
            />
            <MiniStat
              icon={DollarSign}
              label="Cost"
              value={`$${agents.reduce((sum, a) => sum + (a.total_cost ?? 0), 0).toFixed(4)}`}
              color={ACCENT}
            />
          </div>

          <div className="grid grid-cols-3 gap-2 mb-3">
            <MiniStat
              icon={Activity}
              label="Runs"
              value={String(agents.reduce((sum, a) => sum + (a.total_runs ?? 0), 0))}
              color={ACCENT}
            />
            <MiniStat
              icon={Pause}
              label="Paused"
              value={String(counts.paused)}
              color={counts.paused > 0 ? 'var(--color-warning)' : 'var(--color-text-tertiary)'}
            />
            <MiniStat
              icon={Bot}
              label="Idle"
              value={String(counts.idle)}
              color={counts.idle > 0 ? 'var(--color-success)' : 'var(--color-text-tertiary)'}
            />
          </div>

          {mostRecent && (
            <div className="text-[11px] mb-2" style={{ color: 'var(--color-text-secondary)' }}>
              Last: <span style={{ color: 'var(--color-text)' }}>{mostRecent.name}</span>{' '}
              {formatRelativeTime(mostRecent.last_run_at)}
            </div>
          )}

          {budgetWarnings.length > 0 && (
            <div
              className="flex items-center gap-1.5 text-[11px] mb-2"
              style={{ color: 'var(--color-warning)' }}
            >
              <AlertTriangle size={11} />
              {budgetWarnings.length} agent{budgetWarnings.length > 1 ? 's' : ''} near budget limit
            </div>
          )}

          {topAgents.length > 0 && (
            <div className="flex flex-col gap-1.5 pt-2" style={{ borderTop: '1px solid var(--color-border)' }}>
              {topAgents.map((a) => {
                const canRun = a.status === 'idle' || a.status === 'paused';
                const canPause = a.status === 'running';
                return (
                  <div key={a.id} className="flex items-center justify-between text-[11px]">
                    <span className="truncate" style={{ color: 'var(--color-text-secondary)' }}>
                      {a.name}
                    </span>
                    <div className="flex items-center gap-1 shrink-0">
                      {(canRun || canPause) && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleAction(a.id, canPause ? 'pause' : 'run');
                          }}
                          disabled={actingId === a.id}
                          className="p-1 rounded cursor-pointer transition-colors"
                          style={{
                            color: 'var(--color-text-tertiary)',
                            background: 'var(--color-bg-secondary)',
                            border: '1px solid var(--color-border-subtle)',
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.color = 'var(--color-accent)';
                            e.currentTarget.style.borderColor = 'var(--color-accent)';
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.color = 'var(--color-text-tertiary)';
                            e.currentTarget.style.borderColor = 'var(--color-border-subtle)';
                          }}
                        >
                          {canPause ? <Pause size={10} /> : <Play size={10} />}
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}
    </WidgetCard>
  );
}
