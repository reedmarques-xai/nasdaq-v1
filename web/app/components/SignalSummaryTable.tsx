import type { TickerSignal } from "@/lib/types";
import ConfidenceBar from "./ConfidenceBar";
import SentimentBadge from "./SentimentBadge";
import SignalBadge from "./SignalBadge";

function exportCsv(signals: TickerSignal[]) {
  const headers = ["Ticker", "Name", "Signal", "Sentiment", "Sentiment Confidence", "Recommended Action"];
  const rows = signals.map((s) => [
    s.symbol,
    `"${s.name}"`,
    s.signal,
    s.sentiment.toFixed(2),
    (s.sentiment_confidence * 100).toFixed(0) + "%",
    `"${s.recommended_action.replace(/"/g, '""')}"`,
  ]);

  const csv = [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `market_signals_${new Date().toISOString().slice(0, 10)}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

export default function SignalSummaryTable({ signals }: { signals: TickerSignal[] }) {
  if (!signals.length) return null;

  return (
    <div className="mb-8 overflow-hidden rounded-xl border border-border bg-surface">
      <div className="flex items-center justify-between px-4 py-2 bg-bg border-b border-border">
        <span className="text-xs text-text-muted uppercase tracking-wide">Signal Summary</span>
        <button
          onClick={() => exportCsv(signals)}
          className="text-xs text-text-muted hover:text-text transition-colors flex items-center gap-1"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </svg>
          Export CSV
        </button>
      </div>
      <table className="w-full border-collapse">
        <thead>
          <tr className="bg-bg">
            {["Ticker", "Name", "Signal", "Sentiment", "Sentiment Confidence", "Recommended Action"].map(h => (
              <th key={h} className="px-4 py-3 text-left text-xs text-text-muted uppercase tracking-wide border-b border-border">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {signals.map(s => (
            <tr key={s.symbol} className="border-b border-border last:border-b-0 hover:bg-blue/[0.03] transition-colors">
              <td className="px-4 py-3 text-sm font-bold">{s.symbol}</td>
              <td className="px-4 py-3 text-sm">{s.name}</td>
              <td className="px-4 py-3"><SignalBadge label={s.signal} /></td>
              <td className="px-4 py-3"><SentimentBadge sentiment={s.sentiment} /></td>
              <td className="px-4 py-3"><ConfidenceBar value={s.sentiment_confidence} max={1} /></td>
              <td className="px-4 py-3 text-xs text-text-muted max-w-xs truncate">{s.recommended_action}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
