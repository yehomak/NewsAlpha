import type { EventStats } from "../api";

interface Props {
  events: EventStats | null;
}

export function EventIntelligence({ events: ev }: Props) {
  if (!ev) return <div className="card"><div className="loading">loading…</div></div>;

  const maxCount = Math.max(...ev.by_source.map(s => s.count), 1);

  return (
    <div className="card">
      <div className="card-title">Event Intelligence</div>

      <div className="intel-grid">
        <div className="intel-stat">
          <div className="intel-num">{ev.total.toLocaleString()}</div>
          <div className="intel-lbl">Total</div>
        </div>
        <div className="intel-stat">
          <div className="intel-num" style={{ color: "var(--bull)" }}>{ev.processed.toLocaleString()}</div>
          <div className="intel-lbl">Processed</div>
        </div>
        <div className="intel-stat">
          <div className="intel-num" style={{ color: "var(--text-muted)" }}>{ev.unprocessed.toLocaleString()}</div>
          <div className="intel-lbl">Pending</div>
        </div>
        <div className="intel-stat">
          <div className="intel-num" style={{ color: "var(--accent)" }}>{ev.dedup_skipped.toLocaleString()}</div>
          <div className="intel-lbl">Deduped</div>
        </div>
      </div>

      <div className="card-title" style={{ marginBottom: 10 }}>By Source</div>
      {ev.by_source.map(s => (
        <div className="source-row" key={s.source}>
          <span className="source-name">{s.source}</span>
          <div className="source-bar-bg">
            <div
              className="source-bar-fill"
              style={{ width: `${(s.count / maxCount) * 100}%` }}
            />
          </div>
          <span className="source-count">{s.count}</span>
        </div>
      ))}
    </div>
  );
}
