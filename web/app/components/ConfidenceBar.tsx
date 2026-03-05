export default function ConfidenceBar({ value, max = 10 }: { value: number; max?: number }) {
  const pct = (value / max) * 100;
  const norm = pct / 100; // 0-1 for color thresholds
  const color = norm >= 0.7 ? "bg-green" : norm >= 0.4 ? "bg-yellow" : "bg-red";
  const label = max === 1 ? `${(value * 100).toFixed(0)}%` : `${value}/${max}`;

  return (
    <div className="flex items-center gap-2">
      <div className="w-20 h-2 bg-bg rounded-full overflow-hidden border border-border">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-sm text-text-muted">{label}</span>
    </div>
  );
}
