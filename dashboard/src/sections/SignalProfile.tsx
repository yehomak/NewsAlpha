import type { Signal, TickerStats } from "../api";

interface Props {
  signals: Signal[] | null;
  tickers: TickerStats[] | null;
}

const ET_LABEL: Record<string, string> = {
  earnings: "Earnings",
  product_launch: "Product Launch",
  macro: "Macro",
  regulatory: "Regulatory",
  executive: "Executive",
  general: "General",
};

const ET_COLOR: Record<string, string> = {
  earnings: "var(--bull)",
  product_launch: "var(--accent)",
  macro: "#6366f1",
  regulatory: "#f43f5e",
  executive: "#0ea5e9",
  general: "var(--text-muted)",
};

const CONF_BUCKETS = [
  { label: "≥0.85", key: "peak",   min: 0.85, max: 1.01, color: "var(--bull)" },
  { label: "0.7–",  key: "high",   min: 0.70, max: 0.85, color: "var(--accent)" },
  { label: "0.5–",  key: "mid",    min: 0.50, max: 0.70, color: "var(--text-dim)" },
  { label: "<0.5",  key: "low",    min: 0,    max: 0.50, color: "var(--bear)" },
];

export function SignalProfile({ signals, tickers }: Props) {
  const etCounts: Record<string, number> = {};
  const dirCounts: Record<string, number> = { bullish: 0, bearish: 0, neutral: 0 };
  const confCounts: Record<string, number> = { peak: 0, high: 0, mid: 0, low: 0 };

  if (signals) {
    for (const s of signals) {
      const et = s.event_type || "general";
      etCounts[et] = (etCounts[et] || 0) + 1;
      dirCounts[s.direction] = (dirCounts[s.direction] || 0) + 1;
      const bucket = CONF_BUCKETS.find(b => s.confidence >= b.min && s.confidence < b.max);
      if (bucket) confCounts[bucket.key]++;
    }
  }

  const total = signals?.length ?? 0;
  const sortedEt = Object.entries(etCounts).sort((a, b) => b[1] - a[1]);

  const topTickers = tickers
    ? [...tickers].sort((a, b) => b.signal_count - a.signal_count).slice(0, 10)
    : [];
  const maxCount = topTickers[0]?.signal_count ?? 1;

  const dirColor: Record<string, string> = {
    bullish: "var(--bull)",
    bearish: "var(--bear)",
    neutral: "var(--neutral)",
  };

  const maxColBar = 60;

  return (
    <div className="card">
      <div className="card-title">Signal Profile</div>

      <div className="profile-grid">
        <div>
          <div className="profile-sub">Event Type Mix <span className="profile-sub-note">last {total} signals</span></div>
          {sortedEt.map(([et, count]) => (
            <div className="source-row" key={et}>
              <span className="source-name" style={{ color: ET_COLOR[et] ?? "var(--text-dim)" }}>
                {ET_LABEL[et] ?? et}
              </span>
              <div className="source-bar-bg">
                <div
                  className="source-bar-fill"
                  style={{ width: `${(count / total) * 100}%`, background: ET_COLOR[et] ?? "var(--accent)" }}
                />
              </div>
              <span className="source-count">{count}</span>
              <span className="source-pct">{Math.round((count / total) * 100)}%</span>
            </div>
          ))}

          <div style={{ display: "flex", gap: 32, marginTop: 20 }}>
            <div>
              <div className="profile-sub">Direction</div>
              <div className="dir-split-row">
                {Object.entries(dirCounts).map(([dir, count]) => (
                  <div key={dir} className="dir-split-item">
                    <div className="dir-split-bar-wrap">
                      <div
                        className="dir-split-bar"
                        style={{
                          height: `${total > 0 ? Math.round((count / total) * maxColBar) : 0}px`,
                          background: dirColor[dir] ?? "var(--neutral)",
                        }}
                      />
                    </div>
                    <div className="dir-split-pct" style={{ color: dirColor[dir] }}>
                      {total > 0 ? Math.round((count / total) * 100) : 0}%
                    </div>
                    <div className="dir-split-label">{dir.slice(0, 4)}</div>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <div className="profile-sub">Confidence</div>
              <div className="dir-split-row">
                {CONF_BUCKETS.map(b => {
                  const count = confCounts[b.key] ?? 0;
                  return (
                    <div key={b.key} className="dir-split-item">
                      <div className="dir-split-bar-wrap">
                        <div
                          className="dir-split-bar"
                          style={{
                            height: `${total > 0 ? Math.round((count / total) * maxColBar) : 0}px`,
                            background: b.color,
                          }}
                        />
                      </div>
                      <div className="dir-split-pct" style={{ color: b.color }}>
                        {total > 0 ? Math.round((count / total) * 100) : 0}%
                      </div>
                      <div className="dir-split-label">{b.label}</div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>

        <div>
          <div className="profile-sub">Top Tickers by Coverage</div>
          {topTickers.map(t => (
            <div className="source-row" key={t.ticker}>
              <span className="source-name" style={{ fontFamily: "var(--font-mono)", fontWeight: 700, color: "var(--text)", width: 64 }}>
                {t.ticker}
              </span>
              <div className="source-bar-bg">
                <div
                  className="source-bar-fill"
                  style={{
                    width: `${(t.signal_count / maxCount) * 100}%`,
                    background: t.last_direction === "bullish" ? "var(--bull)"
                              : t.last_direction === "bearish" ? "var(--bear)"
                              : "var(--neutral)",
                    opacity: 0.8,
                  }}
                />
              </div>
              <span className="source-count">{t.signal_count}</span>
              <span className={`dir-chip ${t.last_direction}`} style={{ fontSize: 9, padding: "1px 4px", marginLeft: 6 }}>
                {t.last_direction.slice(0, 4)}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
