import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { LandhausStatusPanel } from '../LandhausStatusPanel';

const mockFetch = vi.hoisted(() => vi.fn());

global.fetch = mockFetch;

const defaultHealth = {
  status: 'ok',
  sources: {
    website: { status: 'up', status_code: 200 },
    deskline: { status: 'demo', rooms_total: 12, rooms_occupied: 8, rooms_available: 4 },
    ical: { status: 'demo', bookings_count: 23, last_sync: '2026-06-14T10:00:00Z' },
    vercel: { status: 'demo', deployment_state: 'READY', production_url: 'https://www.landhausbavaria.de' },
  },
};

const defaultWebsite = {
  status: 'ok',
  website: {
    url: 'https://www.landhausbavaria.de',
    data: {
      title: 'Landhaus Bavaria',
      description: 'Bayerische Gastlichkeit',
      address: 'Frankfurter Str. 85',
      opening_hours: { Mo: '11:30-14:00' },
      weekday_specials: ['Bavaria Burgertag'],
      navigation: [{ label: 'Pension', url: 'https://www.landhausbavaria.de/pension' }],
    },
  },
};

function mockResponses(health: Record<string, unknown> = defaultHealth, website: Record<string, unknown> = defaultWebsite) {
  mockFetch.mockResolvedValueOnce({ ok: true, json: async () => health });
  mockFetch.mockResolvedValueOnce({ ok: true, json: async () => website });
}

describe('LandhausStatusPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially', () => {
    mockFetch.mockImplementation(() => new Promise(() => {}));
    render(<LandhausStatusPanel />);
    expect(screen.getByText(/Loading Landhaus Bavaria status/)).toBeInTheDocument();
  });

  it('renders all source statuses when data loads', async () => {
    mockResponses();
    render(<LandhausStatusPanel />);

    await waitFor(() => {
      expect(screen.getByText('Website')).toBeInTheDocument();
      expect(screen.getByText('Deskline')).toBeInTheDocument();
      expect(screen.getByText('iCal Sync')).toBeInTheDocument();
      expect(screen.getByText('Vercel')).toBeInTheDocument();
    });

    expect(screen.getByText('Room Occupancy')).toBeInTheDocument();
    expect(screen.getByText('Website Content')).toBeInTheDocument();
  });

  it('shows error state when fetch fails', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Network error'));

    render(<LandhausStatusPanel />);

    await waitFor(() => {
      expect(screen.getByText(/Network error/)).toBeInTheDocument();
    });
  });

  it('shows error state on non-ok HTTP response', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 503,
    });

    render(<LandhausStatusPanel />);

    await waitFor(() => {
      expect(screen.getByText(/Failed: 503/)).toBeInTheDocument();
    });
  });

  it('renders demo status correctly', async () => {
    mockResponses();
    render(<LandhausStatusPanel />);

    await waitFor(() => {
      expect(screen.getByText('Website')).toBeInTheDocument();
    });

    const demoItems = screen.getAllByText('demo');
    expect(demoItems.length).toBe(3);
    expect(screen.getByText(/4 available/i)).toBeInTheDocument();
    expect(screen.getByText(/Bookings: 23/)).toBeInTheDocument();
    expect(screen.getByText(/Deploy: READY/)).toBeInTheDocument();
  });

  it('renders down status with error message', async () => {
    mockResponses({
      status: 'ok',
      sources: {
        website: { status: 'down', error: 'Connection timeout' },
        deskline: { status: 'demo', rooms_total: 12, rooms_occupied: 8, rooms_available: 4 },
        ical: { status: 'demo', bookings_count: 23 },
        vercel: { status: 'demo', deployment_state: 'READY' },
      },
    });

    render(<LandhausStatusPanel />);

    await waitFor(() => {
      expect(screen.getByText('Connection timeout')).toBeInTheDocument();
    });
  });

  it('refreshes data when refresh button is clicked', async () => {
    mockResponses();

    render(<LandhausStatusPanel />);

    await waitFor(() => {
      expect(screen.getByText('Refresh')).toBeInTheDocument();
    });

    mockResponses();

    const refreshBtn = screen.getByText('Refresh');
    fireEvent.click(refreshBtn);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledTimes(4);
    });
  });
});
