import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router';
import { Database } from 'lucide-react';
import { fetchConnectors } from '../../lib/api';

interface Source {
  id: string;
  name: string;
  type: string;
  status: string;
}

export function DataSourcesMiniWidget() {
  const navigate = useNavigate();
  const [sources, setSources] = useState<Source[]>([]);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const res = await fetchConnectors();
      setSources(res.sources || []);
      setError(null);
    } catch {
      setError('Failed to load sources');
    }
  }, []);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 30000);
    return () => clearInterval(interval);
  }, [refresh]);

  const activeCount = sources.filter((s) => s.status === 'active' || s.status === 'ok' || s.status === 'connected').length;

  return (
    <div
      className="hud-panel p-4 cursor-pointer transition-colors"
      onClick={() => navigate('/data-sources')}
      style={{ border: '1px solid var(--color-border)' }}
      onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'var(--color-accent)')}
      onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'var(--color-border)')}
    >
      <div className="flex items-center justify-between mb-3">
        <h3 className="hud-label flex items-center gap-2">
          <Database size={12} style={{ color: 'var(--color-accent-purple)' }} />
          Data Sources
        </h3>
        <span className="text-xs font-medium" style={{ color: 'var(--color-text-tertiary)' }}>
          {sources.length} total
        </span>
      </div>

      {error ? (
        <div className="text-xs" style={{ color: 'var(--color-error)' }}>{error}</div>
      ) : sources.length === 0 ? (
        <div className="text-xs" style={{ color: 'var(--color-text-tertiary)' }}>No connectors configured</div>
      ) : (
        <>
          <div className="flex flex-wrap gap-2 mb-3">
            {sources.slice(0, 6).map((s) => {
              const isActive = s.status === 'active' || s.status === 'ok' || s.status === 'connected';
              return (
                <span
                  key={s.id}
                  className="px-2 py-0.5 rounded-full text-[11px] font-medium flex items-center gap-1.5"
                  style={{
                    background: isActive ? 'var(--color-accent-subtle)' : 'var(--color-bg-secondary)',
                    color: isActive ? 'var(--color-accent)' : 'var(--color-text-tertiary)',
                  }}
                >
                  <span
                    className="w-1.5 h-1.5 rounded-full"
                    style={{
                      background: isActive ? 'var(--color-success)' : 'var(--color-text-tertiary)',
                    }}
                  />
                  {s.name}
                </span>
              );
            })}
          </div>
          <div className="text-[11px]" style={{ color: 'var(--color-text-secondary)' }}>
            {activeCount} of {sources.length} active
          </div>
        </>
      )}
    </div>
  );
}
