import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router';
import { AgentFleetWidget } from '../AgentFleetWidget';
import { OsintWatchdogWidget } from '../OsintWatchdogWidget';
import { LandhausBavariaWidget } from '../LandhausBavariaWidget';
import { EnergyOverviewWidget } from '../EnergyOverviewWidget';
import { CompactTraceWidget } from '../CompactTraceWidget';

const mocks = vi.hoisted(() => ({
  fetchManagedAgents: vi.fn(),
  fetchAlerts: vi.fn(),
  fetchLandhausHealth: vi.fn(),
  fetchLandhausWebsiteData: vi.fn(),
  fetchEnergy: vi.fn(),
  fetchTelemetry: vi.fn(),
  fetchTraces: vi.fn(),
  fetchOsintStats: vi.fn(),
  fetchConnectors: vi.fn(),
}));

vi.mock('../../../lib/api', () => ({
  fetchManagedAgents: mocks.fetchManagedAgents,
  fetchLandhausHealth: mocks.fetchLandhausHealth,
  fetchLandhausWebsiteData: mocks.fetchLandhausWebsiteData,
  fetchEnergy: mocks.fetchEnergy,
  fetchTelemetry: mocks.fetchTelemetry,
  fetchTraces: mocks.fetchTraces,
  fetchOsintStats: mocks.fetchOsintStats,
  fetchConnectors: mocks.fetchConnectors,
}));

vi.mock('../../Desktop/lib/api', () => ({
  fetchAlerts: mocks.fetchAlerts,
}));

vi.mock('../../../lib/store', () => ({
  useAppStore: vi.fn((selector: any) =>
    selector({
      savings: { total_tokens: 1000, total_calls: 5, total_prompt_tokens: 400, total_completion_tokens: 600, local_cost: 0.001 },
    }),
  ),
}));

function Wrapper({ children }: { children: React.ReactNode }) {
  return <BrowserRouter>{children}</BrowserRouter>;
}

describe('AgentFleetWidget', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.fetchManagedAgents.mockResolvedValue([
      {
        id: 'a1',
        name: 'Test Agent',
        status: 'running',
        agent_type: 'test',
        config: {},
        summary_memory: '',
        created_at: 0,
        updated_at: 0,
        total_runs: 10,
        total_cost: 0.5,
        budget: 1.0,
      },
    ]);
  });

  it('renders agent count and status badges', async () => {
    render(<AgentFleetWidget />, { wrapper: Wrapper });
    await waitFor(() => expect(screen.getByText('1 total')).toBeInTheDocument());
    expect(screen.getByText('Running')).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByText('10')).toBeInTheDocument();
  });
});

describe('OsintWatchdogWidget', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.fetchAlerts.mockResolvedValue({
      alerts: [
        {
          id: 'al1',
          type: 'osint',
          user_id: 'u1',
          timestamp: new Date().toISOString(),
          target: 'example.com',
          tool_name: 'web_search',
          modules: null,
          results: null,
          output: null,
          success: true,
          metadata: {},
        },
      ],
      count: 1,
      unread: 0,
    });
    mocks.fetchOsintStats.mockResolvedValue({
      total_scans_today: 12,
      total_alerts_today: 1,
      watchdog_status: 'active',
      favorites_count: 3,
    });
  });

  it('renders alert count and tool name', async () => {
    render(<OsintWatchdogWidget />, { wrapper: Wrapper });
    await waitFor(() => expect(screen.getAllByText('1').length).toBeGreaterThanOrEqual(1));
    expect(screen.getByText('web_search')).toBeInTheDocument();
  });
});

describe('LandhausBavariaWidget', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.fetchLandhausHealth.mockResolvedValue({
      status: 'ok',
      sources: {
        deskline: { status: 'ok', latency_ms: 120, rooms_total: 12, rooms_occupied: 4, rooms_available: 8 },
        ical: { status: 'ok', latency_ms: 45 },
        website: { status: 'ok', latency_ms: 80 },
        vercel: { status: 'ok', latency_ms: 60, deployment_state: 'ready' },
      },
    });
    mocks.fetchLandhausWebsiteData.mockResolvedValue({
      status: 'ok',
      website: {
        url: 'https://www.landhausbavaria.de',
        data: { title: 'Landhaus Bavaria', opening_hours: { Mo: '11:30-14:00' }, weekday_specials: ['Burger Tuesday'] },
      },
    });
  });

  it('renders source statuses and room stats', async () => {
    render(<LandhausBavariaWidget />, { wrapper: Wrapper });
    await waitFor(() => expect(screen.getByText('Landhaus Bavaria')).toBeInTheDocument());
    expect(screen.getByText('12')).toBeInTheDocument();
    expect(screen.getByText('8')).toBeInTheDocument();
  });
});

describe('EnergyOverviewWidget', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.fetchEnergy.mockResolvedValue({
      total_energy_j: 5000,
      energy_per_token_j: 0.01,
      avg_power_w: 35,
      samples: [{ timestamp: new Date().toISOString(), power_w: 35, energy_j: 100 }],
    });
    mocks.fetchTelemetry.mockResolvedValue({ total_requests: 5, total_tokens: 1000 });
  });

  it('renders power and token stats', async () => {
    render(<EnergyOverviewWidget />, { wrapper: Wrapper });
    await waitFor(() => expect(screen.getByText('35.0 W')).toBeInTheDocument());
    expect(screen.getByText('1.0K')).toBeInTheDocument();
  });
});

describe('CompactTraceWidget', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.fetchTraces.mockResolvedValue({
      traces: [
        {
          id: 't1',
          query: 'hello',
          steps: [{ step_type: 'route', duration_ms: 12, data: {} }],
          created_at: new Date().toISOString(),
        },
      ],
    });
  });

  it('renders trace query', async () => {
    render(<CompactTraceWidget />, { wrapper: Wrapper });
    await waitFor(() => expect(screen.getByText('hello')).toBeInTheDocument());
  });
});
