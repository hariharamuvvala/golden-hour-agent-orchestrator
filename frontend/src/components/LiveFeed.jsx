export default function LiveFeed({ events }) {
  if (events.length === 0) {
    return <p className="empty-state">Waiting for first emergency dispatch…</p>;
  }

  return (
    <div className="feed-list">
      {events.map((e) => (
        <div key={e.emergency_id} className={`feed-item ${e.severity || 'stable'}`}>
          <div className="top-row">
            <span className="amb-hosp">
              {e.ambulance.id} → {e.hospital.name}
            </span>
            <span className="badge" style={{
              background: e.severity === 'critical' ? '#3d1a1a' : e.severity === 'serious' ? '#2d2008' : '#0d2a16',
              color: e.severity === 'critical' ? '#f85149' : e.severity === 'serious' ? '#d29922' : '#3fb950',
            }}>
              {e.severity}
            </span>
          </div>
          <div className="eta">ETA: {e.estimated_eta_min} min · {e.distance_to_patient_km} km to patient · {e.distance_to_hospital_km} km to hospital</div>
          <div className="reasoning">{e.reasoning}</div>
        </div>
      ))}
    </div>
  );
}
