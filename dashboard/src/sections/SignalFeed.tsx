import type { Signal } from "../api";

interface Props {
  signals: Signal[] | null;
}

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return "just now";
  if (m < 60) return `${m}m`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h`;
  return `${Math.floor(h / 24)}d`;
}

function CorrectBadge({ correct }: { correct: boolean | null }) {
  if (correct === null) return <span className="correct-badge pending">pending</span>;
  return correct
    ? <span className="correct-badge yes">✓</span>
    : <span className="correct-badge no">✗</span>;
}

export function SignalFeed({ signals }: Props) {
  if (!signals) return <div className="card"><div className="loading">loading…</div></div>;

  return (
    <div className="card">
      <div className="card-title">Signal Feed</div>
      <div className="tbl-wrap">
        <table>
          <thead>
            <tr>
              <th>Ticker</th>
              <th>Direction</th>
              <th>Conf</th>
              <th>Type</th>
              <th>Age</th>
              <th>Eval</th>
            </tr>
          </thead>
          <tbody>
            {signals.slice(0, 20).map(s => (
              <tr key={s.id}>
                <td className="ticker-cell">{s.ticker}</td>
                <td>
                  <span className={`dir-chip ${s.direction}`}>{s.direction}</span>
                </td>
                <td>
                  <div className="conf-bar-wrap">
                    <div className="conf-bar-bg">
                      <div
                        className="conf-bar-fill"
                        style={{ width: `${Math.round(s.confidence * 100)}%` }}
                      />
                    </div>
                    <span className="conf-val">{Math.round(s.confidence * 100)}</span>
                  </div>
                </td>
                <td className="mono" style={{ fontSize: 11 }}>{s.event_type}</td>
                <td className="mono" style={{ color: "var(--text-muted)", fontSize: 11 }}>
                  {timeAgo(s.created_at)}
                </td>
                <td><CorrectBadge correct={s.correct} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
