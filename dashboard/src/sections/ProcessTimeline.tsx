import type { PipelineStats, EventStats, CostStats } from "../api";

interface Props {
  pipeline: PipelineStats | null;
  events: EventStats | null;
  costs: CostStats | null;
}

function fmt(iso: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  const diff = Date.now() - d.getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return "just now";
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  return `${h}h ${m % 60}m ago`;
}

export function ProcessTimeline({ pipeline, events, costs }: Props) {
  const lifetimeAcceptRate =
    costs != null && events != null && events.processed > 0
      ? `${Math.round((costs.signal_count / events.processed) * 100)}%`
      : "—";

  const rejectedTotal =
    events != null && costs != null
      ? events.processed - costs.signal_count
      : null;

  const rows: { label: string; value: string; dim?: boolean }[] = [
    { label: "Last ingest", value: fmt(pipeline?.last_ingest_at ?? null) },
    { label: "Last pipeline run", value: fmt(pipeline?.last_pipeline_at ?? null) },
    { label: "Last eval run", value: fmt(pipeline?.last_eval_at ?? null) },
    { label: "Signals today", value: String(pipeline?.signals_today ?? "—") },
    { label: "Events today", value: String(pipeline?.events_today ?? "—") },
    {
      label: "Lifetime accept rate",
      value: lifetimeAcceptRate,
    },
    {
      label: "Rejected / truncated",
      value: rejectedTotal != null ? String(rejectedTotal) : "—",
      dim: true,
    },
    {
      label: "Events → no signal (today)",
      value: pipeline != null ? String(pipeline.events_without_signal) : "—",
      dim: true,
    },
    { label: "Active sources", value: String(events?.by_source.length ?? "—") },
    { label: "Dedup skipped (total)", value: String(events?.dedup_skipped ?? "—") },
    {
      label: "Pipeline cost (tracked)",
      value: costs != null ? `$${costs.total_cost_usd.toFixed(4)}` : "—",
    },
    {
      label: "Avg cost / signal",
      value: costs?.avg_cost_per_signal != null
        ? `$${costs.avg_cost_per_signal.toFixed(4)}`
        : "—",
    },
  ];

  return (
    <div className="card">
      <div className="card-title">Process Insights</div>
      {rows.map(r => (
        <div className="timeline-row" key={r.label}>
          <span className="timeline-label">{r.label}</span>
          <span className={`timeline-value mono ${!r.value || r.value === "—" ? "muted" : r.dim ? "dim" : ""}`}>
            {r.value}
          </span>
        </div>
      ))}
    </div>
  );
}
