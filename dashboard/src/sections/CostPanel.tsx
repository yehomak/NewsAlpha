import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { CostStats } from "../api";

interface Props {
  costs: CostStats | null;
}

export function CostPanel({ costs }: Props) {
  if (!costs) return <div className="card"><div className="loading">loading…</div></div>;

  const data = costs.by_day.map(d => ({
    date: d.date.slice(5),    // MM-DD
    cost: +(d.cost_usd.toFixed(4)),
    signals: d.signal_count,
  }));

  return (
    <div className="card">
      <div className="card-title">Cost & Spend</div>

      <div style={{ display: "flex", gap: 24, marginBottom: 20 }}>
        <div>
          <div className="metric-label">Total tracked</div>
          <div className="metric-value accent" style={{ fontSize: 20 }}>
            ${costs.total_cost_usd.toFixed(4)}
          </div>
        </div>
        <div>
          <div className="metric-label">Avg / signal</div>
          <div className="metric-value" style={{ fontSize: 20 }}>
            ${costs.avg_cost_per_signal?.toFixed(4) ?? "—"}
          </div>
        </div>
        <div>
          <div className="metric-label">Signals total</div>
          <div className="metric-value" style={{ fontSize: 20 }}>
            {costs.signal_count}
          </div>
        </div>
      </div>

      {data.length > 0 ? (
        <ResponsiveContainer width="100%" height={120}>
          <AreaChart data={data} margin={{ top: 4, right: 0, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="costGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
              </linearGradient>
            </defs>
            <XAxis
              dataKey="date"
              tick={{ fontSize: 10, fill: "var(--text-muted)", fontFamily: "var(--font-mono)" }}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              tick={{ fontSize: 10, fill: "var(--text-muted)", fontFamily: "var(--font-mono)" }}
              tickLine={false}
              axisLine={false}
              tickFormatter={v => `$${v}`}
            />
            <Tooltip
              formatter={(v: number) => [`$${v.toFixed(4)}`, "cost"]}
              contentStyle={{
                background: "var(--bg-card)",
                border: "1px solid var(--border)",
                borderRadius: 6,
                fontFamily: "var(--font-mono)",
                fontSize: 11,
              }}
            />
            <Area
              type="monotone"
              dataKey="cost"
              stroke="#f59e0b"
              strokeWidth={1.5}
              fill="url(#costGrad)"
              dot={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      ) : (
        <div className="loading" style={{ padding: "20px 0" }}>No daily data yet</div>
      )}

      <div style={{ marginTop: 12, fontSize: 11, color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
        Tracked via pipeline cost_usd — excludes pre-tracking runs
      </div>
    </div>
  );
}
