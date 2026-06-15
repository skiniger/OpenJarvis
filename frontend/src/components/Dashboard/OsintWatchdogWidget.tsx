import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router';
import { Shield, Bell, Clock, BarChart3 } from 'lucide-react';
import { fetchAlerts } from '../Desktop/lib/api';
import { fetchOsintStats } from '../../lib/api';
import type { AlertsResponse } from '../Desktop/lib/api';

type AlertItem = AlertsResponse['alerts'][number];

const API_URL = (import.meta.env.VITE_API_URL as string) || 'http://127.0.0.1:8000';

function getSeverity(alert: AlertItem): string {
  if (!alert.success) return 'critical';
  const diff = alert.metadata?.diff;
  if (diff && (diff.changed || diff.added || diff.removed)) return 'warning';
  return 'info';
}

const SEVERITY_COLOR: Record<string, string> = {
  critical: 'var(--color-error)',
  warning: 'var(--color-warning)',
  info: 'var(--color-success)',
};

interface OsintStats {
  total_scans_today?: number;
  total_alerts_today?: number;
  watchdog_status?: string;
  favorites_count?: number;
}

export function OsintWatchdogWidget() {
  const navigate = useNavigate();
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [count, setCount] = useState(0);
  const [stats, setStats] = useState<OsintStats | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [alertsRes, statsRes] = await Promise.allSettled([
        fetchAlerts(API_URL, 5).catch(() => ({ alerts: [], count: 0 })),
        fetchOsintStats().catch(() => ({} as OsintStats)),
      ]);

      if (alertsRes.status === 'fulfilled') {
        setAlerts(alertsRes.value.alerts.slice(0, 5));
        setCount(alertsRes.value.count);
      }
      if (statsRes.status === 'fulfilled') {
        setStats(statsRes.value);
      }
      setError(null);
    } catch {
      setError('Failed to load alerts');
    }
  }, []);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 15000);
    return () => clearInterval(interval);
  }, [refresh]);

  const criticalCount = alerts.filter((a) => getSeverity(a) === 'critical').length;
  const warningCount = alerts.filter((a) => getSeverity(a) === 'warning').length;

  const borderColor =
    criticalCount > 0 ? 'var(--color-error)' : warningCount > 0 ? 'var(--color-warning)' : 'var(--color-border)';

  const handleClick = () => {
    window.dispatchEvent(new CustomEvent('osint-tab-change', { detail: 'alerts' }));
    navigate('/osint');
  };

  return (
    <div
      className="hud-panel p-4 cursor-pointer transition-colors"
      onClick={handleClick}
      style={{ border: `1px solid ${borderColor}` }}
      onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'var(--color-accent)')}
      onMouseLeave={(e) => (e.currentTarget.style.borderColor = borderColor)}
    >
      <div className="flex items-center justify-between mb-3">
        <h3 className="hud-label flex items-center gap-2">
          <Shield size={12} style={{ color: 'var(--color-accent-purple)' }} />
          OSINT Watchdog
        </h3>
        <div className="flex items-center gap-1.5">
          <Bell size={12} style={{ color: count > 0 ? 'var(--color-warning)' : 'var(--color-text-tertiary)' }} />
          <span
            className="text-xs font-medium"
            style={{ color: count > 0 ? 'var(--color-warning)' : 'var(--color-text-tertiary)' }}
          >
            {count}
          </span>
        </div>
      </div>

      {stats && (
        <div className="grid grid-cols-3 gap-2 mb-3">
          <MiniStat icon={BarChart3} label="Scans" value={String(stats.total_scans_today ?? 0)} />
          <MiniStat icon={Bell} label="Alerts" value={String(stats.total_alerts_today ?? 0)} />
          <MiniStat
            icon={Shield}
            label="Watchdog"
            value={stats.watchdog_status || 'unknown'}
            color={stats.watchdog_status === 'active' ? 'var(--color-success)' : 'var(--color-text-tertiary)'}
          />
        </div>
      )}

      {error ? (
        <div className="text-xs" style={{ color: 'var(--color-error)' }}>{error}</div>
      ) : alerts.length === 0 ? (
        <div className="text-xs" style={{ color: 'var(--color-text-tertiary)' }}>No active alerts</div>
      ) : (
        <div className="flex flex-col gap-1.5">
          {alerts.map((alert) => {
            const severity = getSeverity(alert);
            return (
              <div
                key={alert.id}
                className="flex items-start gap-2 p-1.5 rounded"
                style={{ background: 'var(--color-bg-secondary)' }}
              >
                <span
                  className="w-1.5 h-1.5 rounded-full mt-1 shrink-0"
                  style={{ background: SEVERITY_COLOR[severity] || 'var(--color-text-tertiary)' }}
                />
                <div className="min-w-0">
                  <div className="text-[11px] truncate" style={{ color: 'var(--color-text)' }}>
                    {alert.tool_name || alert.target || 'Untitled alert'}
                  </div>
                  <div className="text-[10px] flex items-center gap-1" style={{ color: 'var(--color-text-tertiary)' }}>
                    <Clock size={9} />
                    {new Date(alert.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              </div>
            );
          })}
          {count > alerts.length && (
            <div className="text-[10px] text-center" style={{ color: 'var(--color-text-tertiary)' }}>
              +{count - alerts.length} more
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function MiniStat({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: typeof Shield;
  label: string;
  value: string;
  color?: string;
}) {
  return (
    <div
      className="flex flex-col items-center gap-1 p-1.5 rounded"
      style={{ background: 'var(--color-bg-secondary)' }}
    >
      <Icon size={12} style={{ color: color || 'var(--color-accent-purple)' }} />
      <span className="text-[10px] font-medium" style={{ color: 'var(--color-text-tertiary)' }}>{label}</span>
      <span className="text-xs font-semibold" style={{ color: color || 'var(--color-text)' }}>{value}</span>
    </div>
  );
}
