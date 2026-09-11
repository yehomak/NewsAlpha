import type { EventStats, PipelineStats, CostStats, Signal } from "../api";

interface Props {
  events: EventStats | null;
  pipeline: PipelineStats | null;
  costs: CostStats | null;
  signals: Signal[] | null;
}

interface FunnelStep {
  label: string;
  sublabel: string;
  count: number;
  dropLabel?: string;
  dropCount?: number;
  barColor?: string;
}

export function ExtractionFunnel({ events, pipeline, costs, signals }: Props) {
  if (!events || !pipeline) return <div className="loading">loading extraction data…</div>;

  const totalEvents = events.total;
  const uniqueEvents = events.total - events.dedup_skipped;
  const netProcessed = events.processed - events.dedup_skipped;
  const signalCount = costs?.signal_count ?? (signals?.length ?? 0);
  const eventsWithoutSignal = pipeline.events_without_signal;

  const acceptanceRate = netProcessed > 0
    ? (signalCount / netProcessed * 100).toFixed(1)
    : "—";

  // Cost per LLM attempt (total tracked cost over net processed — rough but meaningful)
  const totalCost = costs?.total_cost_usd ?? 0;
  const costPerAttempt = netProcessed > 0
    ? `$${(totalCost / netProcessed).toFixed(4)}`
    : "—";
  const costPerSignal = costs?.avg_cost_per_signal != null
    ? `$${costs.avg_cost_per_signal.toFixed(4)}`
    : "—";

  const steps: FunnelStep[] = [
    {
      label: "Events ingested",
      sublabel: "All news fetched from sources (includes duplicates)",
      count: totalEvents,
    },
    {
      label: "Unique events",
      sublabel: "After URL-hash + semantic deduplication",
      count: uniqueEvents,
      dropLabel: "dedup filtered",
      dropCount: events.dedup_skipped,
      barColor: "var(--accent)",
    },
    {
      label: "Pipeline-processed",
      sublabel: "Marked processed; universe mention check applied pre-LLM",
      count: netProcessed,
      dropLabel: "not yet processed",
      dropCount: events.unprocessed,
      barColor: "var(--accent)",
    },
    {
      label: "Signal stored",
      sublabel: "LLM extraction succeeded — ticker resolved, direction, confidence, reasoning",
      count: signalCount,
      dropLabel: "no signal produced",
      dropCount: eventsWithoutSignal,
      barColor: "var(--bull)",
    },
  ];

  const maxCount = totalEvents || 1;

  return (
    <section className="card">
      <div className="section-header">
        <div className="section-step">02</div>
        <div>
          <div className="section-title">Extraction Funnel</div>
          <div className="section-desc">
            Each unique event runs through a LangGraph chain: extract → resolve → reason.
            The resolver validates the LLM-proposed ticker against a curated 100-ticker universe;
            misses are rejected without writing a signal. All call costs are recorded in
            <code>extraction_attempts</code> regardless of outcome.
          </div>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
        <div>
          {steps.map((step, i) => {
            const pct = Math.round(step.count / maxCount * 100);
            const prevCount = i > 0 ? steps[i - 1].count : null;
            const retentionPct = prevCount != null && prevCount > 0
              ? Math.round(step.count / prevCount * 100)
              : null;

            return (
              <div key={step.label} className="funnel-step">
                <div>
                  <div className="funnel-step-num">{step.count.toLocaleString()}</div>
                  {retentionPct !== null && (
                    <div className="funnel-step-pct">{retentionPct}% of prev</div>
                  )}
                </div>
                <div style={{ flex: 1 }}>
                  <div className="funnel-step-label" style={{ fontWeight: 500, color: "var(--text-dim)" }}>
                    {step.label}
                  </div>
                  <div className="funnel-step-label" style={{ marginTop: 2 }}>{step.sublabel}</div>
                  <div className="funnel-step-bar-wrap" style={{ marginTop: 6 }}>
                    <div
                      className="funnel-step-bar"
                      style={{ width: `${pct}%`, background: step.barColor ?? "var(--accent)" }}
                    />
                  </div>
                  {step.dropCount != null && step.dropCount > 0 && (
                    <div className="funnel-step-drop">
                      ↓ {step.dropCount.toLocaleString()} {step.dropLabel}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 12, alignSelf: "start", paddingTop: 4 }}>
          <div className="sub-label">Why events don't produce signals</div>

          <div style={{ fontSize: 12, color: "var(--text-dim)", lineHeight: 1.7 }}>
            <div style={{ marginBottom: 8 }}>
              <span style={{ color: "var(--text)" }}>No universe mention</span> — pre-LLM regex/keyword check finds
              no ticker symbol or company name from the 100-ticker universe.
              These are marked <code>processed=true</code> but no LLM call is made (zero cost).
            </div>
            <div style={{ marginBottom: 8 }}>
              <span style={{ color: "var(--text)" }}>Ticker not in universe</span> — the resolver LLM proposes a
              ticker but it fails universe validation. Call cost recorded, no signal written.
            </div>
            <div>
              <span style={{ color: "var(--text)" }}>Truncated article</span> — reasoning output references
              "truncated" or "cuts off mid-sentence". Signal discarded to avoid low-quality data.
            </div>
          </div>

          <div className="callout-row" style={{ paddingTop: 0, borderTop: "none", flexDirection: "column", gap: 8 }}>
            <div className="callout">
              <div className="callout-val bull">{acceptanceRate}%</div>
              <div className="callout-lbl">Acceptance rate (signals / net-processed)</div>
              <div className="callout-note">{signalCount.toLocaleString()} stored from {netProcessed.toLocaleString()} processed</div>
            </div>
            <div className="callout">
              <div className="callout-val">{costPerAttempt}</div>
              <div className="callout-lbl">Avg cost per processed event</div>
              <div className="callout-note">Includes rejected calls (pre-Sep 11: estimate)</div>
            </div>
            <div className="callout">
              <div className="callout-val">{costPerSignal}</div>
              <div className="callout-lbl">Avg cost per stored signal</div>
              <div className="callout-note">Higher than per-attempt due to rejection overhead</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
