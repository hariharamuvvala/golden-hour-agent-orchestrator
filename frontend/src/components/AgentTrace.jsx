// Parses the reasoning string into 3 steps by [Dispatcher], [Hospital], [Coordinator] tags
function parseReasoning(reasoning) {
  const dispatcher  = reasoning.match(/\[Dispatcher\](.*?)(?=\[Hospital\]|$)/)?.[1]?.trim() ?? '';
  const hospital    = reasoning.match(/\[Hospital\](.*?)(?=\[Coordinator\]|$)/)?.[1]?.trim() ?? '';
  const coordinator = reasoning.match(/\[Coordinator\](.*?)$/)?.[1]?.trim() ?? '';
  return { dispatcher, hospital, coordinator };
}

export default function AgentTrace({ event }) {
  if (!event) {
    return <p className="empty-state">No dispatch yet — waiting for first event.</p>;
  }

  const { dispatcher, hospital, coordinator } = parseReasoning(event.reasoning);

  return (
    <div className="trace-steps">
      <div className="trace-step">
        <div className="trace-icon dispatcher">D</div>
        <div className="trace-body">
          <div className="trace-label">Dispatcher Agent</div>
          <div className="trace-text">{dispatcher}</div>
        </div>
      </div>
      <div className="trace-step">
        <div className="trace-icon hospital">H</div>
        <div className="trace-body">
          <div className="trace-label">Hospital Agent</div>
          <div className="trace-text">{hospital}</div>
        </div>
      </div>
      <div className="trace-step">
        <div className="trace-icon coordinator">C</div>
        <div className="trace-body">
          <div className="trace-label">Coordinator Agent</div>
          <div className="trace-text">{coordinator}</div>
        </div>
      </div>
    </div>
  );
}
