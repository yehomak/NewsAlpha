import type { TickerStats } from "../api";

interface Props {
  tickers: TickerStats[] | null;
  onSelect: (t: TickerStats) => void;
}

function accuracyClass(pct: number | null): string {
  if (pct == null) return "";
  if (pct >= 55) return "good";
  if (pct < 45) return "bad";
  return "";
}

export function TickerGrid({ tickers, onSelect }: Props) {
  if (!tickers) return <div className="card"><div className="loading">loading…</div></div>;

  return (
    <div className="card">
      <div className="card-title">Companies · {tickers.length} tickers</div>
      <div className="ticker-grid">
        {tickers.slice(0, 24).map(t => (
          <div
            className="ticker-card clickable"
            key={t.ticker}
            onClick={() => onSelect(t)}
            role="button"
            tabIndex={0}
            onKeyDown={e => e.key === "Enter" && onSelect(t)}
          >
            <div className="ticker-card-header">
              <span className="ticker-symbol">{t.ticker}</span>
              <span className={`dir-chip ${t.last_direction}`}>{t.last_direction}</span>
            </div>
            <div className="ticker-meta">
              <span>{t.signal_count} signal{t.signal_count !== 1 ? "s" : ""}</span>
              <span>conf {Math.round(t.avg_confidence * 100)}%</span>
              {t.evaluated_count > 0 && (
                <span style={{ color: "var(--text-dim)" }}>
                  {t.correct_count}/{t.evaluated_count} correct
                </span>
              )}
            </div>
            <div className={`ticker-accuracy ${accuracyClass(t.accuracy_pct)}`}>
              {t.accuracy_pct != null ? `${t.accuracy_pct}% acc` : "no eval yet"}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
