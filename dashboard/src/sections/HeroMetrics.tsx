import type { PipelineStats, CostStats, EvalSummary } from "../api";

interface Props {
  pipeline: PipelineStats | null;
  costs: CostStats | null;
  evalSummary: EvalSummary | null;
}

export function HeroMetrics({ pipeline, costs, evalSummary }: Props) {
  const accuracy = evalSummary?.accuracy_pct;
  const evaluated = evalSummary?.evaluated ?? 0;

  return (
    <div className="hero-grid">
      <div className="metric-card">
        <div className="metric-label">Directional Accuracy</div>
        <div className={`metric-value ${accuracy != null && accuracy >= 50 ? "bull" : ""}`}>
          {accuracy != null ? `${accuracy}%` : "—"}
        </div>
        <div className="metric-sub">
          {evaluated > 0 ? `over ${evaluated} evaluated` : "awaiting T+5 data"}
        </div>
      </div>

      <div className="metric-card">
        <div className="metric-label">Signals Generated</div>
        <div className="metric-value">{costs?.signal_count ?? "—"}</div>
        <div className="metric-sub">{pipeline?.signals_today ?? 0} today</div>
      </div>

      <div className="metric-card">
        <div className="metric-label">Total Cost</div>
        <div className="metric-value accent">
          ${costs != null ? costs.total_cost_usd.toFixed(4) : "—"}
        </div>
        <div className="metric-sub">
          {costs?.avg_cost_per_signal != null
            ? `$${costs.avg_cost_per_signal.toFixed(4)} / signal`
            : "—"}
        </div>
      </div>

      <div className="metric-card">
        <div className="metric-label">Events Ingested</div>
        <div className="metric-value">{pipeline?.events_today ?? "—"}</div>
        <div className="metric-sub">today · {pipeline?.events_without_signal ?? 0} no signal</div>
      </div>

      <div className="metric-card">
        <div className="metric-label">Avg Return</div>
        <div className={`metric-value ${(evalSummary?.avg_return_pct ?? 0) >= 0 ? "bull" : ""}`}>
          {evalSummary?.avg_return_pct != null
            ? `${evalSummary.avg_return_pct > 0 ? "+" : ""}${evalSummary.avg_return_pct.toFixed(2)}%`
            : "—"}
        </div>
        <div className="metric-sub">T+5 avg across evaluated</div>
      </div>

      <div className="metric-card">
        <div className="metric-label">Pending Eval</div>
        <div className="metric-value">{evalSummary?.pending ?? "—"}</div>
        <div className="metric-sub">signals awaiting T+5</div>
      </div>
    </div>
  );
}
