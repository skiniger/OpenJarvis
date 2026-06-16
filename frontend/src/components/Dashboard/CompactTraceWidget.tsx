import { useState, useEffect, useCallback } from 'react';
import { GitBranch, Clock, ChevronRight, ChevronDown } from 'lucide-react';
import { fetchTraces } from '../../lib/api';
import { WidgetCard, WIDGET_ACCENT, WidgetError, WidgetSkeleton } from './shared';

const ACCENT = WIDGET_ACCENT.trace;

interface TraceStepData {
  model?: string;
  tokens?: number;
  tool?: string;
  input?: string;
  output?: string;
  [key: string]: unknown;
}

interface TraceStep {
  step_type: string;
  duration_ms: number;
  data: TraceStepData;
}

interface TraceSummary {
  id: string;
  query: string;
  steps: TraceStep[];
  created_at: string;
}

const STEP_COLORS: Record<string, string> = {
  route: 'var(--color-accent)',
  retrieve: 'var(--color-success)',
  generate: 'var(--color-warning)',
  tool_call: 'var(--color-accent-purple)',
  respond: 'var(--color-accent-purple)',
};

export function CompactTraceWidget() {
  const [traces, setTraces] = useState<TraceSummary[]>([]);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      setLoading((prev) => prev && traces.length === 0);
      const data = await fetchTraces(5);
      const list = (data as { traces?: TraceSummary[] }).traces || [];
      setTraces(list.slice(0, 5));
      setError(null);
    } catch {
      setError('Cannot load traces');
    } finally {
      setLoading(false);
    }
  }, [traces.length]);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 10000);
    return () => clearInterval(interval);
  }, [refresh]);

  return (
    <WidgetCard title="Recent Traces" icon={GitBranch} accent={ACCENT}>
      {loading ? (
        <WidgetSkeleton />
      ) : error ? (
        <WidgetError message={error} onRetry={refresh} />
      ) : traces.length === 0 ? (
        <div className="text-xs" style={{ color: 'var(--color-text-tertiary)' }}>No traces yet</div>
      ) : (
        <div className="flex flex-col gap-1.5">
          {traces.map((trace) => {
            const totalMs = trace.steps.reduce((sum, s) => sum + s.duration_ms, 0);
            const isExpanded = expandedId === trace.id;
            return (
              <div key={trace.id} className="rounded overflow-hidden" style={{ border: '1px solid var(--color-border)' }}>
                <button
                  onClick={() => setExpandedId(isExpanded ? null : trace.id)}
                  className="flex items-center gap-2 w-full px-3 py-2 text-left transition-colors cursor-pointer"
                  style={{ background: 'var(--color-bg-secondary)' }}
                  onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--color-bg-tertiary)')}
                  onMouseLeave={(e) => (e.currentTarget.style.background = 'var(--color-bg-secondary)')}
                >
                  {isExpanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                  <span className="text-xs truncate flex-1" style={{ color: 'var(--color-text)' }}>
                    {trace.query || 'Untitled'}
                  </span>
                  <span className="text-[10px] flex items-center gap-1" style={{ color: 'var(--color-text-tertiary)' }}>
                    <Clock size={9} />
                    {totalMs.toFixed(0)}ms
                  </span>
                </button>
                {isExpanded && (
                  <div className="px-3 py-2 flex flex-col gap-1" style={{ borderTop: '1px solid var(--color-border)' }}>
                    {trace.steps.map((step, i) => (
                      <div key={i} className="flex items-center gap-2 text-[11px]">
                        <span
                          className="w-1.5 h-1.5 rounded-full"
                          style={{ background: STEP_COLORS[step.step_type] || 'var(--color-text-tertiary)' }}
                        />
                        <span style={{ color: 'var(--color-text-secondary)' }}>{step.step_type}</span>
                        <span className="ml-auto" style={{ color: 'var(--color-text-tertiary)' }}>
                          {step.duration_ms.toFixed(0)}ms
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </WidgetCard>
  );
}
