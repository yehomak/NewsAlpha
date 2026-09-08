import { useEffect, useState } from "react";
import {
  fetchPipeline,
  fetchEvents,
  fetchCosts,
  fetchTickers,
  fetchEvalSummary,
  fetchSignals,
} from "./api";
import type {
  PipelineStats,
  EventStats,
  CostStats,
  TickerStats,
  EvalSummary,
  Signal,
} from "./api";
import { HeroMetrics } from "./sections/HeroMetrics";
import { SignalFeed } from "./sections/SignalFeed";
import { TickerGrid } from "./sections/TickerGrid";
import { EvalBreakdown } from "./sections/EvalBreakdown";
import { EventIntelligence } from "./sections/EventIntelligence";
import { CostPanel } from "./sections/CostPanel";
import { ProcessTimeline } from "./sections/ProcessTimeline";

type Theme = "dark" | "light";

function relativeTime(iso: string | null): string {
  if (!iso) return "—";
  const diff = Date.now() - new Date(iso).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return "just now";
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

export default function App() {
  const [theme, setTheme] = useState<Theme>(() =>
    window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"
  );

  const [pipeline, setPipeline] = useState<PipelineStats | null>(null);
  const [events, setEvents] = useState<EventStats | null>(null);
  const [costs, setCosts] = useState<CostStats | null>(null);
  const [tickers, setTickers] = useState<TickerStats[] | null>(null);
  const [evalSummary, setEvalSummary] = useState<EvalSummary | null>(null);
  const [signals, setSignals] = useState<Signal[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  useEffect(() => {
    Promise.all([
      fetchPipeline(),
      fetchEvents(),
      fetchCosts(30),
      fetchTickers(),
      fetchEvalSummary(),
      fetchSignals(50),
    ])
      .then(([p, e, c, t, ev, s]) => {
        setPipeline(p);
        setEvents(e);
        setCosts(c);
        setTickers(t);
        setEvalSummary(ev);
        setSignals(s);
      })
      .catch((err: Error) => setError(err.message));
  }, []);

  return (
    <div className="app">
      <header className="header">
        <span className="header-brand">butterfly-effect</span>
        <div className="header-status">
          <span className="status-dot" />
          ingest {relativeTime(pipeline?.last_ingest_at ?? null)}
          &nbsp;·&nbsp;
          pipeline {relativeTime(pipeline?.last_pipeline_at ?? null)}
        </div>
        <div className="header-spacer" />
        <button
          className="theme-btn"
          onClick={() => setTheme(t => (t === "dark" ? "light" : "dark"))}
        >
          {theme === "dark" ? "light" : "dark"}
        </button>
      </header>

      <main className="main">
        {error && <div className="error">API error: {error}</div>}

        <HeroMetrics pipeline={pipeline} costs={costs} evalSummary={evalSummary} />

        <div className="two-col">
          <SignalFeed signals={signals} />
          <TickerGrid tickers={tickers} />
        </div>

        <div className="two-col">
          <EvalBreakdown evalSummary={evalSummary} />
          <EventIntelligence events={events} />
        </div>

        <div className="two-col">
          <CostPanel costs={costs} />
          <ProcessTimeline pipeline={pipeline} events={events} costs={costs} />
        </div>
      </main>
    </div>
  );
}
