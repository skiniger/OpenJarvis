import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router';
import { Map, Database, Layers, Boxes } from 'lucide-react';
import { fetchSitDeckHealth } from '../../lib/api';
import { WidgetCard, StatusPill, WIDGET_ACCENT, WidgetError, WidgetSkeleton } from './shared';

const ACCENT = WIDGET_ACCENT.sitdeck;

interface EndpointHealth {
  status: string;
  status_code?: number;
  size?: number;
  error?: string;
  demo?: boolean;
}

interface SitDeckHealth {
  status: string;
  total_up: number;
  total_endpoints: number;
  demo?: boolean;
  sources: Record<string, EndpointHealth>;
}

interface HealthResponse {
  status: string;
  sitdeck: SitDeckHealth;
}

export function SitDeckWidget() {
  const navigate = useNavigate();
  const [data, setData] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      setLoading((prev) => prev && !data);
      const res = await fetchSitDeckHealth();
      setData(res as HealthResponse);
      setError(null);
    } catch {
      setError('SitDeck health check failed');
    } finally {
      setLoading(false);
    }
  }, [data]);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 30000);
    return () => clearInterval(interval);
  }, [refresh]);

  const sitdeck = data?.sitdeck;
  const sources = sitdeck?.sources || {};
  const totalUp = sitdeck?.total_up ?? 0;
  const totalEndpoints = sitdeck?.total_endpoints ?? 0;
  const anyDown = Object.values(sources).some((s) => s.status !== 'up');
  const borderColor = anyDown ? 'var(--color-error)' : 'var(--color-border)';
  const isDemo = sitdeck?.demo || Object.values(sources).some((s) => s.demo);

  const badge = (
    <span
      className="px-1.5 py-0.5 rounded text-[10px] font-medium"
      style={{
        background: anyDown ? 'var(--color-error-bg)' : `${ACCENT}22`,
        color: anyDown ? 'var(--color-error)' : ACCENT,
        border: `1px solid ${anyDown ? 'var(--color-error)' : ACCENT}40`,
      }}
    >
      {isDemo ? `Demo ${totalUp}/${totalEndpoints}` : `${totalUp}/${totalEndpoints}`}
    </span>
  );

  return (
    <WidgetCard
      title="SitDeck"
      icon={Map}
      accent={ACCENT}
      badge={badge}
      borderColor={borderColor}
      onClick={() => navigate('/sitdeck')}
    >
      {loading ? (
        <WidgetSkeleton />
      ) : error ? (
        <WidgetError message={error} onRetry={refresh} />
      ) : (
        <>
          <div className="grid grid-cols-4 gap-2 mb-3">
            <StatusPill icon={Boxes} label="Widgets" status={sources.widgets?.status || 'unknown'} accent={ACCENT} />
            <StatusPill icon={Database} label="Sources" status={sources.data_sources?.status || 'unknown'} accent={ACCENT} />
            <StatusPill icon={Layers} label="Maps" status={sources.map_capabilities?.status || 'unknown'} accent={ACCENT} />
            <StatusPill icon={Map} label="Plans" status={sources.plans?.status || 'unknown'} accent={ACCENT} />
          </div>

          {sitdeck && (
            <div className="text-[10px] text-center" style={{ color: 'var(--color-text-tertiary)' }}>
              {totalUp === totalEndpoints
                ? 'All SitDeck endpoints reachable'
                : `${totalEndpoints - totalUp} endpoint(s) unreachable`}
              {isDemo && ' · demo mode'}
            </div>
          )}
        </>
      )}
    </WidgetCard>
  );
}
