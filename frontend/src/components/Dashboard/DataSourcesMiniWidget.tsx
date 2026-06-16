import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router';
import { Database, CheckCircle2, XCircle } from 'lucide-react';
import { fetchConnectors } from '../../lib/api';
import { WidgetCard, MiniStat, WIDGET_ACCENT, WidgetError, WidgetSkeleton, useStatusColor } from './shared';

const ACCENT = WIDGET_ACCENT.datasource;

interface Source {
  id: string;
  name: string;
  type: string;
  status: string;
}

function isActiveStatus(status: string): boolean {
  return status === 'active' || status === 'ok' || status === 'connected';
}

export function DataSourcesMiniWidget() {
  const navigate = useNavigate();
  const [sources, setSources] = useState<Source[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      setLoading((prev) => prev && sources.length === 0);
      const res = await fetchConnectors();
      setSources(res.sources || []);
      setError(null);
    } catch {
      setError('Failed to load sources');
    } finally {
      setLoading(false);
    }
  }, [sources.length]);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 30000);
    return () => clearInterval(interval);
  }, [refresh]);

  const activeCount = sources.filter((s) => isActiveStatus(s.status)).length;
  const anyInactive = sources.some((s) => !isActiveStatus(s.status));

  const badge = sources.length > 0 ? (
    <span
      className="px-1.5 py-0.5 rounded text-[10px] font-medium"
      style={{ background: `${ACCENT}22`, color: ACCENT, border: `1px solid ${ACCENT}40` }}
    >
      {sources.length} total
    </span>
  ) : undefined;

  return (
    <WidgetCard
      title="Data Sources"
      icon={Database}
      accent={ACCENT}
      badge={badge}
      borderColor={anyInactive ? 'var(--color-warning)' : 'var(--color-border)'}
      onClick={() => navigate('/data-sources')}
    >
      {loading ? (
        <WidgetSkeleton />
      ) : error ? (
        <WidgetError message={error} onRetry={refresh} />
      ) : sources.length === 0 ? (
        <div className="text-xs" style={{ color: 'var(--color-text-tertiary)' }}>No connectors configured</div>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-2 mb-3">
            <MiniStat icon={CheckCircle2} label="Active" value={activeCount} color="var(--color-success)" />
            <MiniStat icon={XCircle} label="Inactive" value={sources.length - activeCount} color={anyInactive ? 'var(--color-warning)' : 'var(--color-text-tertiary)'} />
          </div>

          <div className="flex flex-wrap gap-2 mb-3">
            {sources.slice(0, 6).map((s) => {
              const active = isActiveStatus(s.status);
              const color = useStatusColor(s.status);
              return (
                <span
                  key={s.id}
                  className="px-2 py-0.5 rounded-full text-[11px] font-medium flex items-center gap-1.5"
                  style={{
                    background: active ? `${ACCENT}22` : 'var(--color-bg-secondary)',
                    color: active ? ACCENT : 'var(--color-text-tertiary)',
                  }}
                >
                  <span
                    className="w-1.5 h-1.5 rounded-full"
                    style={{ background: color }}
                  />
                  {s.name}
                </span>
              );
            })}
          </div>
          <div className="text-[11px]" style={{ color: 'var(--color-text-secondary)' }}>
            {activeCount} of {sources.length} active
          </div>
        </>
      )}
    </WidgetCard>
  );
}
