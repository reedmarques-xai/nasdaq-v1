"""NASDAQ Data Link API client for RTAT, STAT, and UREF datasets."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path

import nasdaqdatalink
import pandas as pd
from rich.console import Console

console = Console()

_DOWNLOADS = Path.home() / "Downloads" / "nasdaq_data"


class NasdaqDataFetcher:
    """Fetches RTAT, STAT, and UREF (intraday retail flow) data."""

    def __init__(self, api_key: str, settings: dict) -> None:
        self.settings = settings
        nasdaqdatalink.ApiConfig.api_key = api_key

        self.rtat_table = settings.get("rtat_table", "NDAQ/RTAT10")
        self.stat_table = settings.get("stat_table", "NDAQ/STAT")
        self.uref_table = settings.get("uref_table", "UREF/FFI")
        self.rtat_lookback = settings.get("rtat_lookback_days", 30)
        self.stat_lookback = settings.get("stat_lookback_days", 30)
        self.uref_lookback = settings.get("uref_lookback_days", 5)

        # Create the download folder once at init
        self.download_dir = _DOWNLOADS / datetime.now().strftime("%Y-%m-%d_%H%M%S")
        self.download_dir.mkdir(parents=True, exist_ok=True)
        console.print(f"  📂 Saving NASDAQ data to [bold]{self.download_dir}[/bold]")

    # ------------------------------------------------------------------
    # RTAT — Retail Trading Activity Tracker
    # Columns: date, ticker, activity (0-1 share of retail $), sentiment (-100 to +100)
    # ------------------------------------------------------------------
    def fetch_rtat(self, ticker: str) -> pd.DataFrame:
        """Fetch RTAT data for a ticker over the lookback window."""
        start = (datetime.now() - timedelta(days=self.rtat_lookback)).strftime("%Y-%m-%d")
        end = datetime.now().strftime("%Y-%m-%d")

        try:
            df = nasdaqdatalink.get_table(
                self.rtat_table,
                ticker=ticker,
                date={"gte": start, "lte": end},
                paginate=True,
            )
            if df.empty:
                console.print(f"  [yellow]⚠ No RTAT data for {ticker}[/yellow]")
            else:
                path = self.download_dir / f"{ticker}_RTAT.csv"
                df.to_csv(path, index=False)
            return df
        except Exception as exc:
            console.print(f"  [red]✗ RTAT fetch failed for {ticker}: {exc}[/red]")
            return pd.DataFrame()

    # ------------------------------------------------------------------
    # STAT — Stock Statistics (E360)
    # Columns: symbol, marketcap, high52week, low52week, avgvolume1m/3m,
    #          divyield, pe, eps, epsdil, pb, freefloat, …
    # ------------------------------------------------------------------
    def fetch_stat(self, ticker: str) -> pd.DataFrame:
        """Fetch the latest STAT snapshot for a ticker."""
        try:
            df = nasdaqdatalink.get_table(
                self.stat_table,
                symbol=ticker,
                paginate=True,
            )
            if df.empty:
                console.print(f"  [yellow]⚠ No STAT data for {ticker}[/yellow]")
            else:
                path = self.download_dir / f"{ticker}_STAT.csv"
                df.to_csv(path, index=False)
            return df
        except Exception as exc:
            console.print(f"  [red]✗ STAT fetch failed for {ticker}: {exc}[/red]")
            return pd.DataFrame()

    # ------------------------------------------------------------------
    # UREF — Intraday US Retail Equities Flow (15-min bars)
    # Columns: date, minute, ticker, volume_buy, volume_sell,
    #          update_time, is_healthy
    # ------------------------------------------------------------------
    def fetch_uref(self, ticker: str) -> pd.DataFrame:
        """Fetch intraday retail flow data (UREF/FFI) for recent days."""
        start = (datetime.now() - timedelta(days=self.uref_lookback)).strftime("%Y-%m-%d")
        end = datetime.now().strftime("%Y-%m-%d")

        try:
            df = nasdaqdatalink.get_table(
                self.uref_table,
                ticker=ticker,
                date={"gte": start, "lte": end},
                paginate=True,
            )
            if df.empty:
                console.print(f"  [yellow]⚠ No UREF data for {ticker}[/yellow]")
            else:
                path = self.download_dir / f"{ticker}_UREF.csv"
                df.to_csv(path, index=False)
            return df
        except Exception as exc:
            console.print(f"  [red]✗ UREF fetch failed for {ticker}: {exc}[/red]")
            return pd.DataFrame()

    # ------------------------------------------------------------------
    # Combined fetch
    # ------------------------------------------------------------------
    def fetch_all(self, ticker: str, name: str) -> dict:
        """Fetch RTAT + STAT + UREF in parallel and return a context dict for Grok."""
        console.print(f"  Fetching data for [bold cyan]{ticker}[/bold cyan] ({name})…")

        with ThreadPoolExecutor(max_workers=3) as pool:
            rtat_fut = pool.submit(self.fetch_rtat, ticker)
            stat_fut = pool.submit(self.fetch_stat, ticker)
            uref_fut = pool.submit(self.fetch_uref, ticker)

            rtat_df = rtat_fut.result()
            stat_df = stat_fut.result()
            uref_df = uref_fut.result()

        # Build human-readable summaries for Grok context
        rtat_summary = self._summarise_rtat(rtat_df, ticker)
        stat_summary = self._summarise_stat(stat_df, ticker)
        uref_summary = self._summarise_uref(uref_df, ticker)

        return {
            "ticker": ticker,
            "name": name,
            "rtat_df": rtat_df,
            "stat_df": stat_df,
            "uref_df": uref_df,
            "rtat_summary": rtat_summary,
            "stat_summary": stat_summary,
            "uref_summary": uref_summary,
        }

    # ------------------------------------------------------------------
    # Internal helpers — build text summaries to send to Grok
    # ------------------------------------------------------------------
    @staticmethod
    def _summarise_rtat(df: pd.DataFrame, ticker: str) -> str:
        if df.empty:
            return f"No RTAT (retail trading activity) data available for {ticker}."

        lines = [f"RTAT Retail Trading Activity for {ticker} (last {len(df)} trading days):"]
        latest = df.sort_values("date", ascending=False).head(5)
        for _, row in latest.iterrows():
            date_str = row["date"].strftime("%Y-%m-%d") if hasattr(row["date"], "strftime") else str(row["date"])
            lines.append(
                f"  {date_str}: activity={row['activity']:.6f}, sentiment={row['sentiment']}"
            )

        # Aggregate stats
        lines.append(f"  Avg activity (period): {df['activity'].mean():.6f}")
        lines.append(f"  Avg sentiment (period): {df['sentiment'].mean():.1f}")
        lines.append(f"  Latest sentiment: {df.sort_values('date', ascending=False).iloc[0]['sentiment']}")

        sent = df.sort_values("date", ascending=False).iloc[0]["sentiment"]
        if sent > 20:
            lines.append("  Interpretation: Retail traders are net BUYERS (bullish retail flow).")
        elif sent < -20:
            lines.append("  Interpretation: Retail traders are net SELLERS (bearish retail flow).")
        else:
            lines.append("  Interpretation: Retail flow is roughly neutral.")

        return "\n".join(lines)

    @staticmethod
    def _summarise_stat(df: pd.DataFrame, ticker: str) -> str:
        if df.empty:
            return f"No STAT (stock statistics) data available for {ticker}."

        row = df.iloc[0]  # latest snapshot
        lines = [f"STAT Stock Statistics for {ticker}:"]

        field_labels = {
            "marketcap": "Market Cap ($M)",
            "high52week": "52-Week High",
            "low52week": "52-Week Low",
            "avgvolume1m": "Avg Volume (1M)",
            "avgvolume3m": "Avg Volume (3M)",
            "divyield": "Dividend Yield",
            "pe": "P/E Ratio",
            "eps": "EPS",
            "epsdil": "EPS (Diluted)",
            "pb": "P/B Ratio",
            "freefloat": "Free Float %",
        }

        for col, label in field_labels.items():
            if col in row.index and pd.notna(row[col]):
                val = row[col]
                if col == "marketcap":
                    lines.append(f"  {label}: ${val:,.1f}M")
                elif col in ("divyield", "freefloat"):
                    lines.append(f"  {label}: {val:.2%}")
                elif col in ("avgvolume1m", "avgvolume3m"):
                    lines.append(f"  {label}: {val:,.0f}")
                else:
                    lines.append(f"  {label}: {val}")

        return "\n".join(lines)

    @staticmethod
    def _summarise_uref(df: pd.DataFrame, ticker: str) -> str:
        if df.empty:
            return f"No UREF (intraday retail flow) data available for {ticker}."

        # Aggregate 15-min bars into daily totals
        daily = (
            df.groupby("date")
            .agg(buy=("volume_buy", "sum"), sell=("volume_sell", "sum"))
            .sort_index(ascending=False)
        )
        daily["net"] = daily["buy"] - daily["sell"]
        daily["ratio"] = daily["buy"] / daily["sell"].replace(0, 1)

        lines = [
            f"UREF Intraday Retail Flow for {ticker} "
            f"(last {len(daily)} trading days, 15-min granularity):"
        ]

        for date_val, row in daily.head(5).iterrows():
            date_str = date_val.strftime("%Y-%m-%d") if hasattr(date_val, "strftime") else str(date_val)
            direction = "BUY" if row["net"] > 0 else "SELL"
            lines.append(
                f"  {date_str}: buy={row['buy']:,.0f} sell={row['sell']:,.0f} "
                f"net={row['net']:+,.0f} ({direction}) ratio={row['ratio']:.2f}"
            )

        total_buy = daily["buy"].sum()
        total_sell = daily["sell"].sum()
        total_net = total_buy - total_sell
        avg_ratio = total_buy / max(total_sell, 1)
        lines.append(f"  Period totals: buy={total_buy:,.0f} sell={total_sell:,.0f} net={total_net:+,.0f}")
        lines.append(f"  Avg buy/sell ratio: {avg_ratio:.2f}")

        if avg_ratio > 1.1:
            lines.append("  Interpretation: Retail is accumulating (buying > selling).")
        elif avg_ratio < 0.9:
            lines.append("  Interpretation: Retail is distributing (selling > buying).")
        else:
            lines.append("  Interpretation: Retail buy/sell flow is roughly balanced.")

        return "\n".join(lines)
