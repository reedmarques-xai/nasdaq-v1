"""FastAPI backend — exposes the signal engine via REST + SSE."""

from __future__ import annotations

import json
import os
from pathlib import Path

import yaml
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from .data_fetcher import NasdaqDataFetcher
from .grok_analyzer import GrokAnalyzer
from .signal_engine import SignalEngine

load_dotenv()

app = FastAPI(title="Market Signal Generator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------
_CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


def _load_settings() -> dict:
    with open(_CONFIG_DIR / "settings.yaml") as f:
        return yaml.safe_load(f)


def _load_tickers() -> list[dict]:
    with open(_CONFIG_DIR / "tickers.yaml") as f:
        return yaml.safe_load(f).get("tickers", [])


def _save_tickers(tickers: list[dict]) -> None:
    with open(_CONFIG_DIR / "tickers.yaml", "w") as f:
        yaml.dump({"tickers": tickers}, f, default_flow_style=False)


# ---------------------------------------------------------------------------
# Pydantic models for request / response
# ---------------------------------------------------------------------------
class Ticker(BaseModel):
    symbol: str
    name: str


class TickerList(BaseModel):
    tickers: list[Ticker]


class AnalyzeRequest(BaseModel):
    tickers: list[Ticker] | None = None  # override; None = use config


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/api/tickers")
def get_tickers() -> dict:
    return {"tickers": _load_tickers()}


@app.put("/api/tickers")
def update_tickers(body: TickerList) -> dict:
    tickers = [t.model_dump() for t in body.tickers]
    _save_tickers(tickers)
    return {"tickers": tickers}


@app.post("/api/analyze")
async def analyze(body: AnalyzeRequest | None = None):
    """Stream analysis results via Server-Sent Events."""
    nasdaq_key = os.getenv("NASDAQ_DATA_LINK_API_KEY")
    xai_key = os.getenv("XAI_API_KEY")

    if not nasdaq_key or not xai_key:
        raise HTTPException(status_code=500, detail="API keys not configured in .env")

    settings = _load_settings()
    tickers = (
        [t.model_dump() for t in body.tickers]
        if body and body.tickers
        else _load_tickers()
    )

    if not tickers:
        raise HTTPException(status_code=400, detail="No tickers configured")

    fetcher = NasdaqDataFetcher(api_key=nasdaq_key, settings=settings.get("nasdaq", {}))
    analyzer = GrokAnalyzer(api_key=xai_key, settings=settings.get("grok", {}))
    engine = SignalEngine(data_fetcher=fetcher, grok_analyzer=analyzer)

    def event_stream():
        for evt in engine.generate_report_stream(tickers):
            yield {
                "event": evt["event"],
                "data": json.dumps(evt["data"]),
            }

    return EventSourceResponse(event_stream())
