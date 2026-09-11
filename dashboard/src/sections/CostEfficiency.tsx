import type { CostStats } from "../api";

interface Props {
  costs: CostStats | null;
}

export function CostEfficiency({ costs }: Props) {
  if (!costs) return <div className="loading">loading cost data…</div>;

  const last14 = costs.by_day.slice(-14);
  const maxCost = Math.max(...last14.map(d => d.cost_usd), 0.001);

  const totalSignals = costs.signal_count;
  const totalCost = costs.total_cost_usd;

  // Budget context: $0.001/article target
  const costPerSignalUsd = costs.avg_cost_per_signal ?? 0;
  const budgetVsTarget = costPerSignalUsd > 0
    ? (costPerSignalUsd / 0.001).toFixed(1)
    : "—";

  // Trend: last 3 days avg vs days 4-7 avg
  const recent3 = last14.slice(-3).map(d => d.cost_usd);
  const prior4 = last14.slice(-7, -3).map(d => d.cost_usd);
  const avgRecent = recent3.length > 0 ? recent3.reduce((a, b) => a + b, 0) / recent3.length : 0;
  const avgPrior = prior4.length > 0 ? prior4.reduce((a, b) => a + b, 0) / prior4.length : null;
  const trendPct = avgPrior != null && avgPrior > 0
    ? ((avgRecent - avgPrior) / avgPrior * 100)
    : null;

  return (
    <section className="card">
      <div className="section-header">
        <div className="section-step">05</div>
        <div>
          <div className="section-title">Cost &amp; Efficiency</div>
          <div className="section-desc">
            All LLM spend via Claude Haiku (<code>claude-haiku-4-5-20251001</code>).
            Daily cost tracked in <code>extraction_attempts</code> from Sep 11 onward;
            prior days use <code>signals.cost_usd</code> plus a $1.776 historical offset
            derived from Anthropic's API export.
          </div>
        </div>
      </div>

      <div className="stat-row">
        <div className="stat-item">
          <div className="stat-val accent">${totalCost.toFixed(4)}</div>
          <div className="stat-lbl">Total tracked spend</div>
        </div>
        <div className="stat-item">
          <div className="stat-val">${costPerSignalUsd.toFixed(4)}</div>
          <div className="stat-lbl">Avg cost / signal</div>
        </div>
        <div className="stat-item">
          <div className="stat-val">{totalSignals.toLocaleString()}</div>
          <div className="stat-lbl">Total signals stored</div>
        </div>
        <div className="stat-item">
          <div
            className={`stat-val ${trendPct == null ? "" : trendPct < 0 ? "bull" : "bear"}`}
          >
            {trendPct != null ? `${trendPct > 0 ? "+" : ""}${trendPct.toFixed(0)}%` : "—"}
          </div>
          <div className="stat-lbl">3d vs prior 4d trend</div>
        </div>
      </div>

      {/* Daily bar chart */}
      <div className="sub-label" style={{ marginBottom: 8 }}>Daily spend (last {last14.length} days)</div>
      <div className="cost-bars">
        {last14.map(d => {
          const heightPct = d.cost_usd / maxCost * 100;
          const label = d.date.slice(5); // MM-DD
          return (
            <div key={d.date} className="cost-bar-col" title={`${d.date}: $${d.cost_usd.toFixed(4)} · ${d.signal_count} signals`}>
              {d.cost_usd > 0 && (
                <div
                  className="cost-bar-val"
                  style={{ top: `-${Math.min(14, 14)}px` }}
                >
                  ${d.cost_usd < 0.01 ? d.cost_usd.toFixed(4) : d.cost_usd.toFixed(3)}
                </div>
              )}
              <div
                className="cost-bar"
                style={{ height: `${heightPct}%` }}
              />
              <div className="cost-bar-date">{label}</div>
            </div>
          );
        })}
      </div>

      <div className="callout-row" style={{ marginTop: 28 }}>
        <div className="callout">
          <div className="callout-val">{budgetVsTarget}×</div>
          <div className="callout-lbl">Cost vs $0.001/article target</div>
          <div className="callout-note">
            {costPerSignalUsd < 0.001
              ? "Under target — prompt caching effective"
              : costPerSignalUsd < 0.005
              ? "Slightly over target — acceptable for Haiku"
              : "Above target — check caching hit rate"}
          </div>
        </div>
        <div className="callout">
          <div className="callout-val">
            {avgRecent > 0 ? `$${avgRecent.toFixed(3)}/day` : "—"}
          </div>
          <div className="callout-lbl">Recent daily avg (3d)</div>
          <div className="callout-note">
            Sep 8 spike was backlog flush (~1M tokens). Baseline ~$0.58/day for fresh news only.
          </div>
        </div>
        <div className="callout">
          <div className="callout-val">~10%</div>
          <div className="callout-lbl">Cache read price (vs full input)</div>
          <div className="callout-note">
            System prompt cached via <code>cache_control: ephemeral</code>.
            Savings visible in Langfuse token breakdown.
          </div>
        </div>
      </div>

      <div
        style={{
          marginTop: 16,
          paddingTop: 12,
          borderTop: "1px solid var(--border)",
          fontSize: 11,
          color: "var(--text-muted)",
          lineHeight: 1.6,
        }}
      >
        <strong style={{ color: "var(--text-dim)" }}>Data source note:</strong> Pre-Sep 11 days use
        <code> signals.cost_usd</code> only (rejected/truncated calls not tracked), plus a $1.776
        offset for untracked historical spend. Sep 11+ uses <code>extraction_attempts.cost_usd</code>
        which captures 100% of LLM spend regardless of outcome.
      </div>
    </section>
  );
}
