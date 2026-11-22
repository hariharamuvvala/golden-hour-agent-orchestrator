import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import ManualDispatch from '../components/ManualDispatch';

// ── Helpers ──────────────────────────────────────────────────────────────────

function renderForm(onDispatched = vi.fn()) {
  render(<ManualDispatch onDispatched={onDispatched} />);
}

const mockPlan = {
  emergency_id: 'MANUAL-ABC123',
  ambulance: { id: 'BLR-01', name: 'Ambulance BLR-01 (Koramangala)', lat: 12.9279, lon: 77.6271, status: 'dispatched' },
  hospital:  { id: 'HOSP-01', name: 'Manipal Hospital', lat: 12.9592, lon: 77.6473, icu_beds_available: 5, specialties: ['trauma'] },
  distance_to_patient_km: 1.2,
  distance_to_hospital_km: 3.5,
  estimated_eta_min: 4.7,
  reasoning: '[Dispatcher] BLR-01 is 1.2km away. [Hospital] Manipal has 5 ICU beds. [Coordinator] ETA 4.7 min.',
  severity: 'critical',
};


// ── 1. Rendering ─────────────────────────────────────────────────────────────

describe('ManualDispatch — rendering', () => {
  it('renders location dropdown', () => {
    renderForm();
    expect(screen.getByLabelText(/location/i)).toBeInTheDocument();
  });

  it('renders severity dropdown', () => {
    renderForm();
    expect(screen.getByLabelText(/severity/i)).toBeInTheDocument();
  });

  it('renders My Location button', () => {
    renderForm();
    expect(screen.getByRole('button', { name: /my location/i })).toBeInTheDocument();
  });

  it('renders Dispatch Now button', () => {
    renderForm();
    expect(screen.getByRole('button', { name: /dispatch now/i })).toBeInTheDocument();
  });

  it('does NOT show lat/lon inputs by default (landmark selected)', () => {
    renderForm();
    expect(screen.queryByLabelText(/latitude/i)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/longitude/i)).not.toBeInTheDocument();
  });

  it('defaults to Koramangala in the dropdown', () => {
    renderForm();
    expect(screen.getByLabelText(/location/i)).toHaveValue('Koramangala');
  });

  it('defaults severity to critical', () => {
    renderForm();
    expect(screen.getByLabelText(/severity/i)).toHaveValue('critical');
  });
});


// ── 2. Landmark dropdown ──────────────────────────────────────────────────────

describe('ManualDispatch — landmark dropdown', () => {
  it('shows lat/lon inputs when Custom is selected', async () => {
    renderForm();
    await userEvent.selectOptions(screen.getByLabelText(/location/i), 'Custom (enter coordinates)');
    expect(screen.getByLabelText(/latitude/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/longitude/i)).toBeInTheDocument();
    // accepts full WGS-84 precision
    expect(screen.getByLabelText(/latitude/i)).toHaveAttribute('step', 'any');
    expect(screen.getByLabelText(/longitude/i)).toHaveAttribute('step', 'any');
  });

  it('hides lat/lon inputs when switching back to a landmark', async () => {
    renderForm();
    await userEvent.selectOptions(screen.getByLabelText(/location/i), 'Custom (enter coordinates)');
    await userEvent.selectOptions(screen.getByLabelText(/location/i), 'Indiranagar');
    expect(screen.queryByLabelText(/latitude/i)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/longitude/i)).not.toBeInTheDocument();
  });

  it('contains all 14 landmarks plus Custom', () => {
    renderForm();
    const options = screen.getAllByRole('option', { hidden: true });
    // location select has 15 options; severity has 3
    const locationSelect = screen.getByLabelText(/location/i);
    expect(locationSelect.options.length).toBe(15);
  });
});


// ── 3. Severity dropdown ──────────────────────────────────────────────────────

describe('ManualDispatch — severity dropdown', () => {
  it('has critical, serious, stable options', () => {
    renderForm();
    const sel = screen.getByLabelText(/severity/i);
    const values = Array.from(sel.options).map(o => o.value);
    expect(values).toEqual(['critical', 'serious', 'stable']);
  });

  it('dispatch button class matches selected severity', async () => {
    renderForm();
    await userEvent.selectOptions(screen.getByLabelText(/severity/i), 'stable');
    const btn = screen.getByRole('button', { name: /dispatch now/i });
    expect(btn).toHaveClass('stable');
  });
});


