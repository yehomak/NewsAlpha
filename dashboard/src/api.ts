const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`${res.status} ${path}`);
  return res.json() as Promise<T>;
}

// --- types ---

export interface PipelineStats {
  last_ingest_at: string | null;
  last_pipeline_at: string | null;
  last_eval_at: string | null;
  signals_today: number;
  events_today: number;
  events_without_signal: number;
}

export interface SourceBreakdown {
  source: string;
  count: number;
}

export interface EventStats {
  total: number;
  processed: number;
  unprocessed: number;
  dedup_skipped: number;
  by_source: SourceBreakdown[];
}

export interface CostDay {
  date: string;
  cost_usd: number;
  signal_count: number;
}

export interface CostStats {
  total_cost_usd: number;
  avg_cost_per_signal: number | null;
  signal_count: number;
  by_day: CostDay[];
}

export interface TickerStats {
  ticker: string;
  signal_count: number;
  avg_confidence: number;
  last_signal_at: string;
  last_direction: string;
  evaluated_count: number;
  correct_count: number;
  accuracy_pct: number | null;
}

export interface DirectionBreakdown {
  direction: string;
  total: number;
  correct: number;
  accuracy_pct: number;
}

export interface EventTypeBreakdown {
  event_type: string;
  total: number;
  correct: number;
  accuracy_pct: number;
}

export interface EvalSummary {
  evaluated: number;
  pending: number;
  accuracy_pct: number | null;
  avg_return_pct: number | null;
  by_direction: DirectionBreakdown[];
  by_event_type: EventTypeBreakdown[];
  as_of: string;
}

export interface Signal {
  id: number;
  event_id: number;
  ticker: string;
  direction: string;
  confidence: number;
  event_type: string;
  reasoning: string;
  cost_usd: string;  // FastAPI serializes Decimal as string
  created_at: string;
  return_pct: number | null;
  correct: boolean | null;
}

// --- fetchers ---

export const fetchPipeline = () => get<PipelineStats>("/stats/pipeline");
export const fetchEvents = () => get<EventStats>("/stats/events");
export const fetchCosts = (days = 30) => get<CostStats>(`/stats/costs?days=${days}`);
export const fetchTickers = () => get<TickerStats[]>("/stats/tickers");
export const fetchEvalSummary = () => get<EvalSummary>("/eval/summary");
export const fetchSignals = (limit = 50) =>
  get<Signal[]>(`/signals?limit=${limit}`);
export const fetchSignalsForTicker = (ticker: string, limit = 100) =>
  get<Signal[]>(`/signals?ticker=${encodeURIComponent(ticker)}&limit=${limit}`);
