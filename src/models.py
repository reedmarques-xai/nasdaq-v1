"""Data models for the Market Signal Generator."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class XSource:
    """A single X/Twitter post used as a source by Grok's x_search."""

    url: str  # Full X post URL, e.g. https://x.com/elonmusk/status/123
    handle: str = ""  # @handle extracted from URL (e.g. "elonmusk")
    title: str = ""  # Citation title/label from the API (e.g. "1")

    # Regex to pull the @handle from an X URL path
    _HANDLE_RE = re.compile(
        r"https?://(?:www\.)?(?:x|twitter)\.com/([A-Za-z0-9_]+)"
    )

    @classmethod
    def handle_from_url(cls, url: str) -> str:
        """Extract the @handle from an X/Twitter URL."""
        m = cls._HANDLE_RE.match(url)
        if m and m.group(1).lower() not in ("i", "search", "hashtag"):
            return m.group(1)
        return ""

    @property
    def display_label(self) -> str:
        """Human-friendly label for display in the report."""
        if self.handle:
            return f"@{self.handle}"
        return self.url


@dataclass
class TickerSignal:
    """Analysis signal for a single ticker."""

    symbol: str
    name: str
    signal: str  # BUY / SELL / HOLD
    confidence: int  # 1-10
    sentiment: float  # -1.0 (very bearish) to 1.0 (very bullish)
    sentiment_confidence: float  # 0.0 to 1.0 how confident Grok is in the sentiment
    retail_flow_summary: str  # RTAT analysis
    stat_summary: str  # STAT analysis
    x_sentiment: str  # X/Twitter sentiment from Grok x-search
    catalysts: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    reasoning: str = ""
    recommended_action: str = ""
    x_sources: list[XSource] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class MarketOverview:
    """Broad market sentiment overview from Grok x-search."""

    overall_sentiment: str  # BULLISH / BEARISH / NEUTRAL
    macro_summary: str  # Fed, rates, economic outlook
    sector_highlights: dict[str, str] = field(default_factory=dict)
    key_events: list[str] = field(default_factory=list)
    x_sources: list[XSource] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class MarketReport:
    """Complete market report with overview + per-ticker signals."""

    overview: MarketOverview
    signals: list[TickerSignal] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)

    @property
    def buy_signals(self) -> list[TickerSignal]:
        return [s for s in self.signals if s.signal == "BUY"]

    @property
    def sell_signals(self) -> list[TickerSignal]:
        return [s for s in self.signals if s.signal == "SELL"]

    @property
    def hold_signals(self) -> list[TickerSignal]:
        return [s for s in self.signals if s.signal == "HOLD"]

    @property
    def total_x_sources(self) -> int:
        """Total unique X sources across the entire report."""
        urls: set[str] = {s.url for s in self.overview.x_sources}
        for sig in self.signals:
            urls.update(s.url for s in sig.x_sources)
        return len(urls)
