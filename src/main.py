"""
Market Signal Generator — main entry point.

Downloads NASDAQ Data Link data (RTAT + STAT), enriches it with real-time
X/Twitter sentiment via Grok's x-search, and generates an HTML report with
actionable trading signals.

Usage:
    python -m src.main                          # Use config defaults
    python -m src.main --tickers AAPL,MSFT      # Override tickers
    python -m src.main --output report.html     # Custom output name
    python -m src.main --no-browser             # Skip auto-open
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

from .data_fetcher import NasdaqDataFetcher
from .grok_analyzer import GrokAnalyzer
from .report_generator import ReportGenerator
from .signal_engine import SignalEngine

console = Console()


def load_config() -> tuple[dict, list[dict]]:
    """Load settings.yaml and tickers.yaml from the config/ directory."""
    config_dir = Path(__file__).resolve().parent.parent / "config"

    settings_path = config_dir / "settings.yaml"
    tickers_path = config_dir / "tickers.yaml"

    if not settings_path.exists():
        console.print("[red]✗ config/settings.yaml not found[/red]")
        sys.exit(1)
    if not tickers_path.exists():
        console.print("[red]✗ config/tickers.yaml not found[/red]")
        sys.exit(1)

    with open(settings_path) as f:
        settings = yaml.safe_load(f)
    with open(tickers_path) as f:
        tickers_config = yaml.safe_load(f)

    return settings, tickers_config.get("tickers", [])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="NASDAQ + Grok Market Signal Generator"
    )
    parser.add_argument(
        "--tickers",
        type=str,
        default=None,
        help="Comma-separated ticker symbols to override config (e.g., AAPL,MSFT,TSLA)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Custom output filename (saved in output/ directory)",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Don't auto-open the report in a browser",
    )
    return parser.parse_args()


def main() -> None:
    # Load environment variables from .env
    load_dotenv()

    args = parse_args()
    settings, config_tickers = load_config()

    # ── Validate API keys ──────────────────────────────────────────
    nasdaq_key = os.getenv("NASDAQ_DATA_LINK_API_KEY")
    xai_key = os.getenv("XAI_API_KEY")

    if not nasdaq_key:
        console.print(
            Panel(
                "[red]NASDAQ_DATA_LINK_API_KEY not set.[/red]\n"
                "Copy .env.example to .env and add your key.\n"
                "Get one at: https://data.nasdaq.com/account/profile",
                title="Missing API Key",
            )
        )
        sys.exit(1)

    if not xai_key:
        console.print(
            Panel(
                "[red]XAI_API_KEY not set.[/red]\n"
                "Copy .env.example to .env and add your key.\n"
                "Get one at: https://console.x.ai",
                title="Missing API Key",
            )
        )
        sys.exit(1)

    # ── Resolve tickers ────────────────────────────────────────────
    if args.tickers:
        # CLI override: convert "AAPL,MSFT" → list of dicts
        tickers = [
            {"symbol": t.strip().upper(), "name": t.strip().upper()}
            for t in args.tickers.split(",")
        ]
    else:
        tickers = config_tickers

    if not tickers:
        console.print("[red]No tickers configured. Check config/tickers.yaml[/red]")
        sys.exit(1)

    console.print(
        Panel(
            f"Analyzing [bold]{len(tickers)}[/bold] tickers: "
            + ", ".join(t["symbol"] for t in tickers),
            title="🚀 Market Signal Generator",
            border_style="blue",
        )
    )

    # ── Initialize components ──────────────────────────────────────
    fetcher = NasdaqDataFetcher(
        api_key=nasdaq_key,
        settings=settings.get("nasdaq", {}),
    )
    analyzer = GrokAnalyzer(
        api_key=xai_key,
        settings=settings.get("grok", {}),
    )

    report_settings = settings.get("report", {})
    if args.no_browser:
        report_settings["open_browser"] = False

    generator = ReportGenerator(settings=report_settings)
    engine = SignalEngine(data_fetcher=fetcher, grok_analyzer=analyzer)

    # ── Run the pipeline ───────────────────────────────────────────
    report = engine.generate_report(tickers)

    # ── Generate HTML report ───────────────────────────────────────
    console.rule("[bold blue]📄 Generating Report[/bold blue]")
    output_path = generator.generate(report)

    console.print()
    console.print(
        Panel(
            f"✅ Done! Report saved to [bold]{output_path}[/bold]",
            border_style="green",
        )
    )


if __name__ == "__main__":
    main()
