"""
xAI Grok market analyzer — official xai-sdk with x_search & web_search.

Uses the official ``xai-sdk`` Python package following the patterns from
https://github.com/xai-org/xai-sdk-python/blob/main/examples/sync/server_side_tools.py

Key SDK calls:
  client = Client(api_key=...)
  chat   = client.chat.create(model=..., tools=[x_search(), web_search()])
  chat.append(system(...))
  chat.append(user(...))
  response = chat.sample()          # non-streaming
  response.content                  # assistant text
  response.citations                # list[str] of all source URLs
"""

from __future__ import annotations

import json
import re
from datetime import datetime

from xai_sdk import Client
from xai_sdk.chat import system, user
from xai_sdk.tools import web_search, x_search
from rich.console import Console

from .models import MarketOverview, TickerSignal, XSource

console = Console()

# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------

TICKER_ANALYSIS_SYSTEM_PROMPT = """\
You are an expert market analyst with deep knowledge of equities, ETFs, \
macroeconomics, and retail trading dynamics. You have access to real-time \
X/Twitter data via search tools.

Your job is to analyze the provided NASDAQ trading data (RTAT retail activity \
+ STAT stock statistics) alongside current market sentiment from X to produce \
an actionable trading signal.

You MUST return your analysis as valid JSON with this exact schema:
{
  "signal": "BUY" | "SELL" | "HOLD",
  "sentiment": <float -1.0 to 1.0>,
  "sentiment_confidence": <float 0.0 to 1.0>,
  "retail_flow_summary": "<2-4 sentence RTAT analysis>",
  "stat_summary": "<2-4 sentence STAT analysis>",
  "x_sentiment": "<2-4 sentence summary of X/Twitter sentiment>",
  "catalysts": ["<catalyst 1>", "<catalyst 2>", ...],
  "risks": ["<risk 1>", "<risk 2>", ...],
  "reasoning": "<comprehensive 3-5 sentence reasoning>",
  "recommended_action": "<specific actionable recommendation>"
}

Guidelines:
- Use the RTAT sentiment score (-100 to +100) to gauge retail conviction.
- Use STAT fundamentals (P/E, market cap, 52-week range) for valuation context.
- Search X for: $TICKER mentions, company news, analyst opinions, sector trends.
- Be specific in your recommendation (e.g., "Accumulate below $180", not just "Buy").
- "sentiment" is a float from -1.0 (extremely bearish) to 1.0 (extremely bullish), \
  representing your assessment of overall market/social sentiment for this ticker \
  based on X/Twitter posts, news flow, and retail activity. 0.0 = perfectly neutral.
- "sentiment_confidence" is a float from 0.0 to 1.0 representing how confident you \
  are in your sentiment score. 0.0 = no confidence (highly conflicting/insufficient signals), \
  1.0 = very high confidence (clear consensus sentiment with strong evidence).
- Always disclose uncertainty honestly.
- Return ONLY valid JSON, no markdown fences or extra text.
"""

MARKET_OVERVIEW_SYSTEM_PROMPT = """\
You are an expert macro-market analyst. You have access to real-time X/Twitter \
data via search tools.

Provide a comprehensive market overview by searching X for:
1. Broad market sentiment (S&P 500, NASDAQ, Dow Jones trends)
2. Federal Reserve / interest rate chatter
3. Macroeconomic indicators and concerns
4. Sector rotation themes
5. Upcoming catalysts (earnings season, FOMC, economic releases)
6. Geopolitical risks affecting markets

Return your analysis as valid JSON with this exact schema:
{
  "overall_sentiment": "BULLISH" | "BEARISH" | "NEUTRAL",
  "macro_summary": "<4-6 sentence overview of macro conditions>",
  "sector_highlights": {
    "Technology": "<1-2 sentence sentiment>",
    "Healthcare": "<1-2 sentence sentiment>",
    "Financials": "<1-2 sentence sentiment>",
    "Energy": "<1-2 sentence sentiment>",
    "Consumer": "<1-2 sentence sentiment>"
  },
  "key_events": ["<upcoming event 1>", "<upcoming event 2>", ...]
}

Return ONLY valid JSON, no markdown fences or extra text.
"""


