import { AgentFleetWidget } from '../components/Dashboard/AgentFleetWidget';
import { OsintWatchdogWidget } from '../components/Dashboard/OsintWatchdogWidget';
import { LandhausBavariaWidget } from '../components/Dashboard/LandhausBavariaWidget';
import { EnergyOverviewWidget } from '../components/Dashboard/EnergyOverviewWidget';
import { CompactTraceWidget } from '../components/Dashboard/CompactTraceWidget';

export function DashboardPage() {
  const now = new Date();
  const stamp = now.toISOString().replace('T', ' ').slice(0, 19) + ' UTC';

  return (
    <div className="flex-1 overflow-y-auto px-6 py-10">
      <div className="max-w-6xl mx-auto">
        <header className="mb-6">
          <div className="flex items-center justify-between">
            <h1 className="text-lg font-semibold" style={{ color: 'var(--color-text)' }}>
              System Command Center
            </h1>
            <div className="text-xs" style={{ color: 'var(--color-text-tertiary)' }}>
              {stamp}
            </div>
          </div>
          <p className="text-sm mt-2 max-w-2xl" style={{ color: 'var(--color-text-secondary)' }}>
            Live overview of all integrated subsystems — agents, OSINT, Landhaus Bavaria, and on-device inference.
          </p>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-4 mb-4">
          <AgentFleetWidget />
          <OsintWatchdogWidget />
          <LandhausBavariaWidget />
          <EnergyOverviewWidget />
        </div>

        <CompactTraceWidget />
      </div>
    </div>
  );
}
