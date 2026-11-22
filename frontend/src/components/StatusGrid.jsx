export default function StatusGrid({ ambulances, hospitals }) {
  return (
    <div>
      <div className="status-section-title">Ambulances</div>
      <div className="card-grid">
        {ambulances.map((a) => (
          <div key={a.id} className={`amb-card ${a.status}`}>
            <div className="card-name" title={a.name}>{a.id}</div>
            <div className="card-name" style={{ fontSize: '11px', color: '#8b949e', fontWeight: 400 }}>
              {a.name.replace(/Ambulance BLR-\d+ \(/, '').replace(')', '')}
            </div>
            <div className="card-status">{a.status}</div>
          </div>
        ))}
      </div>

      <div className="status-section-title" style={{ marginTop: 14 }}>Hospitals</div>
      <div className="card-grid">
        {hospitals.map((h) => (
          <div key={h.id} className="hosp-card">
            <div className="card-name" title={h.name}>{h.name}</div>
            <div className="icu">ICU beds: <span>{h.icu_beds_available}</span></div>
          </div>
        ))}
      </div>
    </div>
  );
}
