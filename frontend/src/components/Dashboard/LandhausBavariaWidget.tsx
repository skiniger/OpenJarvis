import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router';
import { Hotel, Globe, Calendar, Server, Clock, Utensils } from 'lucide-react';
import { fetchLandhausHealth, fetchLandhausWebsiteData } from '../../lib/api';
import { WidgetCard, StatusPill, MiniStat, WIDGET_ACCENT, WidgetError, WidgetSkeleton } from './shared';

const ACCENT = WIDGET_ACCENT.landhaus;

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
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      setLoading((prev) => prev && !data && !website);
      const [healthRes, websiteRes] = await Promise.all([
        fetchLandhausHealth(),
        fetchLandhausWebsiteData(),
      ]);
      setData(healthRes as HealthResponse);
      setWebsite(websiteRes as WebsiteResponse);
      setError(null);
    } catch {
      setError('Health check failed');
    } finally {
      setLoading(false);
    }
  }, [data, website]);

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

  const badge = deskline?.isDemo ? (
    <span
      className="px-1.5 py-0.5 rounded text-[10px] font-medium"
      style={{ background: `${ACCENT}22`, color: ACCENT, border: `1px solid ${ACCENT}40` }}
    >
      Demo
    </span>
  ) : undefined;

  return (
    <WidgetCard
      title="Landhaus Bavaria"
      icon={Hotel}
      accent={ACCENT}
      badge={badge}
      borderColor={borderColor}
      onClick={() => navigate('/landhaus')}
    >
      {loading ? (
        <WidgetSkeleton />
      ) : error ? (
        <WidgetError message={error} onRetry={refresh} />
      ) : (
        <>
          <div className="grid grid-cols-4 gap-2 mb-3">
            <StatusPill icon={Globe} label="Web" status={sources.website?.status || 'unknown'} accent={ACCENT} />
            <StatusPill icon={Server} label="Desk" status={deskline?.status || 'unknown'} accent={ACCENT} />
            <StatusPill icon={Calendar} label="iCal" status={ical?.status || 'unknown'} accent={ACCENT} />
            <StatusPill icon={Globe} label="Vercel" status={vercel?.status || 'unknown'} accent={ACCENT} />
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
                    background: occupancyRate > 80 ? 'var(--color-error)' : occupancyRate > 50 ? ACCENT : 'var(--color-success)',
                  }}
                />
              </div>
              <div className="grid grid-cols-3 gap-2 mt-2">
                <MiniStat label="Total" value={deskline.rooms_total ?? '—'} />
                <MiniStat label="Occupied" value={deskline.rooms_occupied ?? '—'} />
                <MiniStat label="Available" value={deskline.rooms_available ?? '—'} />
              </div>
            </div>
          )}

          {(todayHours || nextSpecial) && (
            <div className="grid grid-cols-2 gap-2">
              {todayHours && (
                <div className="p-2 rounded text-[10px]" style={{ background: 'var(--color-bg-secondary)' }}>
                  <div className="flex items-center gap-1 mb-0.5" style={{ color: ACCENT }}>
                    <Clock size={10} />
                    <span>Heute</span>
                  </div>
                  <div style={{ color: 'var(--color-text)' }}>{todayHours}</div>
                </div>
              )}
              {nextSpecial && (
                <div className="p-2 rounded text-[10px]" style={{ background: 'var(--color-bg-secondary)' }}>
                  <div className="flex items-center gap-1 mb-0.5" style={{ color: ACCENT }}>
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
    </WidgetCard>
  );
}