// ── 4. Successful dispatch ────────────────────────────────────────────────────

describe('ManualDispatch — successful dispatch', () => {
  beforeEach(() => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockPlan,
    });
  });

  it('calls onDispatched with the plan on success', async () => {
    const onDispatched = vi.fn();
    renderForm(onDispatched);
    await userEvent.click(screen.getByRole('button', { name: /dispatch now/i }));
    await waitFor(() => expect(onDispatched).toHaveBeenCalledWith(mockPlan));
  });

  it('POSTs to /dispatch with correct body', async () => {
    renderForm();
    await userEvent.click(screen.getByRole('button', { name: /dispatch now/i }));
    await waitFor(() => expect(global.fetch).toHaveBeenCalledWith(
      'http://localhost:8000/dispatch',
      expect.objectContaining({
        method: 'POST',
        body: expect.stringContaining('"severity":"critical"'),
      })
    ));
  });

  it('POSTs Koramangala coords by default', async () => {
    renderForm();
    await userEvent.click(screen.getByRole('button', { name: /dispatch now/i }));
    await waitFor(() => {
      const body = JSON.parse(global.fetch.mock.calls[0][1].body);
      expect(body.lat).toBe(12.9279);
      expect(body.lon).toBe(77.6271);
    });
  });

  it('shows Dispatching… while loading', async () => {
    // Never resolve so we can catch the loading state
    global.fetch = vi.fn().mockReturnValue(new Promise(() => {}));
    renderForm();
    await userEvent.click(screen.getByRole('button', { name: /dispatch now/i }));
    expect(screen.getByRole('button', { name: /dispatching/i })).toBeDisabled();
  });
});


// ── 5. Error handling ─────────────────────────────────────────────────────────

describe('ManualDispatch — error handling', () => {
  it('shows error message on 503', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      json: async () => ({ detail: 'No available ambulance or hospital' }),
    });
    renderForm();
    await userEvent.click(screen.getByRole('button', { name: /dispatch now/i }));
    await waitFor(() =>
      expect(screen.getByText(/no available ambulance or hospital/i)).toBeInTheDocument()
    );
  });

  it('shows error on network failure', async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error('Network error'));
    renderForm();
    await userEvent.click(screen.getByRole('button', { name: /dispatch now/i }));
    await waitFor(() =>
      expect(screen.getByText(/network error/i)).toBeInTheDocument()
    );
  });
});


// ── 6. Geolocation ───────────────────────────────────────────────────────────

describe('ManualDispatch — geolocation', () => {
  it('shows error when geolocation is not supported', async () => {
    // Remove geolocation from navigator
    const originalGeo = navigator.geolocation;
    Object.defineProperty(navigator, 'geolocation', { value: undefined, configurable: true });

    renderForm();
    await userEvent.click(screen.getByRole('button', { name: /my location/i }));
    expect(screen.getByText(/not supported/i)).toBeInTheDocument();

    Object.defineProperty(navigator, 'geolocation', { value: originalGeo, configurable: true });
  });

  it('fills lat/lon and switches to Custom on successful geolocation', async () => {
    const mockGeo = {
      getCurrentPosition: vi.fn((success) =>
        success({ coords: { latitude: 12.9716, longitude: 77.5946 } })
      ),
    };
    Object.defineProperty(navigator, 'geolocation', { value: mockGeo, configurable: true });

    renderForm();
    await userEvent.click(screen.getByRole('button', { name: /my location/i }));

    await waitFor(() =>
      expect(screen.getByLabelText(/location/i)).toHaveValue('Custom (enter coordinates)')
    );
    expect(screen.getByLabelText(/latitude/i)).toHaveValue(12.9716);
    expect(screen.getByLabelText(/longitude/i)).toHaveValue(77.5946);
    expect(screen.getByText(/12\.9716/)).toBeInTheDocument(); // geo status
  });

  it('shows permission denied error', async () => {
    const mockGeo = {
      getCurrentPosition: vi.fn((_, error) =>
        error({ code: 1, PERMISSION_DENIED: 1 }) // code 1 = PERMISSION_DENIED
      ),
    };
    Object.defineProperty(navigator, 'geolocation', { value: mockGeo, configurable: true });

    renderForm();
    await userEvent.click(screen.getByRole('button', { name: /my location/i }));

    await waitFor(() =>
      expect(screen.getByText(/location access denied/i)).toBeInTheDocument()
    );
  });
});
