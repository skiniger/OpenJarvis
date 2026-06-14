import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router';
import { Hotel, Wifi, Calendar, Globe } from 'lucide-react';
import { fetchLandhausHealth } from '../../lib/api';

interface SourceHealth {
  status: string;
  latency_ms: number;
  rooms_total?: number;
  rooms_occupied?: number;
  rooms_available?: number;
  next_checkin?: string;
  bookings_count?: number;
  last_sync?: string;
  channels?: string[];
  deployment_state?: string;
  production_url?: string;
  last_deploy?: string;
  isDemo?: boolean;
  message?: string;
}

interface HealthResponse {
  status: string;
  sources: Record<string, SourceHealth>;
}

export function LandhausBavariaWidget() {
  const navigate = useNavigate();
  const [data, setData] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const res = await fetchLandhausHealth();
      setData(res as HealthResponse);
      setError(null);
    } catch {
      setError('Health check failed');
    }
  }, []);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 30000);
    return () => clearInterval(interval);
  }, [refresh]);

  const sources = data?.sources || {};
  const deskline = sources.deskline;
  const ical = sources.ical;
  const vercel = sources.vercel;

  const anyDown = Object.values(sources).some((s) => s.status !== 'ok');
  const borderColor = anyDown ? 'var(--color-error)' : 'var(--color-border)';

  return (
    <div
      className="hud-panel p-4 cursor-pointer transition-colors"
      onClick={() => navigate('/landhaus')}
      style={{ border: `1px solid ${borderColor}` }}
      onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'var(--color-accent)')}
      onMouseLeave={(e) => (e.currentTarget.style.borderColor = borderColor)}
    >
      <div className="flex items-center justify-between mb-3">
        <h3 className="hud-label flex items-center gap-2">
          <Hotel size={12} style={{ color: '#38bdf8' }} />
          Landhaus Bavaria
        </h3>
        {deskline?.isDemo && (
          <span
            className="px-1.5 py-0.5 rounded text-[10px] font-medium"
            style={{ background: '#38bdf820', color: '#38bdf8' }}
          >
            Demo
          </span>
        )}
      </div>

      {error ? (
        <div className="text-xs" style={{ color: 'var(--color-error)' }}>{error}</div>
      ) : (
        <>
          <div className="grid grid-cols-3 gap-2 mb-3">
            <StatusPill
              icon={Globe}
              label="Website"
              status={sources.website?.status || 'unknown'}
              latency={sources.website?.latency_ms}
            />
            <StatusPill
              icon={Wifi}
              label="Deskline"
              status={deskline?.status || 'unknown'}
              latency={deskline?.latency_ms}
            />
            <StatusPill
              icon={Calendar}
              label="iCal"
              status={ical?.status || 'unknown'}
              latency={ical?.latency_ms}
            />
          </div>

          {deskline && (
            <div className="grid grid-cols-3 gap-2 text-center">
              <MiniStat label="Total" value={deskline.rooms_total ?? '—'} />
              <MiniStat label="Occupied" value={deskline.rooms_occupied ?? '—'} />
              <MiniStat label="Available" value={deskline.rooms_available ?? '—'} />
            </div>
          )}

          {vercel && (
            <div className="mt-2 text-[10px] text-center" style={{ color: 'var(--color-text-tertiary)' }}>
              Vercel: {vercel.deployment_state || 'unknown'}
              {vercel.last_deploy && ` · ${new Date(vercel.last_deploy).toLocaleDateString()}`}
            </div>
          )}
        </>
      )}
    </div>
  );
}

function StatusPill({
  icon: Icon,
  label,
  status,
  latency,
}: {
  icon: typeof Wifi;
  label: string;
  status: string;
  latency?: number;
}) {
  const color =
    status === 'ok'
      ? 'var(--color-success)'
      : status === 'warning'
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
      {latency !== undefined && (
        <span className="text-[9px]" style={{ color: 'var(--color-text-tertiary)' }}>
          {latency}ms
        </span>
      )}
    </div>
  );
}

function MiniStat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="p-1.5 rounded" style={{ background: 'var(--color-bg-secondary)' }}>
      <div className="text-[10px]" style={{ color: 'var(--color-text-tertiary)' }}>
        {label}
      </div>
      <div className="text-sm font-semibold" style={{ color: 'var(--color-text)' }}>
        {value}
      </div>
    </div>
  );
}
