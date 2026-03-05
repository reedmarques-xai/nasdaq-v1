function getLabel(v: number): string {
  if (v >= 0.5) return "Bullish";
  if (v > 0.1) return "Lean Bull";
  if (v >= -0.1) return "Neutral";
  if (v > -0.5) return "Lean Bear";
  return "Bearish";
}

function getColor(v: number): { bar: string; text: string; border: string; bg: string } {
  if (v >= 0.1) return { bar: "bg-green", text: "text-green", border: "border-green", bg: "bg-green-bg" };
  if (v > -0.1) return { bar: "bg-yellow", text: "text-yellow", border: "border-yellow", bg: "bg-yellow-bg" };
  return { bar: "bg-red", text: "text-red", border: "border-red", bg: "bg-red-bg" };
}

export default function SentimentBadge({ sentiment }: { sentiment: number }) {
  const label = getLabel(sentiment);
  const c = getColor(sentiment);
  // Map -1..1 → 0%..100% for the bar fill
  const pct = ((sentiment + 1) / 2) * 100;

  return (
    <div className="flex items-center gap-2">
      <div className="w-20 h-2 bg-bg rounded-full overflow-hidden border border-border relative">
        {/* center tick */}
        <div className="absolute left-1/2 top-0 bottom-0 w-px bg-border" />
        <div className={`h-full rounded-full ${c.bar}`} style={{ width: `${pct}%` }} />
      </div>
      <span className={`text-xs font-semibold ${c.text}`}>
        {sentiment > 0 ? "+" : ""}{sentiment.toFixed(2)} {label}
      </span>
    </div>
  );
}