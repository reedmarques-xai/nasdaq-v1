"use client";

import { useCallback, useRef, useState } from "react";
import { startAnalysis } from "@/lib/api";
import type {
  MarketOverview as MarketOverviewType,
  ProgressTask,
  SSEStatus,
  TickerSignal,
} from "@/lib/types";

import Disclaimer from "./components/Disclaimer";
import Header from "./components/Header";
import MarketOverview from "./components/MarketOverview";
import SignalSummaryTable from "./components/SignalSummaryTable";
import StatusBar from "./components/StatusBar";
import TickerCard from "./components/TickerCard";

// ── helpers to build / update the task list ────────────────────────

function buildTasksFromPlan(
  tickers: { symbol: string; name: string }[]
): ProgressTask[] {
  const fetch: ProgressTask[] = tickers.map((t) => ({
    id: `fetch-${t.symbol}`,
    label: `Fetch NASDAQ data for ${t.symbol} (${t.name})`,
    status: "pending",
  }));
  const analysis: ProgressTask[] = [
    {
      id: "overview",
      label: "Market overview via Grok + X search",
      status: "pending",
    },
    ...tickers.map((t) => ({
      id: `analyze-${t.symbol}`,
      label: `Analyze ${t.symbol} (${t.name}) via Grok + X search`,
      status: "pending" as const,
    })),
  ];
  return [...fetch, ...analysis];
}

function updateTask(
  tasks: ProgressTask[],
  id: string,
  status: ProgressTask["status"]
): ProgressTask[] {
  return tasks.map((t) => (t.id === id ? { ...t, status } : t));
}

function updateMany(
  tasks: ProgressTask[],
  prefix: string,
  status: ProgressTask["status"]
): ProgressTask[] {
  return tasks.map((t) =>
    t.id.startsWith(prefix) ? { ...t, status } : t
  );
}

// ── component ──────────────────────────────────────────────────────

export default function Home() {
  const [running, setRunning] = useState(false);
  const [tasks, setTasks] = useState<ProgressTask[]>([]);
  const [overview, setOverview] = useState<MarketOverviewType | null>(null);
  const [signals, setSignals] = useState<TickerSignal[]>([]);
  const [timestamp, setTimestamp] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const cancelRef = useRef<(() => void) | null>(null);

  const handleStatus = useCallback((data: SSEStatus) => {
    switch (data.step) {
      case "plan":
        setTasks(buildTasksFromPlan(data.tickers));
        break;
      case "fetching":
        setTasks((prev) => updateTask(prev, `fetch-${data.ticker}`, "running"));
        break;
      case "fetched":
        setTasks((prev) => updateTask(prev, `fetch-${data.ticker}`, "done"));
        break;
      case "analyzing":
        // Mark overview + all ticker analyses as running
        setTasks((prev) => {
          let next = updateTask(prev, "overview", "running");
          next = updateMany(next, "analyze-", "running");
          return next;
        });
        break;
      case "overview_complete":
        setTasks((prev) => updateTask(prev, "overview", "done"));
        break;
    }
  }, []);

  const handleRun = useCallback(() => {
    setRunning(true);
    setOverview(null);
    setSignals([]);
    setTasks([]);
    setTimestamp(null);
    setError(null);

    const cancel = startAnalysis({
      onStatus: handleStatus,
      onOverview: (data) => {
        setOverview(data);
        setTimestamp(new Date().toLocaleString());
      },
      onSignal: (data) => {
        setSignals((prev) => [...prev, data]);
        // Mark this ticker's analysis as done
        setTasks((prev) => updateTask(prev, `analyze-${data.symbol}`, "done"));
      },
      onDone: () => {
        setRunning(false);
      },
      onError: (err) => {
        setError(err);
        setRunning(false);
      },
    });

    cancelRef.current = cancel;
  }, [handleStatus]);

  return (
    <>
      <Header timestamp={timestamp} running={running} onRun={handleRun} />

      {error && (
        <div className="mb-6 bg-red-bg border border-red rounded-xl p-4 text-red text-sm">
          ⚠️ {error}
        </div>
      )}

      {running && <StatusBar tasks={tasks} />}

      {overview && <MarketOverview data={overview} />}

      <SignalSummaryTable signals={signals} />

      {signals.map((sig) => (
        <TickerCard key={sig.symbol} signal={sig} />
      ))}

      {(overview || signals.length > 0) && <Disclaimer />}
    </>
  );
}
