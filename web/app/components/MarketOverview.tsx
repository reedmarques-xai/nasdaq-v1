import type { MarketOverview as MarketOverviewType } from "@/lib/types";
import SignalBadge from "./SignalBadge";
import XSourcesPanel from "./XSourcesPanel";

export default function MarketOverview({ data }: { data: MarketOverviewType }) {
  return (
    <div className="animate-fade-in bg-surface rounded-xl border border-border p-6 mb-8">
      <h2 className="text-lg font-semibold mb-4 flex items-center gap-3">
        🌍 Market Overview <SignalBadge label={data.overall_sentiment} />
      </h2>

      <p className="text-text-muted text-sm leading-relaxed mb-4">{data.macro_summary}</p>

      {Object.keys(data.sector_highlights).length > 0 && (
        <>
          <h3 className="text-sm font-semibold mt-4 mb-3">Sector Sentiment</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
            {Object.entries(data.sector_highlights).map(([sector, sentiment]) => (
              <div key={sector} className="bg-bg border border-border rounded-lg p-3">
                <h4 className="text-xs font-semibold text-blue mb-1">{sector}</h4>
                <p className="text-xs text-text-muted">{sentiment}</p>
              </div>
            ))}
          </div>
        </>
      )}

      {data.key_events.length > 0 && (
        <div className="mt-4">
          <h3 className="text-sm font-semibold mb-2">📅 Upcoming Events</h3>
          <ul className="list-disc list-inside text-sm text-text-muted space-y-1">
            {data.key_events.map((evt, i) => <li key={i}>{evt}</li>)}
          </ul>
        </div>
      )}

      <XSourcesPanel sources={data.x_sources} />
    </div>
  );
}
