import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { SystemTelemetryWidget } from '../SystemTelemetryWidget';

const mocks = vi.hoisted(() => ({
  fetchMonitoringMetrics: vi.fn(),
}));

vi.mock('../../../lib/api', () => ({
  fetchMonitoringMetrics: mocks.fetchMonitoringMetrics,
}));

describe('SystemTelemetryWidget', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.fetchMonitoringMetrics.mockResolvedValue({
      timestamp: '2026-06-16T22:00:00Z',
      cpu: { percent: 14.3 },
      memory: { percent: 83.2 },
      disk: { percent: 67.2 },
    });
  });

  it('renders system metrics', async () => {
    render(<SystemTelemetryWidget />);
    await waitFor(() => expect(screen.getByText('System Telemetry')).toBeInTheDocument());
    expect(screen.getByText('14%')).toBeInTheDocument();
    expect(screen.getByText('83%')).toBeInTheDocument();
    expect(screen.getByText('67%')).toBeInTheDocument();
  });

  it('shows error state when fetch fails', async () => {
    mocks.fetchMonitoringMetrics.mockRejectedValue(new Error('fail'));
    render(<SystemTelemetryWidget />);
    await waitFor(() => expect(screen.getByText('Metrics unavailable')).toBeInTheDocument());
  });
});
