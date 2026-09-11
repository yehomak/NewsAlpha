import type { EventStats, PipelineStats } from "../api";

interface Props {
  events: EventStats | null;
  pipeline: PipelineStats | null;
}

export function IngestionSection({ events, pipeline }: Props) {
  if (!events) return <div className="loading">loading ingestion data…</div>;

  const uniqueEvents = events.total - events.dedup_skipped;
  const netProcessed = events.processed - events.dedup_skipped;
  const processedRate = uniqueEvents > 0 ? Math.round(netProcessed / uniqueEvents * 100) : 0;
  const dedupRate = events.total > 0 ? Math.round(events.dedup_skipped / events.total * 100) : 0;
  const maxSource = Math.max(...events.by_source.map(s => s.count), 1);

  return (
    <section className="card">
      <div className="section-header">
        <div className="section-step">01</div>
        <div>
          <div className="section-title">Ingestion</div>
          <div className="section-desc">
            Raw news gathered from {events.by_source.length} RSS/API source{events.by_source.length !== 1 ? "s" : ""} on a 1-hour scheduler.
            Events are deduplicated by URL hash (exact) and semantic similarity via all-MiniLM-L6-v2 embeddings
            (cosine &gt; 0.95 against the last 24h window). Duplicates are stored with <code>processed=true</code> for
            audit visibility but excluded from the extraction pipeline.
          </div>
        </div>
      </div>

      <div className="stat-row">
        <div className="stat-item">
          <div className="stat-val">{events.total.toLocaleString()}</div>
          <div className="stat-lbl">Total events</div>
        </div>
        <div className="stat-item">
          <div className="stat-val">{(pipeline?.events_today ?? "—").toLocaleString()}</div>
          <div className="stat-lbl">Today</div>
        </div>
        <div className="stat-item">
          <div className="stat-val">{events.by_source.length}</div>
          <div className="stat-lbl">Active sources</div>
        </div>
        <div className="stat-item">
          <div className="stat-val muted">{events.dedup_skipped.toLocaleString()}</div>
          <div className="stat-lbl">Dedup skipped</div>
        </div>
        <div className="stat-item">
          <div className="stat-val">{events.unprocessed.toLocaleString()}</div>
          <div className="stat-lbl">Unprocessed</div>
        </div>
      </div>

      <div className="sub-label" style={{ marginBottom: 12 }}>Events by source</div>
      {events.by_source.map(s => (
        <div key={s.source} className="source-row">
          <div className="source-name">{s.source}</div>
          <div className="source-bar-bg">
            <div
              className="source-bar-fill"
              style={{ width: `${Math.round(s.count / maxSource * 100)}%` }}
            />
          </div>
          <div className="source-count mono">{s.count.toLocaleString()}</div>
          <div className="source-pct">{Math.round(s.count / events.total * 100)}%</div>
        </div>
      ))}

      <div className="callout-row">
        <div className="callout">
          <div className="callout-val">{processedRate}%</div>
          <div className="callout-lbl">Unique events pipeline-processed</div>
          <div className="callout-note">{netProcessed.toLocaleString()} of {uniqueEvents.toLocaleString()} unique</div>
        </div>
        <div className="callout">
          <div className="callout-val">{dedupRate}%</div>
          <div className="callout-lbl">Duplicate rate</div>
          <div className="callout-note">{events.dedup_skipped.toLocaleString()} dupes out of {events.total.toLocaleString()} total</div>
        </div>
        <div className="callout">
          <div className="callout-val">{uniqueEvents.toLocaleString()}</div>
          <div className="callout-lbl">Unique events (post-dedup)</div>
          <div className="callout-note">Eligible for extraction pipeline</div>
        </div>
      </div>
    </section>
  );
}
