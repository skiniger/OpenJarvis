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
import { WidgetCard, MiniStat, TrendSparkline, WIDGET_ACCENT, WidgetError, WidgetSkeleton } from './shared';

const ACCENT = WIDGET_ACCENT.energy;

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
  const [powerHistory, setPowerHistory] = useState<number[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      setLoading((prev) => prev && !energy);
      const [energyRes, telRes] = await Promise.allSettled([
        fetchEnergy().catch(() => null),
        fetchTelemetry().catch(() => null),
      ]);

      if (energyRes.status === 'fulfilled' && energyRes.value) {
        const data = energyRes.value as EnergyData;
        setEnergy(data);
        if (data.samples) {
          const points = data.samples.slice(-20).map((s) => ({
            time: new Date(s.timestamp).toLocaleTimeString(),
            power: Math.round(s.power_w * 10) / 10,
          }));
          setChartData(points);
          setPowerHistory((prev) => [...prev.slice(-19), data.avg_power_w ?? 0]);
        }
        setError(null);
      }
      if (telRes.status === 'fulfilled' && telRes.value) {
        setTelemetry(telRes.value as TelemetryStats);
      }
    } catch {
      setError('Cannot connect');
    } finally {
      setLoading(false);
    }
  }, [energy]);

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

  const tokens = savings?.total_tokens ?? telemetry?.total_tokens ?? 0;
  const requests = savings?.total_calls ?? telemetry?.total_requests ?? 0;

  return (
    <WidgetCard title="Energy / Inference" icon={Zap} accent={ACCENT}>
      {loading ? (
        <WidgetSkeleton />
      ) : error || !energy ? (
        <WidgetError message={error || 'awaiting telemetry…'} onRetry={fetchData} />
      ) : (
        <>
          <div className="grid grid-cols-2 gap-2 mb-3">
            <MiniStat icon={Zap} label="Power" value={`${(energy.avg_power_w ?? 0).toFixed(1)} W`} color={ACCENT} />
            <MiniStat icon={Hash} label="Tokens" value={formatNumber(tokens)} color={ACCENT} />
            <MiniStat icon={Thermometer} label="Thermal" value={thermalStatus.label} color={thermalStatus.color} />
            <MiniStat icon={Activity} label="Requests" value={String(requests)} color={ACCENT} />
          </div>

          {chartData.length > 1 && (
            <div className="h-28 mb-2">
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
                  <Line type="monotone" dataKey="power" stroke={ACCENT} strokeWidth={1.5} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {powerHistory.length > 1 && (
            <div>
              <div className="flex items-center justify-between text-[10px] mb-1" style={{ color: 'var(--color-text-tertiary)' }}>
                <span>Power trend</span>
              </div>
              <TrendSparkline data={powerHistory} color={ACCENT} width={240} height={28} />
            </div>
          )}
        </>
      )}
    </WidgetCard>
  );
}

function formatNumber(n: number): string {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M';
  if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K';
  return String(n);
}
