import type { TickerSignal } from "@/lib/types";
import ConfidenceBar from "./ConfidenceBar";
import SentimentBadge from "./SentimentBadge";
import SignalBadge from "./SignalBadge";
import XSourcesPanel from "./XSourcesPanel";

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-bg border border-border rounded-lg p-4">
      <h3 className="text-xs font-semibold text-blue uppercase tracking-wide mb-2">{title}</h3>
      <p className="text-sm text-text-muted leading-relaxed">{children}</p>
    </div>
  );
}

export default function TickerCard({ signal }: { signal: TickerSignal }) {
  return (
    <div className="animate-fade-in bg-surface rounded-xl border border-border p-6 mb-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-4 flex-wrap gap-3">
        <h2 className="text-xl font-semibold">{signal.symbol} — {signal.name}</h2>
        <div className="flex items-center gap-3">
          <SignalBadge label={signal.signal} />
          <SentimentBadge sentiment={signal.sentiment} />
          <div className="flex flex-col items-end">
            <span className="text-[10px] text-text-muted uppercase tracking-wide">Sentiment Confidence</span>
            <ConfidenceBar value={signal.sentiment_confidence} max={1} />
          </div>
        </div>
      </div>

      {/* 2x2 grid of analysis sections */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <Section title="📈 Retail Flow (RTAT)">{signal.retail_flow_summary}</Section>
        <Section title="📊 Fundamentals (STAT)">{signal.stat_summary}</Section>
        <Section title="🐦 X / Twitter Sentiment">{signal.x_sentiment}</Section>
        <Section title="🧠 Reasoning">{signal.reasoning}</Section>
      </div>

      {/* Catalysts + Risks */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div className="bg-bg border border-border rounded-lg p-4">
          <h3 className="text-xs font-semibold text-green mb-2">🚀 Catalysts</h3>
          <ul className="list-disc list-inside text-sm text-text-muted space-y-1">
            {signal.catalysts.length ? signal.catalysts.map((c, i) => <li key={i}>{c}</li>) : <li>None identified</li>}
          </ul>
        </div>
        <div className="bg-bg border border-border rounded-lg p-4">
          <h3 className="text-xs font-semibold text-red mb-2">⚠️ Risks</h3>
          <ul className="list-disc list-inside text-sm text-text-muted space-y-1">
            {signal.risks.length ? signal.risks.map((r, i) => <li key={i}>{r}</li>) : <li>None identified</li>}
          </ul>
        </div>
      </div>

      {/* Action callout */}
      <div className="bg-blue-bg border border-blue rounded-lg p-4 mb-2">
        <h3 className="text-xs font-semibold text-blue mb-1">💡 Recommended Action</h3>
        <p className="text-sm font-semibold">{signal.recommended_action}</p>
      </div>

      <XSourcesPanel sources={signal.x_sources} />
    </div>
  );
}
