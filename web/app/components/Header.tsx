export default function Header({ timestamp, running, onRun }: {
  timestamp: string | null;
  running: boolean;
  onRun: () => void;
}) {
  return (
    <div className="text-center mb-8 p-8 bg-surface rounded-xl border border-border">
      <h1 className="text-2xl font-semibold mb-2">📊 Market Signal Report</h1>
      <p className="text-text-muted text-sm mb-4">
        {timestamp ? `Generated ${timestamp}` : "Powered by NASDAQ Data Link + Grok AI"}
      </p>
      <button
        onClick={onRun}
        disabled={running}
        className="px-6 py-2.5 rounded-lg font-semibold text-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed bg-blue text-bg hover:bg-blue/80"
      >
        {running ? (
          <span className="flex items-center gap-2">
            <span className="inline-block w-4 h-4 border-2 border-bg border-t-transparent rounded-full animate-spin" />
            Analyzing…
          </span>
        ) : (
          "🚀 Run Analysis"
        )}
      </button>
    </div>
  );
}
