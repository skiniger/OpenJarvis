import { AgentFleetWidget } from '../components/Dashboard/AgentFleetWidget';
import { OsintWatchdogWidget } from '../components/Dashboard/OsintWatchdogWidget';
import { LandhausBavariaWidget } from '../components/Dashboard/LandhausBavariaWidget';
import { SitDeckWidget } from '../components/Dashboard/SitDeckWidget';
import { EnergyOverviewWidget } from '../components/Dashboard/EnergyOverviewWidget';
import { SystemTelemetryWidget } from '../components/Dashboard/SystemTelemetryWidget';
import { CompactTraceWidget } from '../components/Dashboard/CompactTraceWidget';
import { GlobalStatusStrip } from '../components/Dashboard/GlobalStatusStrip';
import { DataSourcesMiniWidget } from '../components/Dashboard/DataSourcesMiniWidget';

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

        <GlobalStatusStrip />

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
          <AgentFleetWidget />
          <OsintWatchdogWidget />
          <DataSourcesMiniWidget />
          <LandhausBavariaWidget />
          <SitDeckWidget />
          <EnergyOverviewWidget />
          <SystemTelemetryWidget />
        </div>

        <CompactTraceWidget />
      </div>
    </div>
  );
}