class GrokAnalyzer:
    """Analyzes tickers via the official xai-sdk with x_search + web_search."""

    def __init__(self, api_key: str, settings: dict) -> None:
        self.client = Client(api_key=api_key)
        self.model = settings.get("model", "grok-4-1-fast-reasoning")
        self.temperature = settings.get("temperature", 0.3)
        self.x_search_enabled = settings.get("x_search_enabled", True)

    # ------------------------------------------------------------------
    # Core call — create a fresh chat, append messages, sample response
    # ------------------------------------------------------------------
    def _call_grok(
        self, system_prompt: str, user_message: str
    ) -> tuple[str, list[XSource]]:
        """Send a request via xai-sdk and return (text, x_sources).

        Creates a new ``chat`` for each call, appends system + user
        messages, enables server-side tools (x_search, web_search),
        then calls ``chat.sample()`` for a non-streaming response.

        Returns
        -------
        tuple[str, list[XSource]]
            The assistant text and all X-post citations collected
            from ``response.citations``.
        """
        # Build the tools list
        tools = []
        if self.x_search_enabled:
            tools.append(x_search())
            tools.append(web_search())

        # Create a fresh chat session with tools attached
        chat = self.client.chat.create(
            model=self.model,
            temperature=self.temperature,
            tools=tools if tools else None,
        )
        chat.append(system(system_prompt))
        chat.append(user(user_message))

        # Non-streaming sample — blocks until Grok finishes tool calls
        # and produces the final response.
        response = chat.sample()

        # Extract X-post sources from response.citations
        citations: list[str] = response.citations or []
        x_sources = self._extract_x_sources(citations)

        return response.content, x_sources

    # ------------------------------------------------------------------
    # Extract X-post sources from citations
    # ------------------------------------------------------------------
    _X_URL_RE = re.compile(r"https?://(?:www\.)?(?:x|twitter)\.com/")

    @classmethod
    def _extract_x_sources(cls, citations: list[str]) -> list[XSource]:
        """Filter citations to only X/Twitter post URLs, deduplicate."""
        seen: set[str] = set()
        sources: list[XSource] = []

        for url in citations:
            if not cls._X_URL_RE.match(url) or url in seen:
                continue
            seen.add(url)
            handle = XSource.handle_from_url(url)
            sources.append(XSource(url=url, handle=handle))

        return sources

    # ------------------------------------------------------------------
    # Parse JSON from Grok response (handles markdown fences, etc.)
    # ------------------------------------------------------------------
    @staticmethod
    def _parse_json(text: str) -> dict:
        """Extract and parse JSON from Grok's response."""
        cleaned = text.strip()
        # Strip markdown code fences if present
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            cleaned = "\n".join(lines)

        return json.loads(cleaned)

    # ------------------------------------------------------------------
    # Analyze a single ticker
    # ------------------------------------------------------------------
    def analyze_ticker(
        self, ticker: str, name: str, nasdaq_data: dict
    ) -> TickerSignal:
        """Analyze a ticker using NASDAQ data + Grok x-search + web-search."""
        console.print(
            f"  🤖 Analyzing [bold cyan]{ticker}[/bold cyan] with Grok + x-search…"
        )

        user_message = (
            f"Analyze {ticker} ({name}) for a trading signal.\n\n"
            f"=== NASDAQ RTAT DATA (Retail Trading Activity) ===\n"
            f"{nasdaq_data['rtat_summary']}\n\n"
            f"=== NASDAQ STAT DATA (Stock Statistics) ===\n"
            f"{nasdaq_data['stat_summary']}\n\n"
            f"=== NASDAQ UREF DATA (Intraday Retail Buy/Sell Flow) ===\n"
            f"{nasdaq_data['uref_summary']}\n\n"
            f"Search X/Twitter for current sentiment on ${ticker}, {name}, "
            f"and any recent news or catalysts. Then combine the NASDAQ data "
            f"with X sentiment to produce your trading signal as JSON."
        )

        try:
            raw, x_sources = self._call_grok(
                TICKER_ANALYSIS_SYSTEM_PROMPT, user_message
            )
            data = self._parse_json(raw)
            console.print(
                f"    ↳ {len(x_sources)} X source(s) collected for {ticker}"
            )

            return TickerSignal(
                symbol=ticker,
                name=name,
                signal=data.get("signal", "HOLD").upper(),
                confidence=int(data.get("confidence", 5)),
                sentiment=float(data.get("sentiment", 0.0)),
                sentiment_confidence=float(data.get("sentiment_confidence", 0.5)),
                retail_flow_summary=data.get("retail_flow_summary", ""),
                stat_summary=data.get("stat_summary", ""),
                x_sentiment=data.get("x_sentiment", ""),
                catalysts=data.get("catalysts", []),
                risks=data.get("risks", []),
                reasoning=data.get("reasoning", ""),
                recommended_action=data.get("recommended_action", ""),
                x_sources=x_sources,
            )
        except json.JSONDecodeError as exc:
            console.print(
                f"  [red]✗ Failed to parse Grok JSON for {ticker}: {exc}[/red]"
            )
            return self._fallback_signal(ticker, name, f"JSON parse error: {exc}")
        except Exception as exc:
            console.print(
                f"  [red]✗ Grok analysis failed for {ticker}: {exc}[/red]"
            )
            return self._fallback_signal(ticker, name, str(exc))

    # ------------------------------------------------------------------
    # Market overview
    # ------------------------------------------------------------------
    def get_market_overview(self) -> MarketOverview:
        """Get broad market sentiment via Grok + x-search + web-search."""
        console.print("  🌍 Fetching market overview via Grok + x-search…")

        user_message = (
            "Provide a comprehensive market overview for today. "
            "Search X/Twitter for current broad market sentiment, "
            "Federal Reserve commentary, macro indicators, sector trends, "
            "and any upcoming market-moving events. Return as JSON."
        )

        try:
            raw, x_sources = self._call_grok(
                MARKET_OVERVIEW_SYSTEM_PROMPT, user_message
            )
            data = self._parse_json(raw)
            console.print(
                f"    ↳ {len(x_sources)} X source(s) for market overview"
            )

            return MarketOverview(
                overall_sentiment=data.get("overall_sentiment", "NEUTRAL").upper(),
                macro_summary=data.get("macro_summary", ""),
                sector_highlights=data.get("sector_highlights", {}),
                key_events=data.get("key_events", []),
                x_sources=x_sources,
            )
        except Exception as exc:
            console.print(f"  [red]✗ Market overview failed: {exc}[/red]")
            return MarketOverview(
                overall_sentiment="NEUTRAL",
                macro_summary=f"Unable to fetch market overview: {exc}",
            )

    # ------------------------------------------------------------------
    # Fallback signal on error
    # ------------------------------------------------------------------
    @staticmethod
    def _fallback_signal(ticker: str, name: str, error: str) -> TickerSignal:
        return TickerSignal(
            symbol=ticker,
            name=name,
            signal="HOLD",
            confidence=1,
            sentiment=0.0,
            sentiment_confidence=0.0,
            retail_flow_summary="Analysis unavailable.",
            stat_summary="Analysis unavailable.",
            x_sentiment="Analysis unavailable.",
            reasoning=f"Analysis could not be completed: {error}",
            recommended_action="No recommendation — review manually.",
        )
