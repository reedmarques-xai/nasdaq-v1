import type { MarketOverview, SSEDone, SSEStatus, Ticker, TickerSignal } from "./types";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ── REST helpers ──────────────────────────────────────────────────

export async function fetchTickers(): Promise<Ticker[]> {
  const res = await fetch(`${API}/api/tickers`);
  const data = await res.json();
  return data.tickers;
}

export async function saveTickers(tickers: Ticker[]): Promise<void> {
  await fetch(`${API}/api/tickers`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tickers }),
  });
}

// ── SSE streaming client ──────────────────────────────────────────

export interface AnalysisCallbacks {
  onStatus: (data: SSEStatus) => void;
  onOverview: (data: MarketOverview) => void;
  onSignal: (data: TickerSignal) => void;
  onDone: (data: SSEDone) => void;
  onError: (error: string) => void;
}

export function startAnalysis(
  callbacks: AnalysisCallbacks,
  tickers?: Ticker[]
): () => void {
  const controller = new AbortController();

  (async () => {
    try {
      const res = await fetch(`${API}/api/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tickers: tickers ?? null }),
        signal: controller.signal,
      });

      if (!res.ok || !res.body) {
        callbacks.onError(`HTTP ${res.status}: ${res.statusText}`);
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let currentEvent = "";
      let dataLines: string[] = [];

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        for (const rawLine of lines) {
          const line = rawLine.replace(/\r$/, "");
          if (line.startsWith("event:")) {
            currentEvent = line.slice(6).trim();
          } else if (line.startsWith("data:")) {
            dataLines.push(line.slice(5).trim());
          } else if (line === "" && currentEvent && dataLines.length > 0) {
            const payload = JSON.parse(dataLines.join("\n"));
            switch (currentEvent) {
              case "status":
                callbacks.onStatus(payload);
                break;
              case "overview":
                callbacks.onOverview(payload);
                break;
              case "signal":
                callbacks.onSignal(payload);
                break;
              case "done":
                callbacks.onDone(payload);
                break;
            }
            currentEvent = "";
            dataLines = [];
          }
        }
      }
    } catch (err) {
      if (!controller.signal.aborted) {
        callbacks.onError(String(err));
      }
    }
  })();

  return () => controller.abort();
}
