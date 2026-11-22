import { useState } from 'react';

const BACKEND = 'http://localhost:8000';

export default function ManualDispatch({ onDispatched }) {
  const [lat, setLat]           = useState('12.9716');
  const [lon, setLon]           = useState('77.5946');
  const [severity, setSeverity] = useState('critical');
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState('');

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await fetch(`${BACKEND}/dispatch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lat: parseFloat(lat), lon: parseFloat(lon), severity }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail ?? `HTTP ${res.status}`);
      }
      const plan = await res.json();
      onDispatched(plan);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="manual-dispatch" onSubmit={handleSubmit}>
      <div className="md-row">
        <label>
          Latitude
          <input
            type="number" step="0.0001" min="12.80" max="13.10"
            value={lat} onChange={e => setLat(e.target.value)} required
          />
        </label>
        <label>
          Longitude
          <input
            type="number" step="0.0001" min="77.45" max="77.80"
            value={lon} onChange={e => setLon(e.target.value)} required
          />
        </label>
        <label>
          Severity
          <select value={severity} onChange={e => setSeverity(e.target.value)}>
            <option value="critical">Critical</option>
            <option value="serious">Serious</option>
            <option value="stable">Stable</option>
          </select>
        </label>
        <button type="submit" disabled={loading} className={`dispatch-btn ${severity}`}>
          {loading ? 'Dispatching…' : '🚑 Dispatch Now'}
        </button>
      </div>
      {error && <div className="md-error">{error}</div>}
    </form>
  );
}
