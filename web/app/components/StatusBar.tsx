import type { ProgressTask } from "@/lib/types";

function TaskIcon({ status }: { status: ProgressTask["status"] }) {
  if (status === "done") {
    return <span className="text-green text-sm">✓</span>;
  }
  if (status === "running") {
    return (
      <span className="inline-block w-3.5 h-3.5 border-2 border-blue border-t-transparent rounded-full animate-spin" />
    );
  }
  return <span className="text-border text-sm">○</span>;
}

export default function StatusBar({ tasks }: { tasks: ProgressTask[] }) {
  if (!tasks.length) return null;

  const done = tasks.filter((t) => t.status === "done").length;
  const total = tasks.length;
  const pct = total > 0 ? Math.round((done / total) * 100) : 0;

  // Split into phases for visual grouping
  const fetchTasks = tasks.filter((t) => t.id.startsWith("fetch-"));
  const analysisTasks = tasks.filter(
    (t) => t.id.startsWith("analyze-") || t.id === "overview"
  );

  return (
    <div className="mb-6 bg-surface border border-border rounded-xl p-5">
      {/* Overall progress */}
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm font-semibold">
          Pipeline Progress
        </span>
        <span className="text-xs text-text-muted">
          {done}/{total} tasks · {pct}%
        </span>
      </div>
      <div className="w-full h-1.5 bg-bg rounded-full overflow-hidden border border-border mb-5">
        <div
          className="h-full bg-blue rounded-full transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Phase 1: Data Fetching */}
        {fetchTasks.length > 0 && (
          <div>
            <h3 className="text-xs font-semibold text-text-muted uppercase tracking-wide mb-2">
              Phase 1 — NASDAQ Data Fetching
            </h3>
            <ul className="space-y-1.5">
              {fetchTasks.map((t) => (
                <li key={t.id} className="flex items-center gap-2">
                  <TaskIcon status={t.status} />
                  <span
                    className={`text-sm ${
                      t.status === "done"
                        ? "text-text-muted line-through"
                        : t.status === "running"
                          ? "text-text"
                          : "text-text-muted"
                    }`}
                  >
                    {t.label}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Phase 2: Grok Analysis */}
        {analysisTasks.length > 0 && (
          <div>
            <h3 className="text-xs font-semibold text-text-muted uppercase tracking-wide mb-2">
              Phase 2 — Grok AI + X Sentiment Analysis
            </h3>
            <ul className="space-y-1.5">
              {analysisTasks.map((t) => (
                <li key={t.id} className="flex items-center gap-2">
                  <TaskIcon status={t.status} />
                  <span
                    className={`text-sm ${
                      t.status === "done"
                        ? "text-text-muted line-through"
                        : t.status === "running"
                          ? "text-text"
                          : "text-text-muted"
                    }`}
                  >
                    {t.label}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
