import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { SchedulePanel } from '../SchedulePanel';

const mockFetchSchedules = vi.hoisted(() => vi.fn());
const mockCreateSchedule = vi.hoisted(() => vi.fn());
const mockDeleteSchedule = vi.hoisted(() => vi.fn());
const mockToggleSchedule = vi.hoisted(() => vi.fn());

vi.mock('../../Desktop/lib/api', () => ({
  fetchSchedules: mockFetchSchedules,
  createSchedule: mockCreateSchedule,
  deleteSchedule: mockDeleteSchedule,
  toggleSchedule: mockToggleSchedule,
}));

describe('SchedulePanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders empty state', async () => {
    mockFetchSchedules.mockResolvedValue({ schedules: [], count: 0 });
    render(<SchedulePanel />);

    await waitFor(() => {
      expect(screen.getByText(/No schedules yet/)).toBeInTheDocument();
    });
  });

  it('shows schedule list', async () => {
    mockFetchSchedules.mockResolvedValue({
      schedules: [
        {
          id: '1',
          target: 'example.com',
          modules: ['dns', 'whois'],
          interval_minutes: 60,
          last_run: null,
          next_run: null,
          enabled: true,
          created_at: new Date().toISOString(),
        },
      ],
      count: 1,
    });
    render(<SchedulePanel />);

    await waitFor(() => {
      expect(screen.getByText('example.com')).toBeInTheDocument();
    });
    expect(screen.getByText('Active')).toBeInTheDocument();
  });

  it('opens create form on button click', async () => {
    mockFetchSchedules.mockResolvedValue({ schedules: [], count: 0 });
    render(<SchedulePanel />);

    fireEvent.click(screen.getByText('New Schedule'));
    expect(screen.getByPlaceholderText('example.com')).toBeInTheDocument();
  });

  it('creates schedule on form submit', async () => {
    mockFetchSchedules.mockResolvedValue({ schedules: [], count: 0 });
    mockCreateSchedule.mockResolvedValue({ id: '2', target: 'test.com', modules: ['dns'], interval_minutes: 30, enabled: true });

    render(<SchedulePanel />);
    fireEvent.click(screen.getByText('New Schedule'));

    const input = screen.getByPlaceholderText('example.com');
    fireEvent.change(input, { target: { value: 'test.com' } });

    fireEvent.click(screen.getByText('Create Schedule'));

    await waitFor(() => {
      expect(mockCreateSchedule).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({ target: 'test.com', modules: expect.any(Array), interval_minutes: expect.any(Number) }),
      );
    });
  });

  it('toggles schedule status', async () => {
    mockFetchSchedules.mockResolvedValue({
      schedules: [
        {
          id: '1',
          target: 'example.com',
          modules: ['dns'],
          interval_minutes: 60,
          last_run: null,
          next_run: null,
          enabled: true,
          created_at: new Date().toISOString(),
        },
      ],
      count: 1,
    });
    mockToggleSchedule.mockResolvedValue({ schedule_id: '1', enabled: false });

    render(<SchedulePanel />);
    await waitFor(() => {
      expect(screen.getByText('example.com')).toBeInTheDocument();
    });

    const pauseBtn = screen.getByTitle('Pause');
    fireEvent.click(pauseBtn);

    await waitFor(() => {
      expect(mockToggleSchedule).toHaveBeenCalledWith(expect.any(String), '1');
    });
  });
});
