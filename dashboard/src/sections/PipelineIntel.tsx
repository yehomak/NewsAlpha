import type { PipelineStats, EventStats, CostStats, Signal } from "../api";

interface Props {
  pipeline: PipelineStats | null;
  events: EventStats | null;
  costs: CostStats | null;
  signals: Signal[] | null;
}

function pct(n: number, d: number): string {
  return d > 0 ? `${Math.round((n / d) * 100)}%` : "—";
}

export function PipelineIntel({ pipeline, events, costs, signals }: Props) {
  // Yield funnel: events → signals
  const totalProcessed = events?.processed ?? 0;
  const deduped = events?.dedup_skipped ?? 0;
  const realProcessed = totalProcessed - deduped;
  const totalSignals = costs?.signal_count ?? 0;
  const rejected = realProcessed > 0 ? realProcessed - totalSignals : null;

  // Cost stats
  const avgCost = costs?.avg_cost_per_signal ?? null;
  const totalCost = costs?.total_cost_usd ?? 0;

  // Daily sparkline
  const byDay = costs?.by_day ?? [];
  const maxDaySignals = Math.max(...byDay.map(d => d.signal_count), 1);

  // Outliers from signals sample
  const highConf = signals
    ? [...signals].sort((a, b) => b.confidence - a.confidence).slice(0, 3)
    : [];
  const expensive = signals
    ? [...signals].sort((a, b) => Number(b.cost_usd) - Number(a.cost_usd)).slice(0, 3)
    : [];
  const avgCostSample = signals && signals.length > 0
    ? signals.reduce((s, x) => s + Number(x.cost_usd), 0) / signals.length
    : null;

  return (
    <div className="card">
      <div className="card-title">Pipeline Intelligence</div>

      <div className="profile-grid">
        {/* Left: yield funnel + cost */}
        <div>
          <div className="profile-sub">Event → Signal Funnel</div>
          <div className="funnel-rows">
            <div className="funnel-row">
              <span className="funnel-label">Ingested</span>
              <span className="funnel-val mono">{(events?.total ?? 0).toLocaleString()}</span>
            </div>
            <div className="funnel-row">
              <span className="funnel-label">Dedup skipped</span>
              <span className="funnel-val mono" style={{ color: "var(--text-muted)" }}>
                −{deduped.toLocaleString()} <span className="funnel-pct">({pct(deduped, events?.total ?? 0)})</span>
              </span>
            </div>
            <div className="funnel-row">
              <span className="funnel-label">Sent to LLM</span>
              <span className="funnel-val mono">{realProcessed.toLocaleString()}</span>
            </div>
            {rejected !== null && (
              <div className="funnel-row">
                <span className="funnel-label">Rejected / truncated</span>
                <span className="funnel-val mono" style={{ color: "var(--bear)" }}>
                  −{rejected.toLocaleString()} <span className="funnel-pct">({pct(rejected, realProcessed)})</span>
                </span>
              </div>
            )}
            <div className="funnel-row funnel-total">
              <span className="funnel-label">Signals produced</span>
              <span className="funnel-val mono" style={{ color: "var(--bull)" }}>
                {totalSignals.toLocaleString()} <span className="funnel-pct">({pct(totalSignals, realProcessed)} yield)</span>
              </span>
            </div>
          </div>

          <div className="profile-sub" style={{ marginTop: 20 }}>Cost Breakdown</div>
          <div className="funnel-rows">
            <div className="funnel-row">
              <span className="funnel-label">Total spend</span>
              <span className="funnel-val mono">${totalCost.toFixed(4)}</span>
            </div>
            <div className="funnel-row">
              <span className="funnel-label">Avg / signal</span>
              <span className="funnel-val mono">
                {avgCost != null ? `$${avgCost.toFixed(4)}` : "—"}
              </span>
            </div>
            {avgCostSample != null && (
              <div className="funnel-row">
                <span className="funnel-label">Avg / signal (sample)</span>
                <span className="funnel-val mono">${avgCostSample.toFixed(4)}</span>
              </div>
            )}
            <div className="funnel-row">
              <span className="funnel-label">Today's signals</span>
              <span className="funnel-val mono">{pipeline?.signals_today ?? "—"}</span>
            </div>
            <div className="funnel-row">
              <span className="funnel-label">Today's events</span>
              <span className="funnel-val mono">{pipeline?.events_today ?? "—"}</span>
            </div>
          </div>
        </div>

        {/* Right: daily bars + outliers */}
        <div>
          {byDay.length > 0 && (
            <>
              <div className="profile-sub">Daily Signal Output</div>
              <div className="sparkbar-row">
                {byDay.slice(-14).map(d => (
                  <div key={d.date} className="sparkbar-col">
                    <div className="sparkbar-tip">{d.signal_count}</div>
                    <div
                      className="sparkbar"
                      style={{ height: `${Math.round((d.signal_count / maxDaySignals) * 48) + 2}px` }}
                    />
                    <div className="sparkbar-label">{d.date.slice(5)}</div>
                  </div>
                ))}
              </div>
            </>
          )}

          <div className="profile-sub" style={{ marginTop: 20 }}>High Conviction <span className="profile-sub-note">conf ≥ 0.85</span></div>
          {highConf.filter(s => s.confidence >= 0.85).length === 0 ? (
            <div style={{ fontSize: 12, color: "var(--text-muted)" }}>none in sample</div>
          ) : (
            highConf.filter(s => s.confidence >= 0.85).map(s => (
              <div key={s.id} className="outlier-row">
                <span className="ticker-cell" style={{ fontSize: 12, width: 52 }}>{s.ticker}</span>
                <span className={`dir-chip ${s.direction}`} style={{ fontSize: 9, padding: "1px 4px" }}>
                  {s.direction.slice(0, 4)}
                </span>
                <span className="funnel-pct" style={{ marginLeft: 8 }}>
                  conf {Math.round(s.confidence * 100)}%
                </span>
              </div>
            ))
          )}

          <div className="profile-sub" style={{ marginTop: 16 }}>Most Expensive Signals</div>
          {expensive.map(s => (
            <div key={s.id} className="outlier-row">
              <span className="ticker-cell" style={{ fontSize: 12, width: 52 }}>{s.ticker}</span>
              <span className="funnel-val mono" style={{ fontSize: 11 }}>${Number(s.cost_usd).toFixed(4)}</span>
              <span className="funnel-pct" style={{ marginLeft: 8 }}>
                {s.event_type}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
