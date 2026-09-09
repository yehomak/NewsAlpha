import { Fragment, useState } from "react";
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

function CorrectBadge({ correct, returnPct }: { correct: boolean | null; returnPct: number | null }) {
  if (correct === null) return <span className="correct-badge pending">pending</span>;
  const pct = returnPct != null ? ` ${returnPct > 0 ? "+" : ""}${returnPct.toFixed(1)}%` : "";
  return correct
    ? <span className="correct-badge yes">✓{pct}</span>
    : <span className="correct-badge no">✗{pct}</span>;
}

export function SignalFeed({ signals }: Props) {
  const [expanded, setExpanded] = useState<number | null>(null);
  if (!signals) return <div className="card"><div className="loading">loading…</div></div>;

  return (
    <div className="card">
      <div className="card-title">Signal Feed · {signals.length} signals</div>
      <div className="tbl-wrap">
        <table>
          <thead>
            <tr>
              <th>Ticker</th>
              <th>Direction</th>
              <th>Conf</th>
              <th>Type</th>
              <th>Reasoning</th>
              <th>Age</th>
              <th>Result</th>
            </tr>
          </thead>
          <tbody>
            {signals.slice(0, 30).flatMap(s => {
              const isOpen = expanded === s.id;
              const rows = [
                <Fragment key={s.id}>
                  <tr
                    style={{ cursor: "pointer" }}
                    onClick={() => setExpanded(isOpen ? null : s.id)}
                  >
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
                    <td className="reasoning-cell" title={s.reasoning}>
                      {s.reasoning.length > 90 ? s.reasoning.slice(0, 90) + "…" : s.reasoning}
                    </td>
                    <td className="mono" style={{ color: "var(--text-muted)", fontSize: 11 }}>
                      {timeAgo(s.created_at)}
                    </td>
                    <td><CorrectBadge correct={s.correct} returnPct={s.return_pct} /></td>
                  </tr>
                  {isOpen && (
                    <tr>
                      <td colSpan={7} className="reasoning-expanded">
                        <div className="reasoning-full">{s.reasoning}</div>
                        <div className="reasoning-meta mono">
                          signal #{s.id} · cost ${s.cost_usd.toFixed(4)} · {new Date(s.created_at).toUTCString()}
                        </div>
                      </td>
                    </tr>
                  )}
                </Fragment>,
              ];
              return rows;
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
