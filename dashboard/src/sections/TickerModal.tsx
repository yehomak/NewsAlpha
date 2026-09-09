import { useEffect, useRef, useState } from "react";
import { fetchSignalsForTicker } from "../api";
import type { Signal, TickerStats } from "../api";

interface Props {
  ticker: TickerStats;
  onClose: () => void;
}

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return "just now";
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

export function TickerModal({ ticker: t, onClose }: Props) {
  const [signals, setSignals] = useState<Signal[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const backdropRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchSignalsForTicker(t.ticker)
      .then(setSignals)
      .catch((err: Error) => setError(err.message));
  }, [t.ticker]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  const bullish = signals?.filter(s => s.direction === "bullish").length ?? 0;
  const bearish = signals?.filter(s => s.direction === "bearish").length ?? 0;
  const neutral = signals?.filter(s => s.direction === "neutral").length ?? 0;

  return (
    <div
      className="modal-backdrop"
      ref={backdropRef}
      onClick={e => { if (e.target === backdropRef.current) onClose(); }}
    >
      <div className="modal">
        <div className="modal-header">
          <div className="modal-title-row">
            <span className="modal-ticker">{t.ticker}</span>
            <span className={`dir-chip ${t.last_direction}`}>{t.last_direction}</span>
            {t.accuracy_pct != null && (
              <span className={`modal-accuracy ${t.accuracy_pct >= 55 ? "good" : t.accuracy_pct < 45 ? "bad" : ""}`}>
                {t.accuracy_pct}% acc
              </span>
            )}
          </div>
          <div className="modal-meta">
            {t.signal_count} signals · avg conf {Math.round(t.avg_confidence * 100)}%
            {signals && ` · ${bullish}↑ ${bearish}↓ ${neutral}–`}
            {t.evaluated_count > 0 && ` · ${t.correct_count}/${t.evaluated_count} correct`}
          </div>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        <div className="modal-body">
          {error && <div className="error">{error}</div>}
          {!signals && !error && <div className="loading">loading signals…</div>}
          {signals && signals.map(s => (
            <div className="modal-signal" key={s.id}>
              <div className="modal-signal-header">
                <span className={`dir-chip ${s.direction}`}>{s.direction}</span>
                <div className="conf-bar-wrap" style={{ width: 80 }}>
                  <div className="conf-bar-bg">
                    <div className="conf-bar-fill" style={{ width: `${Math.round(s.confidence * 100)}%` }} />
                  </div>
                  <span className="conf-val">{Math.round(s.confidence * 100)}</span>
                </div>
                <span className="mono" style={{ fontSize: 11, color: "var(--text-muted)" }}>
                  {s.event_type}
                </span>
                <span className="mono" style={{ fontSize: 11, color: "var(--text-muted)", marginLeft: "auto" }}>
                  {timeAgo(s.created_at)}
                </span>
                {s.correct !== null && (
                  <span className={`correct-badge ${s.correct ? "yes" : "no"}`}>
                    {s.correct ? "✓" : "✗"}
                    {s.return_pct != null && ` ${s.return_pct > 0 ? "+" : ""}${s.return_pct.toFixed(1)}%`}
                  </span>
                )}
                {s.correct === null && (
                  <span className="correct-badge pending">pending</span>
                )}
              </div>
              <div className="modal-reasoning">{s.reasoning}</div>
              <div className="modal-signal-footer mono">
                #{s.id} · ${s.cost_usd.toFixed(4)}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
