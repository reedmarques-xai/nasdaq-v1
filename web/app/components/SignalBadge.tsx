const colors = {
  BUY: "bg-green-bg text-green border-green",
  SELL: "bg-red-bg text-red border-red",
  HOLD: "bg-yellow-bg text-yellow border-yellow",
  BULLISH: "bg-green-bg text-green border-green",
  BEARISH: "bg-red-bg text-red border-red",
  NEUTRAL: "bg-yellow-bg text-yellow border-yellow",
} as const;

export default function SignalBadge({ label }: { label: string }) {
  const cls = colors[label as keyof typeof colors] ?? "bg-surface text-text-muted border-border";
  return (
    <span className={`inline-block px-3.5 py-1 rounded-full text-xs font-bold uppercase tracking-wide border ${cls}`}>
      {label}
    </span>
  );
}
