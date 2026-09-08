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
  const rows: { label: string; value: string }[] = [
    { label: "Last ingest", value: fmt(pipeline?.last_ingest_at ?? null) },
    { label: "Last pipeline run", value: fmt(pipeline?.last_pipeline_at ?? null) },
    { label: "Last eval run", value: fmt(pipeline?.last_eval_at ?? null) },
    { label: "Signals today", value: String(pipeline?.signals_today ?? "—") },
    { label: "Events today", value: String(pipeline?.events_today ?? "—") },
    {
      label: "Events → no signal",
      value: pipeline != null ? String(pipeline.events_without_signal) : "—",
    },
    {
      label: "Signal accept rate",
      value:
        pipeline != null && pipeline.events_today > 0
          ? `${Math.round((pipeline.signals_today / pipeline.events_today) * 100)}%`
          : "—",
    },
    { label: "Sources active", value: String(events?.by_source.length ?? "—") },
    { label: "Dedup skipped", value: String(events?.dedup_skipped ?? "—") },
    { label: "Pipeline total cost", value: costs != null ? `$${costs.total_cost_usd.toFixed(4)}` : "—" },
  ];

  return (
    <div className="card">
      <div className="card-title">Process Insights</div>
      {rows.map(r => (
        <div className="timeline-row" key={r.label}>
          <span className="timeline-label">{r.label}</span>
          <span className={`timeline-value mono ${r.value === "—" ? "muted" : ""}`}>
            {r.value}
          </span>
        </div>
      ))}
    </div>
  );
}
