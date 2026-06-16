import { useEffect, useState, useCallback } from 'react';
import {
  Activity,
  Globe,
  Calendar,
  Server,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Loader2,
  RefreshCw,
  Hotel,
  MapPin,
  Phone,
  Mail,
  Clock,
  Utensils,
  ExternalLink,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { fetchLandhausHealth, fetchLandhausWebsiteData } from '../../lib/api';

const API_URL = (import.meta.env.VITE_API_URL as string) || 'http://127.0.0.1:8000';

interface SourceHealth {
  status: string;
  status_code?: number;
  error?: string;
  content_length?: number;
  latest_state?: string;
  latest_url?: string;
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
  data?: WebsiteData;
}

interface WebsiteData {
  title?: string;
  description?: string;
  address?: string;
  phone?: string;
  email?: string;
  opening_hours?: Record<string, string>;
  weekday_specials?: string[];
  prices?: string[];
  images?: Array<{ src: string; alt: string }>;
  navigation?: Array<{ label: string; url: string }>;
  room_keywords?: string[];
  headings?: { h1?: string[]; h2?: string[]; h3?: string[] };
}

interface HealthResponse {
  status: string;
  sources: Record<string, SourceHealth>;
}

interface WebsiteResponse {
  status: string;
  website: {
    url: string;
    data: WebsiteData;
  };
}

function useLandhausData() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [website, setWebsite] = useState<WebsiteResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [healthRes, websiteRes] = await Promise.all([
        fetchLandhausHealth() as Promise<HealthResponse>,
        fetchLandhausWebsiteData() as Promise<WebsiteResponse>,
      ]);
      setHealth(healthRes);
      setWebsite(websiteRes);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch Landhaus data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return { health, website, loading, error, reload: load };
}

const GOLD = '#D4AF37';
const GOLD_LIGHT = '#C9A227';

