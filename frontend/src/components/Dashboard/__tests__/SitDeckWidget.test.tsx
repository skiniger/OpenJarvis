import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router';
import { SitDeckWidget } from '../SitDeckWidget';

const mocks = vi.hoisted(() => ({
  fetchSitDeckHealth: vi.fn(),
}));

vi.mock('../../../lib/api', () => ({
  fetchSitDeckHealth: mocks.fetchSitDeckHealth,
}));

function Wrapper({ children }: { children: React.ReactNode }) {
  return <BrowserRouter>{children}</BrowserRouter>;
}

describe('SitDeckWidget', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.fetchSitDeckHealth.mockResolvedValue({
      status: 'ok',
      sitdeck: {
        status: 'up',
        total_up: 7,
        total_endpoints: 7,
        sources: {
          widgets: { status: 'up', status_code: 200, size: 42 },
          data_sources: { status: 'up', status_code: 200, size: 128 },
          map_capabilities: { status: 'up', status_code: 200, size: 256 },
          plans: { status: 'up', status_code: 200, size: 64 },
          map_types: { status: 'up', status_code: 200, size: 32 },
          customer_count: { status: 'up', status_code: 200, size: 16 },
          content: { status: 'up', status_code: 200, size: 512 },
        },
      },
    });
  });

  it('renders endpoint statuses and totals', async () => {
    render(<SitDeckWidget />, { wrapper: Wrapper });
    await waitFor(() => expect(screen.getByText('SitDeck')).toBeInTheDocument());
    expect(screen.getByText('7/7')).toBeInTheDocument();
    expect(screen.getByText('Widgets')).toBeInTheDocument();
    expect(screen.getByText('Sources')).toBeInTheDocument();
    expect(screen.getByText('Maps')).toBeInTheDocument();
    expect(screen.getByText('Plans')).toBeInTheDocument();
    expect(screen.getByText('All SitDeck endpoints reachable')).toBeInTheDocument();
  });

  it('shows degraded state when endpoints are down', async () => {
    mocks.fetchSitDeckHealth.mockResolvedValue({
      status: 'ok',
      sitdeck: {
        status: 'degraded',
        total_up: 6,
        total_endpoints: 7,
        sources: {
          widgets: { status: 'up', status_code: 200, size: 42 },
          data_sources: { status: 'down', error: 'timeout' },
          map_capabilities: { status: 'up', status_code: 200, size: 256 },
          plans: { status: 'up', status_code: 200, size: 64 },
          map_types: { status: 'up', status_code: 200, size: 32 },
          customer_count: { status: 'up', status_code: 200, size: 16 },
          content: { status: 'up', status_code: 200, size: 512 },
        },
      },
    });

    render(<SitDeckWidget />, { wrapper: Wrapper });
    await waitFor(() => expect(screen.getByText('6/7')).toBeInTheDocument());
    expect(screen.getByText('1 endpoint(s) unreachable')).toBeInTheDocument();
  });

  it('shows error message when fetch fails', async () => {
    mocks.fetchSitDeckHealth.mockRejectedValue(new Error('network error'));
    render(<SitDeckWidget />, { wrapper: Wrapper });
    await waitFor(() => expect(screen.getByText('SitDeck health check failed')).toBeInTheDocument());
  });
});
