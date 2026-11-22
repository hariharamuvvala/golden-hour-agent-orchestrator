import { useEffect, useRef, useState } from 'react';
import './styles/app.css';
import LiveFeed from './components/LiveFeed';
import StatusGrid from './components/StatusGrid';
import AgentTrace from './components/AgentTrace';

const BACKEND = 'http://localhost:8000';

export default function App() {
  const [events, setEvents]         = useState([]);
  const [ambulances, setAmbulances] = useState([]);
  const [hospitals, setHospitals]   = useState([]);
  const esRef = useRef(null);

  // SSE connection
  useEffect(() => {
    const es = new EventSource(`${BACKEND}/stream`);
    esRef.current = es;

    es.onmessage = (e) => {
      try {
        const plan = JSON.parse(e.data);
        setEvents((prev) => [plan, ...prev].slice(0, 50)); // keep last 50
      } catch {/* ignore malformed frames */}
    };

    es.onerror = () => {
      // Browser will auto-reconnect; nothing to do here
    };

    return () => es.close();
  }, []);

  // Poll /status every 3 s
  useEffect(() => {
    const fetchStatus = () => {
      fetch(`${BACKEND}/status`)
        .then((r) => r.json())
        .then((d) => {
          setAmbulances(d.ambulances ?? []);
          setHospitals(d.hospitals ?? []);
        })
        .catch(() => {/* backend not ready yet */});
    };

    fetchStatus();
    const id = setInterval(fetchStatus, 3000);
    return () => clearInterval(id);
  }, []);

  return (
    <>
      <header className="header">
        <div className="pulse" />
        <h1>🚑 Golden Hour — Agent Orchestrator</h1>
        <span style={{ marginLeft: 'auto', fontSize: 12, color: '#8b949e' }}>
          {events.length} dispatch{events.length !== 1 ? 'es' : ''} · Bangalore
        </span>
      </header>

      <div className="dashboard">
        {/* Live Feed — full width */}
        <div className="panel panel-full">
          <h2>Live Dispatch Feed</h2>
          <LiveFeed events={events} />
        </div>

        {/* Agent Trace */}
        <div className="panel">
          <h2>Agent Trace — latest event</h2>
          <AgentTrace event={events[0] ?? null} />
        </div>

        {/* Status Grid */}
        <div className="panel">
          <h2>Fleet &amp; Hospital Status</h2>
          <StatusGrid ambulances={ambulances} hospitals={hospitals} />
        </div>
      </div>
    </>
  );
}
