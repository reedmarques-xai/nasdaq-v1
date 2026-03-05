// TypeScript interfaces matching Python dataclass models

export interface XSource {
  url: string;
  handle: string;
  title: string;
  display_label: string;
}

export interface TickerSignal {
  symbol: string;
  name: string;
  signal: "BUY" | "SELL" | "HOLD";
  confidence: number;
  sentiment: number;           // -1.0 (very bearish) to 1.0 (very bullish)
  sentiment_confidence: number; // 0.0 to 1.0
  retail_flow_summary: string;
  stat_summary: string;
  x_sentiment: string;
  catalysts: string[];
  risks: string[];
  reasoning: string;
  recommended_action: string;
  x_sources: XSource[];
  timestamp: string;
}

export interface MarketOverview {
  overall_sentiment: "BULLISH" | "BEARISH" | "NEUTRAL";
  macro_summary: string;
  sector_highlights: Record<string, string>;
  key_events: string[];
  x_sources: XSource[];
  timestamp: string;
}

export interface Ticker {
  symbol: string;
  name: string;
}

// SSE event types
export type SSEStatus =
  | { step: "plan"; tickers: Ticker[] }
  | { step: "fetching"; ticker: string }
  | { step: "fetched"; ticker: string }
  | { step: "analyzing"; tickers: string[] }
  | { step: "overview_complete" };

export type SSEDone = { total_signals: number };

// Progress task for the checklist UI
export type TaskStatus = "pending" | "running" | "done";
export interface ProgressTask {
  id: string;
  label: string;
  status: TaskStatus;
}
