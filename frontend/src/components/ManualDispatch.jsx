import { useState } from 'react';

const BACKEND = 'http://localhost:8000';

const LANDMARKS = [
  { label: 'Koramangala',    lat: 12.9279, lon: 77.6271 },
  { label: 'Indiranagar',    lat: 12.9784, lon: 77.6408 },
  { label: 'Jayanagar',      lat: 12.9252, lon: 77.5832 },
  { label: 'Hebbal',         lat: 13.0350, lon: 77.5970 },
  { label: 'Whitefield',     lat: 12.9698, lon: 77.7500 },
  { label: 'Marathahalli',   lat: 12.9591, lon: 77.6974 },
  { label: 'HSR Layout',     lat: 12.9116, lon: 77.6474 },
  { label: 'Electronic City',lat: 12.8399, lon: 77.6770 },
  { label: 'Rajajinagar',    lat: 12.9906, lon: 77.5520 },
  { label: 'Yelahanka',      lat: 13.1007, lon: 77.5963 },
  { label: 'MG Road',        lat: 12.9756, lon: 77.6097 },
  { label: 'Banashankari',   lat: 12.9255, lon: 77.5468 },
  { label: 'Bellandur',      lat: 12.9259, lon: 77.6762 },
  { label: 'Malleshwaram',   lat: 13.0035, lon: 77.5703 },
  { label: 'Custom (enter coordinates)', lat: null, lon: null },
];

export default function ManualDispatch({ onDispatched }) {
  const [landmark, setLandmark]   = useState(LANDMARKS[0].label);
  const [lat, setLat]             = useState(String(LANDMARKS[0].lat));
  const [lon, setLon]             = useState(String(LANDMARKS[0].lon));
  const [severity, setSeverity]   = useState('critical');
  const [loading, setLoading]     = useState(false);
  const [geoLoading, setGeoLoading] = useState(false);
  const [error, setError]         = useState('');
  const [geoStatus, setGeoStatus] = useState('');

  const isCustom = landmark === 'Custom (enter coordinates)';

  function handleLandmarkChange(e) {
    const selected = LANDMARKS.find(l => l.label === e.target.value);
    setLandmark(selected.label);
    if (selected.lat !== null) {
      setLat(String(selected.lat));
      setLon(String(selected.lon));
    }
  }

  function handleUseMyLocation() {
    if (!navigator.geolocation) {
      setError('Geolocation is not supported by this browser.');
      return;
    }
    setGeoLoading(true);
    setGeoStatus('Detecting location…');
    setError('');
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const { latitude, longitude } = pos.coords;
        setLat(latitude.toFixed(6));
        setLon(longitude.toFixed(6));
        setLandmark('Custom (enter coordinates)');
        setGeoStatus(`📍 ${latitude.toFixed(4)}, ${longitude.toFixed(4)}`);
        setGeoLoading(false);
      },
      (err) => {
        setGeoStatus('');
        setGeoLoading(false);
        if (err.code === err.PERMISSION_DENIED) {
          setError('Location access denied. Pick a landmark or enter coordinates manually.');
        } else {
          setError('Could not get location. Pick a landmark or enter coordinates manually.');
        }
      },
      { timeout: 8000 }
    );
  }

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
      setGeoStatus('');
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

        {/* Landmark dropdown */}
        <label>
          Location
          <select value={landmark} onChange={handleLandmarkChange} style={{ width: 180 }}>
            {LANDMARKS.map(l => (
              <option key={l.label} value={l.label}>{l.label}</option>
            ))}
          </select>
        </label>

        {/* Show lat/lon only when custom */}
        {isCustom && (
          <>
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
          </>
        )}

        {/* Severity */}
        <label>
          Severity
          <select value={severity} onChange={e => setSeverity(e.target.value)}>
            <option value="critical">Critical</option>
            <option value="serious">Serious</option>
            <option value="stable">Stable</option>
          </select>
        </label>

        {/* Use my location */}
        <button
          type="button"
          className="geo-btn"
          onClick={handleUseMyLocation}
          disabled={geoLoading}
          title="Detect my GPS location"
        >
          {geoLoading ? '…' : '📍 My Location'}
        </button>

        {/* Dispatch */}
        <button type="submit" disabled={loading} className={`dispatch-btn ${severity}`}>
          {loading ? 'Dispatching…' : '🚑 Dispatch Now'}
        </button>
      </div>

      {/* Geo status feedback */}
      {geoStatus && !error && (
        <div className="md-geo-status">{geoStatus}</div>
      )}
      {error && <div className="md-error">{error}</div>}
    </form>
  );
}
