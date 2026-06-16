import { useEffect, useState, useCallback } from 'react';
import { Cpu, Thermometer, HardDrive, Activity } from 'lucide-react';
import { fetchMonitoringMetrics } from '../../lib/api';
import { WidgetCard, MiniStat, TrendSparkline, WIDGET_ACCENT } from './shared';

const ACCENT = WIDGET_ACCENT.energy;
const HISTORY_LIMIT = 20;

interface MetricsSnapshot {
  timestamp: string;
  cpu: { percent: number };
  memory: { percent: number };
  disk: { percent: number };
}

export function SystemTelemetryWidget() {
  const [latest, setLatest] = useState<MetricsSnapshot | null>(null);
  const [history, setHistory] = useState<MetricsSnapshot[]>([]);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const res = await fetchMonitoringMetrics();
      const data = res as {
        timestamp?: string;
        cpu?: { percent?: number };
        memory?: { percent?: number };
        disk?: { percent?: number };
      };
      const snapshot: MetricsSnapshot = {
        timestamp: data.timestamp || new Date().toISOString(),
        cpu: { percent: data.cpu?.percent ?? 0 },
        memory: { percent: data.memory?.percent ?? 0 },
        disk: { percent: data.disk?.percent ?? 0 },
      };
      setLatest(snapshot);
      setHistory((prev) => [...prev.slice(-HISTORY_LIMIT + 1), snapshot]);
      setError(null);
    } catch {
      setError('Metrics unavailable');
    }
  }, []);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 5000);
    return () => clearInterval(interval);
  }, [refresh]);

  const cpuHistory = history.map((h) => h.cpu.percent);
  const memoryHistory = history.map((h) => h.memory.percent);

  const thermal = latest
    ? latest.cpu.percent < 50
      ? { label: 'Cool', color: 'var(--color-success)' }
      : latest.cpu.percent < 80
        ? { label: 'Warm', color: 'var(--color-warning)' }
        : { label: 'Hot', color: 'var(--color-error)' }
    : { label: '—', color: 'var(--color-text-tertiary)' };

  return (
    <WidgetCard title="System Telemetry" icon={Cpu} accent={ACCENT}>
      {error ? (
        <div className="text-xs" style={{ color: 'var(--color-error)' }}>{error}</div>
      ) : !latest ? (
        <div className="text-xs" style={{ color: 'var(--color-text-tertiary)' }}>awaiting telemetry…</div>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-2 mb-3">
            <MiniCard icon={Activity} label="CPU" value={`${latest.cpu.percent.toFixed(0)}%`} color={ACCENT} />
            <MiniCard icon={Thermometer} label="Thermal" value={thermal.label} color={thermal.color} />
            <MiniCard icon={HardDrive} label="Memory" value={`${latest.memory.percent.toFixed(0)}%`} color={ACCENT} />
            <MiniCard icon={HardDrive} label="Disk" value={`${latest.disk.percent.toFixed(0)}%`} color={ACCENT} />
          </div>

          {cpuHistory.length > 1 && (
            <div className="mb-2">
              <div className="flex items-center justify-between text-[10px] mb-1" style={{ color: 'var(--color-text-tertiary)' }}>
                <span>CPU trend</span>
                <span>{HISTORY_LIMIT}s window</span>
              </div>
              <TrendSparkline data={cpuHistory} color={ACCENT} width={240} height={28} />
            </div>
          )}

          {memoryHistory.length > 1 && (
            <div>
              <div className="flex items-center justify-between text-[10px] mb-1" style={{ color: 'var(--color-text-tertiary)' }}>
                <span>Memory trend</span>
              </div>
              <TrendSparkline data={memoryHistory} color={ACCENT} width={240} height={28} />
            </div>
          )}
        </>
      )}
    </WidgetCard>
  );
}

function MiniCard({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: typeof Cpu;
  label: string;
  value: string;
  color?: string;
}) {
  return (
    <div className="flex items-center gap-2 p-2 rounded" style={{ background: 'var(--color-bg-secondary)' }}>
      <Icon size={12} style={{ color: color || 'var(--color-accent)' }} />
      <div>
        <div className="text-[10px]" style={{ color: 'var(--color-text-tertiary)' }}>{label}</div>
        <div className="text-xs font-medium" style={{ color: color || 'var(--color-text)' }}>{value}</div>
      </div>
    </div>
  );
}
