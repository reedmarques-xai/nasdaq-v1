"""Signal engine — orchestrates data fetching and parallel Grok analysis."""

from __future__ import annotations

import json
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from datetime import datetime

from rich.console import Console
from rich.progress import BarColumn, MofNCompleteColumn, Progress, SpinnerColumn, TextColumn

from .data_fetcher import NasdaqDataFetcher
from .grok_analyzer import GrokAnalyzer
from .models import MarketReport, TickerSignal, XSource

console = Console()


def _serialize(obj: object) -> object:
    """JSON-safe serializer for dataclasses with datetime / XSource."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, XSource):
        return {"url": obj.url, "handle": obj.handle, "title": obj.title, "display_label": obj.display_label}
    return str(obj)


class SignalEngine:
    """Orchestrates the full pipeline: fetch data → parallel Grok analysis → signals."""

    def __init__(
        self,
        data_fetcher: NasdaqDataFetcher,
        grok_analyzer: GrokAnalyzer,
    ) -> None:
        self.fetcher = data_fetcher
        self.grok = grok_analyzer

    # ------------------------------------------------------------------
    # Streaming generator — yields SSE events for the web frontend
    # ------------------------------------------------------------------
    def generate_report_stream(
        self, tickers: list[dict]
    ) -> Generator[dict, None, None]:
        """Yield SSE-ready dicts as each pipeline step completes.

        Event types:
            status   – granular progress updates (see steps below)
            overview – full MarketOverview as dict
            signal   – full TickerSignal as dict
            done     – {"total_signals": N}

        Status steps:
            plan              – initial plan with ticker list
            fetching          – starting to fetch NASDAQ data for a ticker
            fetched           – finished fetching NASDAQ data for a ticker
            analyzing         – all Grok calls dispatched in parallel
            overview_complete – market overview finished
        """
        symbols = [t["symbol"] for t in tickers]

        # 0) Emit the plan so the frontend knows the full task list
        yield {
            "event": "status",
            "data": {
                "step": "plan",
                "tickers": [{"symbol": t["symbol"], "name": t["name"]} for t in tickers],
            },
        }

        # 1) Fetch NASDAQ data for all tickers in parallel
        # Mark all as fetching
        for t in tickers:
            yield {
                "event": "status",
                "data": {"step": "fetching", "ticker": t["symbol"]},
            }

        ticker_data: list[dict] = [{}] * len(tickers)  # preserve order
        with ThreadPoolExecutor(max_workers=len(tickers)) as pool:
            fetch_futures = {
                pool.submit(self.fetcher.fetch_all, t["symbol"], t["name"]): idx
                for idx, t in enumerate(tickers)
            }
            for fut in as_completed(fetch_futures):
                idx = fetch_futures[fut]
                ticker_data[idx] = fut.result()
                yield {
                    "event": "status",
                    "data": {"step": "fetched", "ticker": tickers[idx]["symbol"]},
                }

        # 2) Fire off all Grok calls in parallel
        yield {
            "event": "status",
            "data": {"step": "analyzing", "tickers": symbols},
        }
        max_workers = 1 + len(tickers)

        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            overview_future = pool.submit(self.grok.get_market_overview)

            ticker_futures = {}
            for idx, td in enumerate(ticker_data):
                fut = pool.submit(
                    self.grok.analyze_ticker,
                    ticker=td["ticker"],
                    name=td["name"],
                    nasdaq_data=td,
                )
                ticker_futures[fut] = idx

            # Yield overview as soon as it's ready
            overview = overview_future.result()
            overview_dict = asdict(overview)
            overview_dict["x_sources"] = [
                _serialize(s) for s in overview.x_sources
            ]
            overview_dict["timestamp"] = overview.timestamp.isoformat()
            yield {
                "event": "status",
                "data": {"step": "overview_complete"},
            }
            yield {"event": "overview", "data": overview_dict}

            # Yield each signal as it completes
            for fut in as_completed(ticker_futures):
                sig = fut.result()
                sig_dict = asdict(sig)
                sig_dict["x_sources"] = [_serialize(s) for s in sig.x_sources]
                sig_dict["timestamp"] = sig.timestamp.isoformat()
                yield {"event": "signal", "data": sig_dict}

        yield {"event": "done", "data": {"total_signals": len(tickers)}}

    # ------------------------------------------------------------------
    # Batch mode — existing CLI method
    # ------------------------------------------------------------------
    def generate_report(self, tickers: list[dict]) -> MarketReport:
        """
        Run the full signal generation pipeline.

        All Grok API calls (market overview + every ticker analysis) are
        dispatched in parallel via a thread pool.  Each ``_call_grok``
        creates its own independent ``chat`` session so there are no
        shared-state concerns.

        Parameters
        ----------
        tickers : list[dict]
            Each dict has keys ``symbol`` and ``name``.

        Returns
        -------
        MarketReport
            Complete report with market overview + per-ticker signals.
        """
        console.rule("[bold blue]📡 Market Signal Generator[/bold blue]")
        console.print()

        # ── 1) Fetch NASDAQ data for each ticker (sequential — fast) ──
        console.print("[bold]Step 1/2 — Fetching NASDAQ Data[/bold]")
        ticker_data: list[dict] = []
        for t in tickers:
            data = self.fetcher.fetch_all(t["symbol"], t["name"])
            ticker_data.append(data)
        console.print()

        # ── 2) Parallel Grok analysis (market overview + all tickers) ─
        console.print(
            f"[bold]Step 2/2 — Grok Analysis + X Sentiment "
            f"({1 + len(tickers)} parallel calls)[/bold]"
        )

        # Use a thread pool with one worker per call (overview + N tickers)
        max_workers = 1 + len(tickers)
        overview = None
        # Pre-fill signals list to preserve ticker order
        signals: list[TickerSignal | None] = [None] * len(ticker_data)

        with (
            ThreadPoolExecutor(max_workers=max_workers) as pool,
            Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                MofNCompleteColumn(),
                console=console,
            ) as progress,
        ):
            total = 1 + len(ticker_data)  # overview + tickers
            task = progress.add_task("Analyzing…", total=total)

            # Submit market overview
            overview_future = pool.submit(self.grok.get_market_overview)

            # Submit each ticker analysis, tracking its index
            ticker_futures = {}
            for idx, td in enumerate(ticker_data):
                fut = pool.submit(
                    self.grok.analyze_ticker,
                    ticker=td["ticker"],
                    name=td["name"],
                    nasdaq_data=td,
                )
                ticker_futures[fut] = idx

            # Collect the overview
            overview = overview_future.result()
            progress.advance(task)

            # Collect ticker results as they complete
            for fut in as_completed(ticker_futures):
                idx = ticker_futures[fut]
                signals[idx] = fut.result()
                progress.advance(task)

        console.print(
            f"  Overall sentiment: [bold]{overview.overall_sentiment}[/bold]\n"
        )

        report = MarketReport(
            overview=overview,
            signals=signals,  # type: ignore[arg-type]
            generated_at=datetime.now(),
        )

        # Quick summary to console
        self._print_summary(report)
        return report

    # ------------------------------------------------------------------
    # Console summary
    # ------------------------------------------------------------------
    @staticmethod
    def _print_summary(report: MarketReport) -> None:
        console.rule("[bold green]📊 Signal Summary[/bold green]")

        signal_colors = {"BUY": "green", "SELL": "red", "HOLD": "yellow"}

        for sig in report.signals:
            color = signal_colors.get(sig.signal, "white")
            console.print(
                f"  [{color}]{sig.signal:4s}[/{color}] "
                f"(confidence {sig.confidence}/10)  "
                f"[bold]{sig.symbol:6s}[/bold] {sig.name}"
            )

        buy_count = len(report.buy_signals)
        sell_count = len(report.sell_signals)
        hold_count = len(report.hold_signals)
        console.print(
            f"\n  Totals: [green]{buy_count} BUY[/green] · "
            f"[red]{sell_count} SELL[/red] · "
            f"[yellow]{hold_count} HOLD[/yellow]"
        )
        console.print()
