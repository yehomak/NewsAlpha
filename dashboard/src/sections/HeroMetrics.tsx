import type { PipelineStats, CostStats, EvalSummary, EventStats } from "../api";

interface Props {
  pipeline: PipelineStats | null;
  costs: CostStats | null;
  evalSummary: EvalSummary | null;
  events: EventStats | null;
}

export function HeroMetrics({ pipeline, costs, evalSummary, events }: Props) {
  const accuracy = evalSummary?.accuracy_pct;
  const evaluated = evalSummary?.evaluated ?? 0;

  const acceptRate =
    costs != null && events != null && events.processed > 0
      ? Math.round((costs.signal_count / events.processed) * 100)
      : null;

  return (
    <div className="hero-grid">
      <div className="metric-card">
        <div className="metric-label">Directional Accuracy</div>
        <div className={`metric-value ${accuracy != null && accuracy >= 50 ? "bull" : ""}`}>
          {accuracy != null ? `${accuracy}%` : "—"}
        </div>
        <div className="metric-sub">
          {evaluated > 0
            ? `${evaluated} signals evaluated (T+5)`
            : "awaiting T+5 data · ~Sep 13"}
        </div>
      </div>

      <div className="metric-card">
        <div className="metric-label">Signals Generated</div>
        <div className="metric-value">{costs?.signal_count ?? "—"}</div>
        <div className="metric-sub">
          {pipeline?.signals_today ?? 0} today
          {acceptRate != null && ` · ${acceptRate}% accept rate`}
        </div>
      </div>

      <div className="metric-card">
        <div className="metric-label">Pipeline Cost</div>
        <div className="metric-value accent">
          ${costs != null ? costs.total_cost_usd.toFixed(4) : "—"}
        </div>
        <div className="metric-sub">
          {costs?.avg_cost_per_signal != null
            ? `$${costs.avg_cost_per_signal.toFixed(4)} / signal · pipeline-tracked only`
            : "pipeline-tracked only"}
        </div>
      </div>

      <div className="metric-card">
        <div className="metric-label">Events Ingested</div>
        <div className="metric-value">{events?.total ?? "—"}</div>
        <div className="metric-sub">
          {events != null
            ? `${events.processed} processed · ${events.dedup_skipped} deduped · ${pipeline?.events_today ?? 0} today`
            : "—"}
        </div>
      </div>

      <div className="metric-card">
        <div className="metric-label">Avg Return T+5</div>
        <div className={`metric-value ${(evalSummary?.avg_return_pct ?? 0) >= 0 ? "bull" : ""}`}>
          {evalSummary?.avg_return_pct != null
            ? `${evalSummary.avg_return_pct > 0 ? "+" : ""}${evalSummary.avg_return_pct.toFixed(2)}%`
            : "—"}
        </div>
        <div className="metric-sub">avg return across evaluated signals</div>
      </div>

      <div className="metric-card">
        <div className="metric-label">Pending Eval</div>
        <div className="metric-value">{evalSummary?.pending ?? "—"}</div>
        <div className="metric-sub">
          {evalSummary != null && evalSummary.pending > 0
            ? "signals awaiting T+5 window"
            : evaluated > 0
              ? "all signals evaluated"
              : "no signals yet"}
        </div>
      </div>
    </div>
  );
}
