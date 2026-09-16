import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  Cell,
  ResponsiveContainer,
} from "recharts";
import type { EvalSummary } from "../api";

interface Props {
  evalSummary: EvalSummary | null;
}

function AccBar({ pct, n }: { pct: number; n: number }) {
  const color = pct >= 60 ? "var(--bull)" : pct >= 45 ? "var(--accent)" : "var(--bear)";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <div style={{ flex: 1, height: 4, background: "var(--border)", borderRadius: 2, overflow: "hidden" }}>
        <div style={{ width: `${pct}%`, height: "100%", background: color, borderRadius: 2 }} />
      </div>
      <span className="mono" style={{ fontSize: 11, color, width: 36, textAlign: "right" }}>
        {pct.toFixed(0)}%
      </span>
      <span style={{ fontSize: 10, color: "var(--text-muted)", width: 28 }}>n={n}</span>
    </div>
  );
}

const tooltipStyle = {
  background: "var(--bg-card)",
  border: "1px solid var(--border)",
  borderRadius: 6,
  fontFamily: "var(--font-mono)",
  fontSize: 11,
};

const axisStyle = {
  fontSize: 10,
  fill: "var(--text-muted)",
  fontFamily: "var(--font-mono)",
};

export function GroundTruth({ evalSummary }: Props) {
  const pending = evalSummary == null;
  const hasResults = evalSummary != null && evalSummary.evaluated > 0;

  const dayData = evalSummary?.by_day.map(d => ({
    date: d.date.slice(5),   // MM-DD
    accuracy: d.accuracy_pct,
    evaluated: d.evaluated,
    correct: d.correct,
  })) ?? [];

  return (
    <section className="card">
      <div className="section-header">
        <div className="section-step">04</div>
        <div>
          <div className="section-title">Ground Truth</div>
          <div className="section-desc">
            Each signal's direction (bullish/bearish/neutral) is locked at T0 — the moment the
            news was published. Five calendar days later the eval job fetches the closing price
            and computes <code>return_pct = (price_t5 − price_t0) / price_t0</code>. A signal
            is <strong>correct</strong> if the direction matches the sign of the return (neutral
            requires |return| &lt; 1%). The T+5 price is never fetched early — look-ahead bias
            is architecturally impossible.
          </div>
        </div>
      </div>

      {pending && (
        <div className="eval-pending">
          <div className="eval-pending-icon">◌</div>
          <div className="eval-pending-title">No eval data yet</div>
          <div className="eval-pending-desc">
            Signals need 5 calendar days before T+5 price can be fetched. Eval job runs every 6h.
          </div>
        </div>
      )}

      {!pending && !hasResults && (
        <div className="eval-pending">
          <div className="eval-pending-icon">◌</div>
          <div className="eval-pending-title">Eval data loading</div>
          <div className="eval-pending-desc">
            {evalSummary!.pending} signal{evalSummary!.pending !== 1 ? "s" : ""} pending T+5 resolution.
          </div>
        </div>
      )}

      {hasResults && evalSummary && (
        <div>
          {/* Hero metrics */}
          <div className="stat-row">
            <div className="stat-item">
              <div
                className={`stat-val ${
                  (evalSummary.accuracy_pct ?? 0) >= 55 ? "bull"
                  : (evalSummary.accuracy_pct ?? 0) >= 45 ? "accent"
                  : "bear"
                }`}
              >
                {evalSummary.accuracy_pct != null ? `${evalSummary.accuracy_pct.toFixed(1)}%` : "—"}
              </div>
              <div className="stat-lbl">Overall accuracy</div>
              <div style={{ fontSize: 10, color: "var(--text-muted)", marginTop: 2 }}>
                random baseline ~50%
              </div>
            </div>
            <div className="stat-item">
              <div className="stat-val">{evalSummary.evaluated.toLocaleString()}</div>
              <div className="stat-lbl">Evaluated</div>
              <div style={{ fontSize: 10, color: "var(--text-muted)", marginTop: 2 }}>
                T+5 window closed
              </div>
            </div>
            <div className="stat-item">
              <div className="stat-val muted">{evalSummary.pending.toLocaleString()}</div>
              <div className="stat-lbl">Pending</div>
              <div style={{ fontSize: 10, color: "var(--text-muted)", marginTop: 2 }}>
                T+5 not yet elapsed
              </div>
            </div>
            <div className="stat-item">
              <div className="stat-val">
                {evalSummary.avg_return_pct != null
                  ? `${evalSummary.avg_return_pct > 0 ? "+" : ""}${evalSummary.avg_return_pct.toFixed(2)}%`
                  : "—"}
              </div>
              <div className="stat-lbl">Avg T+5 return</div>
              <div style={{ fontSize: 10, color: "var(--text-muted)", marginTop: 2 }}>
                {evalSummary.avg_abnormal_return_pct != null
                  ? `abnormal: ${evalSummary.avg_abnormal_return_pct > 0 ? "+" : ""}${evalSummary.avg_abnormal_return_pct.toFixed(2)}%`
                  : "abnormal: —"}
              </div>
            </div>
          </div>

          {/* Daily accuracy wave */}
          {dayData.length > 0 && (
            <div style={{ marginBottom: 20 }}>
              <div className="sub-label">Accuracy by eval day</div>
              <ResponsiveContainer width="100%" height={140}>
                <BarChart data={dayData} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
                  <XAxis dataKey="date" tick={axisStyle} tickLine={false} axisLine={false} />
                  <YAxis
                    domain={[0, 100]}
                    tick={axisStyle}
                    tickLine={false}
                    axisLine={false}
                    tickFormatter={v => `${v}%`}
                  />
                  <ReferenceLine y={50} stroke="var(--text-muted)" strokeDasharray="4 4" />
                  <Tooltip
                    contentStyle={tooltipStyle}
                    formatter={(v, _name, props) => [
                      v != null ? `${Number(v).toFixed(1)}%` : "—",
                      `accuracy — ${props.payload?.correct ?? "?"}/${props.payload?.evaluated ?? "?"} correct`,
                    ]}
                  />
                  <Bar dataKey="accuracy" radius={[3, 3, 0, 0]}>
                    {dayData.map((d, i) => (
                      <Cell
                        key={i}
                        fill={
                          d.accuracy == null ? "var(--border)"
                          : d.accuracy >= 55 ? "var(--bull)"
                          : d.accuracy >= 45 ? "var(--accent)"
                          : "var(--bear)"
                        }
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
              <div style={{ fontSize: 10, color: "var(--text-muted)", marginTop: 2 }}>
                Each bar = signals whose T+5 window closed on that date. New bars appear daily as
                the eval wave rolls forward (Sep 8 → Sep 18).
              </div>
            </div>
          )}

          {/* Direction + event type breakdowns */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
            <div>
              <div className="sub-label">By direction</div>
              <div style={{ fontSize: 10, color: "var(--text-muted)", marginBottom: 8 }}>
                Bullish = predicted price rise. Bearish = predicted decline. Neutral = &lt;1% move expected.
              </div>
              {evalSummary.by_direction.map(row => (
                <div key={row.direction} style={{ padding: "8px 0", borderBottom: "1px solid var(--border)" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                    <span className={`dir-chip ${row.direction}`}>{row.direction.slice(0, 4)}</span>
                    <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
                      {row.correct}/{row.total} correct
                    </span>
                  </div>
                  <AccBar pct={row.accuracy_pct} n={row.total} />
                </div>
              ))}
            </div>

            <div>
              <div className="sub-label">By event type</div>
              <div style={{ fontSize: 10, color: "var(--text-muted)", marginBottom: 8 }}>
                Earnings signals often invert (sell the news). Macro = market-wide catalysts.
              </div>
              {evalSummary.by_event_type.map(row => (
                <div key={row.event_type} style={{ padding: "8px 0", borderBottom: "1px solid var(--border)" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                    <span style={{ fontSize: 12, color: "var(--text-dim)" }}>{row.event_type}</span>
                    <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
                      {row.correct}/{row.total}
                    </span>
                  </div>
                  <AccBar pct={row.accuracy_pct} n={row.total} />
                </div>
              ))}
            </div>
          </div>

          <div style={{ marginTop: 16, fontSize: 11, color: "var(--text-muted)", paddingTop: 12, borderTop: "1px solid var(--border)" }}>
            <strong style={{ color: "var(--text-dim)" }}>No look-ahead bias:</strong> signal
            direction is written at T0 and never modified. Prices are fetched only after T+5 has
            elapsed (with a 17h buffer for late market data). The eval job runs every 6h.
            As of {new Date(evalSummary.as_of).toLocaleDateString()}.
          </div>
        </div>
      )}
    </section>
  );
}