export function LandhausStatusPanel() {
  const { health, website, loading, error, reload } = useLandhausData();
  const [showJson, setShowJson] = useState(false);

  if (loading && !health) {
    return (
      <div className="flex items-center justify-center py-20 gap-2 text-xs" style={{ color: 'var(--color-text-tertiary)' }}>
        <Loader2 size={14} className="animate-spin" />
        Loading Landhaus Bavaria status…
      </div>
    );
  }

  if (error) {
    return (
      <div
        className="px-4 py-3 rounded-lg text-sm flex items-center gap-2"
        style={{
          background: 'color-mix(in srgb, var(--color-error) 8%, transparent)',
          border: '1px solid color-mix(in srgb, var(--color-error) 15%, transparent)',
          color: 'var(--color-error)',
        }}
      >
        <AlertTriangle size={14} />
        {error}
        <button
          onClick={reload}
          className="ml-auto text-xs underline cursor-pointer"
          style={{ color: 'var(--color-accent)' }}
        >
          Retry
        </button>
      </div>
    );
  }

  if (!health) return null;

  const sources = health.sources || {};
  const site = website?.website?.data;
  const siteSource = sources.website;

  return (
    <div className="flex flex-col gap-6 max-w-6xl mx-auto pb-10">
      {/* Hero header */}
      <header
        className="rounded-2xl p-6 md:p-8 relative overflow-hidden"
        style={{
          background: 'linear-gradient(135deg, rgba(212,175,55,0.12) 0%, rgba(15,23,42,0.6) 100%)',
          border: `1px solid ${GOLD}30`,
        }}
      >
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Hotel size={20} style={{ color: GOLD }} />
              <h1 className="text-lg md:text-xl font-semibold" style={{ color: 'var(--color-text)' }}>
                {site?.title || 'Landhaus Bavaria'}
              </h1>
            </div>
            <p className="text-sm max-w-2xl" style={{ color: 'var(--color-text-secondary)' }}>
              {site?.description || 'Bayerische Gastlichkeit in Bad Nauheim — Restaurant, Pension & Veranstaltungen.'}
            </p>
            {site?.address && (
              <div className="flex items-center gap-1.5 mt-3 text-xs" style={{ color: 'var(--color-text-tertiary)' }}>
                <MapPin size={12} style={{ color: GOLD }} />
                {site.address}
              </div>
            )}
          </div>
          <button
            onClick={reload}
            disabled={loading}
            className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium cursor-pointer transition-colors shrink-0"
            style={{
              background: 'rgba(212,175,55,0.15)',
              border: `1px solid ${GOLD}40`,
              color: GOLD,
            }}
          >
            <RefreshCw size={12} className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>
        </div>
      </header>

      {/* System status */}
      <section>
        <h2 className="text-xs font-semibold uppercase tracking-wider mb-3 flex items-center gap-2" style={{ color: 'var(--color-text-tertiary)' }}>
          <Activity size={12} style={{ color: GOLD }} />
          System Status
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
          <StatusCard
            icon={Globe}
            label="Website"
            source={sources.website}
            accent="#38bdf8"
          />
          <StatusCard
            icon={Server}
            label="Deskline"
            source={sources.deskline}
            accent="#a78bfa"
          />
          <StatusCard
            icon={Calendar}
            label="iCal Sync"
            source={sources.ical}
            accent="#f472b6"
          />
          <StatusCard
            icon={Activity}
            label="Vercel"
            source={sources.vercel}
            accent="#fb923c"
          />
        </div>
      </section>

      {/* Occupancy visualization */}
      {sources.deskline && (
        <section>
          <h2 className="text-xs font-semibold uppercase tracking-wider mb-3 flex items-center gap-2" style={{ color: 'var(--color-text-tertiary)' }}>
            <Hotel size={12} style={{ color: GOLD }} />
            Room Occupancy
          </h2>
          <div
            className="rounded-xl p-4"
            style={{ background: 'var(--color-bg-secondary)', border: '1px solid var(--color-border)' }}
          >
            <OccupancyBar
              total={sources.deskline.rooms_total ?? 12}
              occupied={sources.deskline.rooms_occupied ?? 8}
              available={sources.deskline.rooms_available ?? 4}
            />
          </div>
        </section>
      )}

      {/* Website content */}
      {site && (
        <section>
          <h2 className="text-xs font-semibold uppercase tracking-wider mb-3 flex items-center gap-2" style={{ color: 'var(--color-text-tertiary)' }}>
            <Globe size={12} style={{ color: GOLD }} />
            Website Content
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <InfoCard
              icon={Clock}
              title="Opening Hours"
              accent={GOLD}
            >
              {site.opening_hours ? (
                <ul className="space-y-1">
                  {Object.entries(site.opening_hours).map(([day, hours]) => (
                    <li key={day} className="flex justify-between text-xs py-1" style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
                      <span style={{ color: 'var(--color-text-secondary)' }}>{day}</span>
                      <span style={{ color: 'var(--color-text)' }}>{hours}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <span className="text-xs" style={{ color: 'var(--color-text-tertiary)' }}>No opening hours found</span>
              )}
            </InfoCard>

            <InfoCard
              icon={Utensils}
              title="Weekly Specials"
              accent={GOLD}
            >
              {site.weekday_specials && site.weekday_specials.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {site.weekday_specials.map((special) => (
                    <span
                      key={special}
                      className="text-[10px] px-2 py-1 rounded-full font-medium"
                      style={{ background: `${GOLD}20`, color: GOLD, border: `1px solid ${GOLD}30` }}
                    >
                      {special}
                    </span>
                  ))}
                </div>
              ) : (
                <span className="text-xs" style={{ color: 'var(--color-text-tertiary)' }}>No specials found</span>
              )}
            </InfoCard>

            <InfoCard
              icon={MapPin}
              title="Contact & Address"
              accent={GOLD}
            >
              <div className="space-y-2 text-xs">
                {site.address && (
                  <div className="flex items-start gap-2" style={{ color: 'var(--color-text-secondary)' }}>
                    <MapPin size={12} style={{ color: GOLD, marginTop: 2 }} />
                    {site.address}
                  </div>
                )}
                {site.phone && (
                  <div className="flex items-center gap-2" style={{ color: 'var(--color-text-secondary)' }}>
                    <Phone size={12} style={{ color: GOLD }} />
                    {site.phone}
                  </div>
                )}
                {site.email && (
                  <div className="flex items-center gap-2" style={{ color: 'var(--color-text-secondary)' }}>
                    <Mail size={12} style={{ color: GOLD }} />
                    <a href={`mailto:${site.email}`} className="hover:underline" style={{ color: GOLD }}>{site.email}</a>
                  </div>
                )}
              </div>
            </InfoCard>

            <InfoCard
              icon={Globe}
              title="Quick Links"
              accent={GOLD}
            >
              <div className="flex flex-wrap gap-2">
                {site.navigation?.slice(0, 8).map((link) => (
                  <a
                    key={link.url}
                    href={link.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-[10px] px-2 py-1 rounded-md transition-colors"
                    style={{ background: 'var(--color-bg-primary)', color: 'var(--color-text-secondary)', border: '1px solid var(--color-border)' }}
                  >
                    {link.label}
                    <ExternalLink size={9} />
                  </a>
                )) || (
                  <span className="text-xs" style={{ color: 'var(--color-text-tertiary)' }}>No links found</span>
                )}
              </div>
            </InfoCard>
          </div>
        </section>
      )}

      {/* Debug JSON */}
      <section>
        <button
          onClick={() => setShowJson((v) => !v)}
          className="flex items-center gap-1 text-[10px] uppercase tracking-wider cursor-pointer mb-2"
          style={{ color: 'var(--color-text-tertiary)' }}
        >
          {showJson ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
          Raw API Response
        </button>
        {showJson && (
          <div
            className="rounded-lg p-4"
            style={{ background: 'var(--color-bg-secondary)', border: '1px solid var(--color-border)' }}
          >
            <pre
              className="text-[10px] overflow-auto rounded p-2"
              style={{
                background: 'var(--color-bg-primary)',
                color: 'var(--color-text-secondary)',
                maxHeight: '300px',
              }}
            >
              {JSON.stringify({ health, website }, null, 2)}
            </pre>
          </div>
        )}
      </section>
    </div>
  );
}

function StatusCard({
  icon: Icon,
  label,
  source,
  accent,
}: {
  icon: React.ElementType;
  label: string;
  source?: SourceHealth;
  accent: string;
}) {
  const status = source?.status || 'unknown';
  const isUp = status === 'up';
  const isDown = status === 'down';
  const isDemo = status === 'demo';

  const StatusIcon = isUp ? CheckCircle : isDown ? XCircle : AlertTriangle;
  const statusColor = isUp ? '#4ade80' : isDown ? 'var(--color-error)' : isDemo ? '#38bdf8' : '#facc15';

  return (
    <div
      className="rounded-xl p-4 flex flex-col gap-3"
      style={{ background: 'var(--color-bg-secondary)', border: '1px solid var(--color-border)' }}
    >
      <div className="flex items-center gap-3">
        <div
          className="w-10 h-10 rounded-lg flex items-center justify-center shrink-0"
          style={{ background: `color-mix(in srgb, ${accent} 12%, transparent)` }}
        >
          <Icon size={18} style={{ color: accent }} />
        </div>
        <div className="flex flex-col">
          <span className="text-xs font-medium" style={{ color: 'var(--color-text)' }}>
            {label}
          </span>
          <span className="text-[10px] flex items-center gap-1" style={{ color: statusColor }}>
            <StatusIcon size={10} />
            {status}
          </span>
        </div>
      </div>

      {source?.status_code && (
        <div className="text-[10px]" style={{ color: 'var(--color-text-tertiary)' }}>
          Status code: {source.status_code}
        </div>
      )}

      {source?.rooms_available != null && (
        <div className="grid grid-cols-3 gap-2 text-center">
          <MiniStat label="Total" value={source.rooms_total ?? '—'} />
          <MiniStat label="Occupied" value={source.rooms_occupied ?? '—'} />
          <MiniStat label="Free" value={source.rooms_available ?? '—'} />
        </div>
      )}

      {source?.bookings_count != null && (
        <div className="text-[10px]" style={{ color: 'var(--color-text-tertiary)' }}>
          Bookings: {source.bookings_count}
          {source.channels && ` · ${source.channels.join(', ')}`}
        </div>
      )}

      {source?.deployment_state && (
        <div className="text-[10px]" style={{ color: 'var(--color-text-tertiary)' }}>
          Deploy: {source.deployment_state}
        </div>
      )}

      {source?.production_url && (
        <a
          href={source.production_url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-[10px] truncate flex items-center gap-1 hover:underline"
          style={{ color: GOLD }}
        >
          {source.production_url}
          <ExternalLink size={9} />
        </a>
      )}

      {source?.error && (
        <div
          className="text-[10px] px-2 py-1 rounded"
          style={{
            background: 'color-mix(in srgb, var(--color-error) 8%, transparent)',
            color: 'var(--color-error)',
          }}
        >
          {source.error}
        </div>
      )}
    </div>
  );
}

function MiniStat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="p-1.5 rounded" style={{ background: 'var(--color-bg-primary)' }}>
      <div className="text-[9px]" style={{ color: 'var(--color-text-tertiary)' }}>
        {label}
      </div>
      <div className="text-sm font-semibold" style={{ color: 'var(--color-text)' }}>
        {value}
      </div>
    </div>
  );
}

function OccupancyBar({ total, occupied, available }: { total: number; occupied: number; available: number }) {
  const occupiedPct = total > 0 ? Math.round((occupied / total) * 100) : 0;
  const availablePct = total > 0 ? Math.round((available / total) * 100) : 0;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between text-xs" style={{ color: 'var(--color-text-secondary)' }}>
        <span>{occupied} occupied</span>
        <span>{available} available</span>
        <span>{total} total</span>
      </div>
      <div
        className="h-3 rounded-full overflow-hidden flex"
        style={{ background: 'var(--color-bg-primary)', border: '1px solid var(--color-border)' }}
      >
        <div
          className="h-full transition-all duration-500"
          style={{ width: `${occupiedPct}%`, background: 'var(--color-error)' }}
          title={`Occupied: ${occupied}`}
        />
        <div
          className="h-full transition-all duration-500"
          style={{ width: `${availablePct}%`, background: GOLD }}
          title={`Available: ${available}`}
        />
      </div>
      <div className="flex gap-4 text-[10px]" style={{ color: 'var(--color-text-tertiary)' }}>
        <div className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full" style={{ background: 'var(--color-error)' }} />
          Occupied {occupiedPct}%
        </div>
        <div className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full" style={{ background: GOLD }} />
          Available {availablePct}%
        </div>
      </div>
    </div>
  );
}

function InfoCard({
  icon: Icon,
  title,
  accent,
  children,
}: {
  icon: React.ElementType;
  title: string;
  accent: string;
  children: React.ReactNode;
}) {
  return (
    <div
      className="rounded-xl p-4"
      style={{ background: 'var(--color-bg-secondary)', border: '1px solid var(--color-border)' }}
    >
      <div className="flex items-center gap-2 mb-3">
        <Icon size={14} style={{ color: accent }} />
        <h3 className="text-xs font-medium" style={{ color: 'var(--color-text)' }}>
          {title}
        </h3>
      </div>
      {children}
    </div>
  );
}
