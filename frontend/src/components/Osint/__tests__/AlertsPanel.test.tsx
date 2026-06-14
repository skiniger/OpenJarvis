import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { AlertsPanel } from '../AlertsPanel';

const mockFetchAlerts = vi.hoisted(() => vi.fn());

vi.mock('../../Desktop/lib/api', () => ({
  fetchAlerts: mockFetchAlerts,
}));

describe('AlertsPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders empty state', async () => {
    mockFetchAlerts.mockResolvedValue({ alerts: [], count: 0, unread: 0 });
    render(<AlertsPanel />);

    await waitFor(() => {
      expect(screen.getByText(/No change alerts yet/)).toBeInTheDocument();
    });
  });

  it('shows alert list with targets', async () => {
    mockFetchAlerts.mockResolvedValue({
      alerts: [
        {
          id: 'a1',
          target: 'example.com',
          type: 'scan',
          timestamp: new Date().toISOString(),
          metadata: {
            diff: {
              changed: { status: { from: 200, to: 404 } },
            },
          },
        },
      ],
      count: 1,
      unread: 1,
    });
    render(<AlertsPanel />);

    await waitFor(() => {
      expect(screen.getByText('example.com')).toBeInTheDocument();
    });
    expect(screen.getByText('scan')).toBeInTheDocument();
  });

  it('expands alert to show diff details', async () => {
    mockFetchAlerts.mockResolvedValue({
      alerts: [
        {
          id: 'a1',
          target: 'example.com',
          type: 'scan',
          timestamp: new Date().toISOString(),
          metadata: {
            diff: {
              changed: { status: { from: 200, to: 404 } },
              added: { new_key: 'value' },
              removed: { old_key: 'gone' },
            },
          },
        },
      ],
      count: 1,
      unread: 1,
    });
    render(<AlertsPanel />);

    await waitFor(() => {
      expect(screen.getByText('example.com')).toBeInTheDocument();
    });

    const expandBtn = screen.getByTitle('Expand');
    fireEvent.click(expandBtn);

    expect(screen.getByText('Changed')).toBeInTheDocument();
    expect(screen.getByText('Added')).toBeInTheDocument();
    expect(screen.getByText('Removed')).toBeInTheDocument();
  });

  it('shows error on fetch failure', async () => {
    mockFetchAlerts.mockRejectedValue(new Error('Network error'));
    render(<AlertsPanel />);

    await waitFor(() => {
      expect(screen.getByText(/Network error/)).toBeInTheDocument();
    });
  });
});
