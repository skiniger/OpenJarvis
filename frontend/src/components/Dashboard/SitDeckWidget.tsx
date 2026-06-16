import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router';
import { Map, Database, Layers, Boxes } from 'lucide-react';
import { fetchSitDeckHealth } from '../../lib/api';

interface EndpointHealth {
  status: string;
  status_code?: number;
  size?: number;
  error?: string;
}

interface SitDeckHealth {
  status: string;
  total_up: number;
  total_endpoints: number;
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

  const refresh = useCallback(async () => {
    try {
      const res = await fetchSitDeckHealth();
      setData(res as HealthResponse);
      setError(null);
    } catch {
      setError('SitDeck health check failed');
    }
  }, []);

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

  return (
    <div
      className="hud-panel p-4 cursor-pointer transition-colors"
      onClick={() => navigate('/sitdeck')}
      style={{ border: `1px solid ${borderColor}` }}
      onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'var(--color-accent)')}
      onMouseLeave={(e) => (e.currentTarget.style.borderColor = borderColor)}
    >
      <div className="flex items-center justify-between mb-3">
        <h3 className="hud-label flex items-center gap-2">
          <Map size={12} style={{ color: '#a78bfa' }} />
          SitDeck
        </h3>
        {sitdeck && (
          <span
            className="px-1.5 py-0.5 rounded text-[10px] font-medium"
            style={{
              background: anyDown ? 'var(--color-error-bg)' : '#a78bfa20',
              color: anyDown ? 'var(--color-error)' : '#a78bfa',
            }}
          >
            {totalUp}/{totalEndpoints}
          </span>
        )}
      </div>

      {error ? (
        <div className="text-xs" style={{ color: 'var(--color-error)' }}>{error}</div>
      ) : (
        <>
          <div className="grid grid-cols-4 gap-2 mb-3">
            <EndpointPill
              icon={Boxes}
              label="Widgets"
              status={sources.widgets?.status || 'unknown'}
            />
            <EndpointPill
              icon={Database}
              label="Sources"
              status={sources.data_sources?.status || 'unknown'}
            />
            <EndpointPill
              icon={Layers}
              label="Maps"
              status={sources.map_capabilities?.status || 'unknown'}
            />
            <EndpointPill
              icon={Map}
              label="Plans"
              status={sources.plans?.status || 'unknown'}
            />
          </div>

          {sitdeck && (
            <div className="text-[10px] text-center" style={{ color: 'var(--color-text-tertiary)' }}>
              {totalUp === totalEndpoints
                ? 'All SitDeck endpoints reachable'
                : `${totalEndpoints - totalUp} endpoint(s) unreachable`}
            </div>
          )}
        </>
      )}
    </div>
  );
}

function EndpointPill({
  icon: Icon,
  label,
  status,
}: {
  icon: typeof Map;
  label: string;
  status: string;
}) {
  const color =
    status === 'up'
      ? 'var(--color-success)'
      : status === 'degraded'
        ? 'var(--color-warning)'
        : 'var(--color-error)';

  return (
    <div
      className="flex flex-col items-center gap-1 p-2 rounded"
      style={{ background: 'var(--color-bg-secondary)' }}
    >
      <Icon size={14} style={{ color }} />
      <span className="text-[10px] font-medium" style={{ color }}>
        {label}
      </span>
    </div>
  );
}
