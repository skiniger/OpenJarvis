import { useState, useEffect, useCallback } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { Zap, Activity, Thermometer, Hash } from 'lucide-react';
import { fetchEnergy, fetchTelemetry } from '../../lib/api';
import { useAppStore } from '../../lib/store';

interface EnergySample {
  timestamp: string;
  power_w: number;
  energy_j: number;
}

interface EnergyData {
  total_energy_j?: number;
  energy_per_token_j?: number;
  avg_power_w?: number;
  samples?: EnergySample[];
}

interface TelemetryStats {
  total_requests?: number;
  total_tokens?: number;
}

interface ChartPoint {
  time: string;
  power: number;
}

export function EnergyOverviewWidget() {
  const savings = useAppStore((s) => s.savings);
  const [energy, setEnergy] = useState<EnergyData | null>(null);
  const [telemetry, setTelemetry] = useState<TelemetryStats | null>(null);
  const [chartData, setChartData] = useState<ChartPoint[]>([]);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const [energyRes, telRes] = await Promise.allSettled([
        fetchEnergy().catch(() => null),
        fetchTelemetry().catch(() => null),
      ]);

      if (energyRes.status === 'fulfilled' && energyRes.value) {
        const data = energyRes.value as EnergyData;
        setEnergy(data);
        if (data.samples) {
          setChartData(
            data.samples.slice(-20).map((s) => ({
              time: new Date(s.timestamp).toLocaleTimeString(),
              power: Math.round(s.power_w * 10) / 10,
            })),
          );
        }
        setError(null);
      }
      if (telRes.status === 'fulfilled' && telRes.value) {
        setTelemetry(telRes.value as TelemetryStats);
      }
    } catch {
      setError('Cannot connect');
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const thermalStatus = (energy?.avg_power_w ?? 0) < 50
    ? { label: 'Cool', color: 'var(--color-success)' }
    : (energy?.avg_power_w ?? 0) < 150
      ? { label: 'Warm', color: 'var(--color-warning)' }
      : { label: 'Hot', color: 'var(--color-error)' };

  return (
    <div className="hud-panel p-4" style={{ border: '1px solid var(--color-border)' }}>
      <div className="flex items-center justify-between mb-3">
        <h3 className="hud-label flex items-center gap-2">
          <Zap size={12} style={{ color: 'var(--color-accent)' }} />
          Energy / Inference
        </h3>
      </div>

      {error || !energy ? (
        <div className="text-xs" style={{ color: 'var(--color-text-tertiary)' }}>
          {error || 'awaiting telemetry…'}
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-2 mb-3">
            <MiniCard
              icon={Zap}
              label="Power"
              value={`${(energy.avg_power_w ?? 0).toFixed(1)} W`}
            />
            <MiniCard
              icon={Hash}
              label="Tokens"
              value={formatNumber(savings?.total_tokens ?? telemetry?.total_tokens ?? 0)}
            />
            <MiniCard
              icon={Thermometer}
              label="Thermal"
              value={thermalStatus.label}
              color={thermalStatus.color}
            />
            <MiniCard
              icon={Activity}
              label="Requests"
              value={String(savings?.total_calls ?? telemetry?.total_requests ?? 0)}
            />
          </div>

          {chartData.length > 1 && (
            <div className="h-28">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                  <XAxis dataKey="time" tick={{ fontSize: 9, fill: 'var(--color-text-tertiary)' }} />
                  <YAxis tick={{ fontSize: 9, fill: 'var(--color-text-tertiary)' }} unit="W" />
                  <Tooltip
                    contentStyle={{
                      background: 'var(--color-surface)',
                      border: '1px solid var(--color-border)',
                      borderRadius: 'var(--radius-md)',
                      fontSize: 11,
                      color: 'var(--color-text)',
                    }}
                  />
                  <Line type="monotone" dataKey="power" stroke="var(--color-accent)" strokeWidth={1.5} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function MiniCard({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: typeof Zap;
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

function formatNumber(n: number): string {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M';
  if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K';
  return String(n);
}
