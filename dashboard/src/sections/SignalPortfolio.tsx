import { useState } from "react";
import type { Signal, TickerStats } from "../api";
import { TickerModal } from "./TickerModal";

interface Props {
  signals: Signal[] | null;
  tickers: TickerStats[] | null;
}

const EVENT_TYPE_LABELS: Record<string, string> = {
  earnings: "Earnings",
  product_launch: "Product",
  legal: "Legal",
  partnership: "Partnership",
  macro: "Macro",
  analyst: "Analyst",
  acquisition: "M&A",
  other: "Other",
};

function ConfBar({ value }: { value: number }) {
  return (
    <div className="conf-bar-wrap">
      <div className="conf-bar-bg">
        <div className="conf-bar-fill" style={{ width: `${Math.round(value * 100)}%` }} />
      </div>
      <div className="conf-val">{Math.round(value * 100)}%</div>
    </div>
  );
}

export function SignalPortfolio({ signals, tickers }: Props) {
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [selectedTicker, setSelectedTicker] = useState<TickerStats | null>(null);

  if (!signals || !tickers) return <div className="loading">loading signal data…</div>;

  // Direction breakdown
  const dirCounts = { bullish: 0, bearish: 0, neutral: 0 };
  for (const s of signals) {
    const d = s.direction as keyof typeof dirCounts;
    if (d in dirCounts) dirCounts[d]++;
  }
  const total = signals.length || 1;

  // Event type breakdown
  const etCounts: Record<string, number> = {};
  for (const s of signals) {
    etCounts[s.event_type] = (etCounts[s.event_type] ?? 0) + 1;
  }
  const etEntries = Object.entries(etCounts).sort((a, b) => b[1] - a[1]);
  const maxEt = etEntries[0]?.[1] ?? 1;

  // Top tickers
  const topTickers = [...tickers].sort((a, b) => b.signal_count - a.signal_count).slice(0, 8);
  const maxTicker = topTickers[0]?.signal_count ?? 1;

  // Last 10 signals
  const recentSignals = signals.slice(0, 10);

  const avgConfidence = signals.length > 0
    ? signals.reduce((sum, s) => sum + s.confidence, 0) / signals.length
    : 0;

  const bullPct = Math.round(dirCounts.bullish / total * 100);
  const bearPct = Math.round(dirCounts.bearish / total * 100);

  return (
    <section className="card">
      <div className="section-header">
        <div className="section-step">03</div>
        <div>
          <div className="section-title">Signal Portfolio</div>
          <div className="section-desc">
            Distribution of {signals.length.toLocaleString()} extracted signals by direction, event type, and ticker.
            Confidence reflects the LLM's self-reported certainty (0–100%). Bullish/bearish skew indicates
            whether the news corpus has a systematic positive or negative bias this period.
          </div>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 20 }}>

        {/* Direction breakdown */}
        <div>
          <div className="sub-label">Direction split</div>
          {(["bullish", "bearish", "neutral"] as const).map(d => {
            const count = dirCounts[d];
            const pct = Math.round(count / total * 100);
            return (
              <div key={d} className="dir-bar-row">
                <div className="dir-bar-label">
                  <span className={`dir-chip ${d}`}>{d.slice(0, 4)}</span>
                </div>
                <div className="dir-bar-bg">
                  <div className={`dir-bar-fill ${d}`} style={{ width: `${pct}%` }} />
                </div>
                <div className="dir-bar-pct">{pct}%</div>
                <div className="dir-bar-count">{count.toLocaleString()}</div>
              </div>
            );
          })}
          <div style={{ marginTop: 16, paddingTop: 12, borderTop: "1px solid var(--border)" }}>
            <div className="sub-label">Avg confidence</div>
            <ConfBar value={avgConfidence} />
            <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 6 }}>
              {bullPct > 55
                ? `Bullish-skewed corpus (${bullPct}%). Could reflect survivorship in universe selection or genuine positive news period.`
                : bearPct > 40
                ? `Bearish-skewed corpus (${bearPct}%). Monitor for macro event clustering.`
                : `Balanced direction mix — typical for a diverse news corpus.`}
            </div>
          </div>
        </div>

        {/* Event type breakdown */}
        <div>
          <div className="sub-label">By event type</div>
          {etEntries.slice(0, 7).map(([et, count]) => (
            <div key={et} className="dir-bar-row">
              <div className="dir-bar-label" style={{ width: 90, fontSize: 11 }}>
                {EVENT_TYPE_LABELS[et] ?? et}
              </div>
              <div className="dir-bar-bg">
                <div
                  className="dir-bar-fill neutral"
                  style={{ width: `${Math.round(count / maxEt * 100)}%` }}
                />
              </div>
              <div className="dir-bar-pct">{Math.round(count / total * 100)}%</div>
              <div className="dir-bar-count">{count}</div>
            </div>
          ))}
        </div>

        {/* Top tickers */}
        <div>
          <div className="sub-label">Top tickers by signal count</div>
          {topTickers.map(t => {
            const lastDir = t.last_direction;
            const dirClass = lastDir === "bullish" ? "bull" : lastDir === "bearish" ? "bear" : "";
            return (
              <div
                key={t.ticker}
                className="dir-bar-row"
                style={{ cursor: "pointer" }}
                onClick={() => setSelectedTicker(t)}
              >
                <div
                  className="dir-bar-label ticker-cell"
                  style={{ width: 60, fontSize: 12 }}
                >
                  {t.ticker}
                </div>
                <div className="dir-bar-bg">
                  <div
                    className="dir-bar-fill"
                    style={{
                      width: `${Math.round(t.signal_count / maxTicker * 100)}%`,
                      background: "var(--accent)",
                    }}
                  />
                </div>
                <div className={`dir-bar-count ${dirClass}`}>{t.signal_count}</div>
              </div>
            );
          })}
          <div style={{ marginTop: 8, fontSize: 10, color: "var(--text-muted)" }}>
            Click a ticker to see all its signals
          </div>
        </div>
      </div>

      {/* Recent signals feed */}
      <div style={{ marginTop: 20 }}>
        <div className="sub-label">Last 10 signals</div>
        <div className="tbl-wrap">
          <table>
            <thead>
              <tr>
                <th>Ticker</th>
                <th>Direction</th>
                <th>Confidence</th>
                <th>Type</th>
                <th>Reasoning</th>
                <th>When</th>
              </tr>
            </thead>
            <tbody>
              {recentSignals.map(s => {
                const isExpanded = expandedId === s.id;
                const when = (() => {
                  const d = Date.now() - new Date(s.created_at).getTime();
                  const m = Math.floor(d / 60000);
                  if (m < 60) return `${m}m ago`;
                  const h = Math.floor(m / 60);
                  if (h < 24) return `${h}h ago`;
                  return `${Math.floor(h / 24)}d ago`;
                })();
                return (
                  <>
                    <tr key={s.id}>
                      <td className="ticker-cell">{s.ticker}</td>
                      <td><span className={`dir-chip ${s.direction}`}>{s.direction.slice(0, 4)}</span></td>
                      <td><ConfBar value={s.confidence} /></td>
                      <td className="mono" style={{ fontSize: 11, color: "var(--text-muted)" }}>
                        {EVENT_TYPE_LABELS[s.event_type] ?? s.event_type}
                      </td>
                      <td
                        className="reasoning-cell"
                        onClick={() => setExpandedId(isExpanded ? null : s.id)}
                      >
                        {s.reasoning.slice(0, 80)}…
                      </td>
                      <td className="mono" style={{ fontSize: 11, color: "var(--text-muted)" }}>{when}</td>
                    </tr>
                    {isExpanded && (
                      <tr className="reasoning-expanded" key={`${s.id}-exp`}>
                        <td colSpan={6}>
                          <div className="reasoning-full">{s.reasoning}</div>
                          <div className="reasoning-meta">
                            {s.event_title} · ${parseFloat(s.cost_usd).toFixed(4)} · signal #{s.id}
                          </div>
                        </td>
                      </tr>
                    )}
                  </>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {selectedTicker && (
        <TickerModal ticker={selectedTicker} onClose={() => setSelectedTicker(null)} />
      )}
    </section>
  );
}
