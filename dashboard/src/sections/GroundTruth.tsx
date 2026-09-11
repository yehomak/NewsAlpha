import type { EvalSummary } from "../api";

interface Props {
  evalSummary: EvalSummary | null;
}

function AccBar({ pct, n }: { pct: number; n: number }) {
  const color = pct >= 60 ? "var(--bull)" : pct >= 45 ? "var(--accent)" : "var(--bear)";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <div
        style={{
          flex: 1,
          height: 4,
          background: "var(--border)",
          borderRadius: 2,
          overflow: "hidden",
        }}
      >
        <div style={{ width: `${pct}%`, height: "100%", background: color, borderRadius: 2 }} />
      </div>
      <span className="mono" style={{ fontSize: 11, color, width: 36, textAlign: "right" }}>
        {pct.toFixed(0)}%
      </span>
      <span style={{ fontSize: 10, color: "var(--text-muted)", width: 28 }}>n={n}</span>
    </div>
  );
}

export function GroundTruth({ evalSummary }: Props) {
  const pending = evalSummary == null;
  const hasResults = evalSummary != null && evalSummary.evaluated > 0;

  return (
    <section className="card">
      <div className="section-header">
        <div className="section-step">04</div>
        <div>
          <div className="section-title">Ground Truth</div>
          <div className="section-desc">
            T+5 eval: each signal's predicted direction is compared to the actual price change
            5 trading days after the event. A signal is "correct" if direction matches the sign
            of <code>return_pct = (price_t5 - price_t0) / price_t0</code>. Random baseline is ~50%.
            Target: &gt;55% sustained over ≥50 signals.
          </div>
        </div>
      </div>

      {pending && (
        <div className="eval-pending">
          <div className="eval-pending-icon">◌</div>
          <div className="eval-pending-title">No eval data yet</div>
          <div className="eval-pending-desc">
            Waiting for the first T+5 windows to close. Signals must be at least 5 trading days old
            before price data can be fetched and accuracy computed.
            First results expected ~Sep 13, 2026.
          </div>
        </div>
      )}

      {!pending && !hasResults && (
        <div className="eval-pending">
          <div className="eval-pending-icon">◌</div>
          <div className="eval-pending-title">Eval data loading</div>
          <div className="eval-pending-desc">
            {evalSummary!.pending} signal{evalSummary!.pending !== 1 ? "s" : ""} pending T+5 resolution.
            No completed evals yet.
          </div>
        </div>
      )}

      {hasResults && evalSummary && (
        <div>
          <div className="stat-row">
            <div className="stat-item">
              <div
                className={`stat-val ${
                  (evalSummary.accuracy_pct ?? 0) >= 55
                    ? "bull"
                    : (evalSummary.accuracy_pct ?? 0) >= 45
                    ? "accent"
                    : "bear"
                }`}
              >
                {evalSummary.accuracy_pct != null ? `${evalSummary.accuracy_pct.toFixed(1)}%` : "—"}
              </div>
              <div className="stat-lbl">Overall accuracy</div>
            </div>
            <div className="stat-item">
              <div className="stat-val">{evalSummary.evaluated.toLocaleString()}</div>
              <div className="stat-lbl">Evaluated signals</div>
            </div>
            <div className="stat-item">
              <div className="stat-val muted">{evalSummary.pending.toLocaleString()}</div>
              <div className="stat-lbl">Pending T+5</div>
            </div>
            <div className="stat-item">
              <div className="stat-val">
                {evalSummary.avg_return_pct != null
                  ? `${evalSummary.avg_return_pct > 0 ? "+" : ""}${evalSummary.avg_return_pct.toFixed(2)}%`
                  : "—"}
              </div>
              <div className="stat-lbl">Avg T+5 return</div>
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginTop: 4 }}>
            <div>
              <div className="sub-label">Accuracy by direction</div>
              {evalSummary.by_direction.map(row => (
                <div key={row.direction} style={{ padding: "8px 0", borderBottom: "1px solid var(--border)" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                    <span className={`dir-chip ${row.direction}`}>
                      {row.direction.slice(0, 4)}
                    </span>
                    <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
                      {row.correct}/{row.total} correct
                    </span>
                  </div>
                  <AccBar pct={row.accuracy_pct} n={row.total} />
                </div>
              ))}
              <div style={{ marginTop: 12, fontSize: 11, color: "var(--text-muted)", lineHeight: 1.6 }}>
                Direction-level accuracy reveals whether bearish or bullish signals have better predictive
                value. A gap &gt;10pp between directions suggests asymmetric signal quality.
              </div>
            </div>

            <div>
              <div className="sub-label">Accuracy by event type</div>
              {evalSummary.by_event_type.map(row => (
                <div key={row.event_type} style={{ padding: "8px 0", borderBottom: "1px solid var(--border)" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                    <span style={{ fontSize: 12, color: "var(--text-dim)" }}>
                      {row.event_type}
                    </span>
                    <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
                      {row.correct}/{row.total}
                    </span>
                  </div>
                  <AccBar pct={row.accuracy_pct} n={row.total} />
                </div>
              ))}
              <div style={{ marginTop: 12, fontSize: 11, color: "var(--text-muted)", lineHeight: 1.6 }}>
                Event types with low n (&lt;10) are statistically noisy. Focus on earnings and macro
                categories for reliable accuracy signals.
              </div>
            </div>
          </div>

          <div style={{ marginTop: 16, fontSize: 11, color: "var(--text-muted)", paddingTop: 12, borderTop: "1px solid var(--border)" }}>
            <strong style={{ color: "var(--text-dim)" }}>Look-ahead bias note:</strong> T+0 price
            is fetched at signal creation time; T+5 is fetched after market close 5 trading days later.
            The eval job runs every 6h. No future price data is used in extraction.
            As of {new Date(evalSummary.as_of).toLocaleDateString()}.
          </div>
        </div>
      )}
    </section>
  );
}
