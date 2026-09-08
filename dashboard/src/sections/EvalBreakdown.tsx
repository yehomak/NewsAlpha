import type { EvalSummary } from "../api";

interface Props {
  evalSummary: EvalSummary | null;
}

function AccBar({ pct }: { pct: number }) {
  const color = pct >= 55 ? "var(--bull)" : pct < 45 ? "var(--bear)" : "var(--neutral)";
  return (
    <div style={{ flex: 1, height: 6, background: "var(--border)", borderRadius: 3, overflow: "hidden" }}>
      <div style={{ width: `${pct}%`, height: "100%", background: color, borderRadius: 3 }} />
    </div>
  );
}

export function EvalBreakdown({ evalSummary: ev }: Props) {
  if (!ev) return <div className="card"><div className="loading">loading…</div></div>;

  return (
    <div className="card">
      <div className="card-title">Accuracy Breakdown</div>

      {ev.evaluated === 0 ? (
        <div className="loading" style={{ padding: "24px 0" }}>
          No evaluated signals yet — first T+5 results expected Sep 13
        </div>
      ) : (
        <>
          <div style={{ marginBottom: 20 }}>
            <div className="card-title" style={{ marginBottom: 10 }}>By Direction</div>
            {ev.by_direction.map(d => (
              <div className="breakdown-row" key={d.direction}>
                <span className={`dir-chip ${d.direction}`} style={{ width: 70 }}>{d.direction}</span>
                <AccBar pct={d.accuracy_pct} />
                <span className="breakdown-acc">{d.accuracy_pct}%</span>
                <span className="breakdown-meta">{d.correct}/{d.total}</span>
              </div>
            ))}
          </div>

          <div>
            <div className="card-title" style={{ marginBottom: 10 }}>By Event Type</div>
            {ev.by_event_type.map(e => (
              <div className="breakdown-row" key={e.event_type}>
                <span className="breakdown-label">{e.event_type}</span>
                <AccBar pct={e.accuracy_pct} />
                <span className="breakdown-acc">{e.accuracy_pct}%</span>
                <span className="breakdown-meta">{e.correct}/{e.total}</span>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
