import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router';
import { Hotel, Globe, Calendar, Server, Clock, Utensils } from 'lucide-react';
import { fetchLandhausHealth, fetchLandhausWebsiteData } from '../../lib/api';

const GOLD = '#D4AF37';
const GOLD_LIGHT = '#C9A227';

interface SourceHealth {
  status: string;
  latency_ms?: number;
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

interface WebsiteData {
  title?: string;
  description?: string;
  address?: string;
  phone?: string;
  email?: string;
  opening_hours?: Record<string, string>;
  weekday_specials?: string[];
  navigation?: Array<{ label: string; url: string }>;
}

interface WebsiteResponse {
  status: string;
  website: {
    url: string;
    data: WebsiteData;
  };
}

export function LandhausBavariaWidget() {
  const navigate = useNavigate();
  const [data, setData] = useState<HealthResponse | null>(null);
  const [website, setWebsite] = useState<WebsiteResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [healthRes, websiteRes] = await Promise.all([
        fetchLandhausHealth(),
        fetchLandhausWebsiteData(),
      ]);
      setData(healthRes as HealthResponse);
      setWebsite(websiteRes as WebsiteResponse);
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
  const site = website?.website?.data;

  const anyDown = Object.values(sources).some((s) => s.status !== 'ok');
  const borderColor = anyDown ? 'var(--color-error)' : 'var(--color-border)';
  const occupancyRate = deskline && deskline.rooms_total
    ? Math.round(((deskline.rooms_occupied || 0) / deskline.rooms_total) * 100)
    : 0;

  const today = new Date().toLocaleDateString('de-DE', { weekday: 'short' });
  const todayHours = site?.opening_hours?.[today] || site?.opening_hours?.['Mo'];
  const nextSpecial = site?.weekday_specials?.[0];

  return (
    <div
      className="hud-panel p-0 cursor-pointer overflow-hidden transition-colors"
      onClick={() => navigate('/landhaus')}
      style={{ border: `1px solid ${borderColor}` }}
      onMouseEnter={(e) => (e.currentTarget.style.borderColor = GOLD)}
      onMouseLeave={(e) => (e.currentTarget.style.borderColor = borderColor)}
    >
      <div
        className="px-4 py-3 flex items-center justify-between"
        style={{
          background: `linear-gradient(135deg, ${GOLD}22 0%, ${GOLD_LIGHT}11 100%)`,
          borderBottom: `1px solid ${GOLD}33`,
        }}
      >
        <h3 className="hud-label flex items-center gap-2 font-semibold">
          <Hotel size={14} style={{ color: GOLD }} />
          <span style={{ color: GOLD }}>Landhaus Bavaria</span>
        </h3>
        {deskline?.isDemo && (
          <span
            className="px-1.5 py-0.5 rounded text-[10px] font-medium"
            style={{ background: `${GOLD}22`, color: GOLD, border: `1px solid ${GOLD}40` }}
          >
            Demo
          </span>
        )}
      </div>

      <div className="p-4">
        {error ? (
          <div className="text-xs" style={{ color: 'var(--color-error)' }}>{error}</div>
        ) : (
          <>
            <div className="grid grid-cols-4 gap-2 mb-3">
              <StatusPill icon={Globe} label="Web" status={sources.website?.status || 'unknown'} />
              <StatusPill icon={Server} label="Desk" status={deskline?.status || 'unknown'} />
              <StatusPill icon={Calendar} label="iCal" status={ical?.status || 'unknown'} />
              <StatusPill icon={Globe} label="Vercel" status={vercel?.status || 'unknown'} />
            </div>

            {deskline && (
              <div className="mb-3">
                <div className="flex items-center justify-between text-[10px] mb-1" style={{ color: 'var(--color-text-tertiary)' }}>
                  <span>Room occupancy</span>
                  <span>{occupancyRate}%</span>
                </div>
                <div
                  className="h-1.5 rounded-full overflow-hidden"
                  style={{ background: 'var(--color-bg-secondary)' }}
                >
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${occupancyRate}%`,
                      background: occupancyRate > 80
                        ? 'var(--color-error)'
                        : occupancyRate > 50
                          ? GOLD_LIGHT
                          : 'var(--color-success)',
                    }}
                  />
                </div>
                <div className="grid grid-cols-3 gap-2 mt-2 text-center">
                  <MiniStat label="Total" value={deskline.rooms_total ?? '—'} />
                  <MiniStat label="Occupied" value={deskline.rooms_occupied ?? '—'} />
                  <MiniStat label="Available" value={deskline.rooms_available ?? '—'} />
                </div>
              </div>
            )}

            {(todayHours || nextSpecial) && (
              <div className="grid grid-cols-2 gap-2">
                {todayHours && (
                  <div
                    className="p-2 rounded text-[10px]"
                    style={{ background: 'var(--color-bg-secondary)' }}
                  >
                    <div className="flex items-center gap-1 mb-0.5" style={{ color: GOLD }}>
                      <Clock size={10} />
                      <span>Heute</span>
                    </div>
                    <div style={{ color: 'var(--color-text)' }}>{todayHours}</div>
                  </div>
                )}
                {nextSpecial && (
                  <div
                    className="p-2 rounded text-[10px]"
                    style={{ background: 'var(--color-bg-secondary)' }}
                  >
                    <div className="flex items-center gap-1 mb-0.5" style={{ color: GOLD }}>
                      <Utensils size={10} />
                      <span>Special</span>
                    </div>
                    <div className="truncate" style={{ color: 'var(--color-text)' }}>{nextSpecial}</div>
                  </div>
                )}
              </div>
            )}

            {vercel && (
              <div className="mt-2 text-[9px] text-center" style={{ color: 'var(--color-text-tertiary)' }}>
                Vercel: {vercel.deployment_state || 'unknown'}
                {vercel.last_deploy && ` · ${new Date(vercel.last_deploy).toLocaleDateString()}`}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

function StatusPill({
  icon: Icon,
  label,
  status,
}: {
  icon: typeof Globe;
  label: string;
  status: string;
}) {
  const color =
    status === 'ok'
      ? 'var(--color-success)'
      : status === 'warning' || status === 'demo'
        ? GOLD
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
