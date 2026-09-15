import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  BarChart,
  Bar,
  Cell,
  ResponsiveContainer,
} from "recharts";
import type { AnalysisData } from "../api";

interface Props {
  analysis: AnalysisData | null;
}

function ICCard({ ic, n }: { ic: number | null; n: number }) {
  const label =
    ic === null ? "—"
    : ic >= 0.1 ? "strong"
    : ic >= 0.05 ? "useful"
    : ic > 0 ? "weak"
    : "negative";
  const color =
    ic === null ? "var(--text-muted)"
    : ic >= 0.05 ? "var(--bull)"
    : ic > 0 ? "var(--accent)"
    : "var(--bear)";

  return (
    <div className="stat-item">
      <div className="stat-val mono" style={{ color }}>
        {ic !== null ? ic.toFixed(4) : "—"}
      </div>
      <div className="stat-lbl">
        IC{" "}
        {ic !== null && (
          <span style={{ color, fontWeight: 600 }}>({label})</span>
        )}
      </div>
      <div style={{ fontSize: 10, color: "var(--text-muted)", marginTop: 2 }}>
        n={n} directional signals
      </div>
    </div>
  );
}

function ProfitFactorCard({ pf }: { pf: number | null }) {
  const color =
    pf === null ? "var(--text-muted)"
    : pf >= 1 ? "var(--bull)"
    : "var(--bear)";
  return (
    <div className="stat-item">
      <div className="stat-val mono" style={{ color }}>
        {pf !== null ? pf.toFixed(2) : "—"}
      </div>
      <div className="stat-lbl">Profit factor</div>
      <div style={{ fontSize: 10, color: "var(--text-muted)", marginTop: 2 }}>
        avg win / avg loss · directional only
      </div>
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

export function SignalQuality({ analysis }: Props) {
  if (!analysis) return <div className="card"><div className="loading">loading…</div></div>;

  const horizonData = analysis.horizon.map(h => ({
    label: `T+${h.offset}`,
    accuracy: h.accuracy_pct,
    n: h.n,
  }));

  const pfData = [
    { label: "Avg win", value: analysis.profit_factor != null && analysis.profit_factor > 0 ? analysis.profit_factor : null },
    { label: "Avg loss", value: -1 },
  ];

  const hasHorizon = horizonData.some(d => d.accuracy !== null);

  return (
    <section className="card">
      <div className="section-header">
        <div className="section-step">05</div>
        <div>
          <div className="section-title">Signal Quality</div>
          <div className="section-desc">
            IC measures directional correlation (neutrals excluded). Profit factor compares average
            winning return to average losing return — above 1.0 means wins outweigh losses.
            Horizon decay shows whether the signal strengthens or fades over the 5-day window.
          </div>
        </div>
      </div>

      <div className="stat-row" style={{ marginBottom: 24 }}>
        <ICCard ic={analysis.ic} n={analysis.ic_n} />
        <ProfitFactorCard pf={analysis.profit_factor} />
        <div className="stat-item">
          <div className="stat-val">{analysis.evaluated}</div>
          <div className="stat-lbl">Evaluated signals</div>
        </div>
      </div>

      {hasHorizon && (
        <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 24 }}>
          <div>
            <div className="sub-label">Accuracy decay T+1 → T+5</div>
            <ResponsiveContainer width="100%" height={180}>
              <LineChart data={horizonData} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
                <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="label" tick={axisStyle} tickLine={false} axisLine={false} />
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
                    `accuracy (n=${props.payload?.n ?? "?"})`,
                  ]}
                />
                <Line
                  type="monotone"
                  dataKey="accuracy"
                  stroke="var(--accent)"
                  strokeWidth={2}
                  dot={{ r: 4, fill: "var(--accent)", strokeWidth: 0 }}
                  connectNulls={false}
                />
              </LineChart>
            </ResponsiveContainer>
            <div style={{ fontSize: 10, color: "var(--text-muted)", marginTop: 4 }}>
              Dashed line = 50% random baseline. Each point shows n signals with a price snapshot at that offset.
            </div>
          </div>

          <div>
            <div className="sub-label">Profit factor breakdown</div>
            {analysis.profit_factor != null ? (
              <ResponsiveContainer width="100%" height={180}>
                <BarChart
                  data={[
                    { label: "Avg win", value: analysis.profit_factor, raw: analysis.profit_factor },
                    { label: "Avg loss", value: 1, raw: -1 },
                  ]}
                  margin={{ top: 8, right: 8, left: -20, bottom: 0 }}
                >
                  <XAxis dataKey="label" tick={axisStyle} tickLine={false} axisLine={false} />
                  <YAxis tick={axisStyle} tickLine={false} axisLine={false} />
                  <Tooltip
                    contentStyle={tooltipStyle}
                    formatter={(v, _name, props) => {
                      const raw = props.payload?.raw as number | undefined;
                      return [raw != null ? raw.toFixed(3) : String(v), "factor"];
                    }}
                  />
                  <Bar dataKey="value" radius={[3, 3, 0, 0]}>
                    <Cell fill="var(--bull)" />
                    <Cell fill="var(--bear)" />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ fontSize: 12, color: "var(--text-muted)", paddingTop: 12 }}>
                Insufficient data — need at least one win and one loss.
              </div>
            )}
          </div>
        </div>
      )}

      {!hasHorizon && (
        <div className="eval-pending">
          <div className="eval-pending-icon">◌</div>
          <div className="eval-pending-title">No horizon data yet</div>
          <div className="eval-pending-desc">
            Price snapshots at intermediate offsets will populate as eval runs accumulate.
          </div>
        </div>
      )}
    </section>
  );
}
