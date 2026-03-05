# 📊 NASDAQ + Grok Market Signal Generator

A Python tool that downloads **NASDAQ Data Link** data (retail trading activity + stock statistics), enriches it with real-time **X/Twitter sentiment** via the **Grok API** (x-search), and generates a polished HTML report with actionable trading signals.

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)

## How It Works

```
NASDAQ Data Link (RTAT + STAT)  ──┐
                                   ├──►  Grok AI Analysis  ──►  HTML Report
X/Twitter Sentiment (x-search)  ──┘
```

1. **Fetches RTAT data** — Retail Trading Activity Tracker (retail vs. institutional flow, sentiment scores)
2. **Fetches STAT data** — Stock statistics (market cap, P/E, 52-week range, volume, dividends)
3. **Grok + x-search** — Searches X/Twitter for real-time sentiment on each ticker, company news, and macro conditions
4. **Produces signals** — BUY / SELL / HOLD with confidence scores, reasoning, catalysts, and risks
5. **Generates HTML report** — Dark-themed, responsive report with summary table + detailed per-ticker cards

## Quick Start

### 1. Clone & Install

```bash
cd nasdaq
python3 -m venv .venv
source .venv/bin/activate   # macOS/Linux
# .venv\Scripts\activate    # Windows
pip install -r requirements.txt
```

### 2. Configure API Keys

```bash
cp .env.example .env
```

Edit `.env` and add your keys:

```env
NASDAQ_DATA_LINK_API_KEY=your_key_here
XAI_API_KEY=your_key_here
```

**Where to get keys:**
- NASDAQ Data Link: [data.nasdaq.com/account/profile](https://data.nasdaq.com/account/profile)
- xAI Grok: [console.x.ai](https://console.x.ai)

### 3. Configure Tickers

Edit `config/tickers.yaml` to set your watchlist:

```yaml
tickers:
  - symbol: AAPL
    name: Apple Inc.
  - symbol: MSFT
    name: Microsoft Corporation
  - symbol: TSLA
    name: Tesla Inc.
```

### 4. Run

```bash
source .venv/bin/activate   # if not already activated
python -m src.main
```

The report will auto-open in your browser.

## CLI Options

```bash
# Analyze specific tickers (overrides config)
python -m src.main --tickers AAPL,MSFT,TSLA

# Don't auto-open browser
python -m src.main --no-browser

# Combine options
python -m src.main --tickers NVDA,AMD --no-browser
```

## Project Structure

```
nasdaq/
├── config/
│   ├── tickers.yaml          # Your watchlist
│   └── settings.yaml         # API and report settings
├── src/
│   ├── main.py               # CLI entry point
│   ├── data_fetcher.py       # NASDAQ Data Link client (RTAT + STAT)
│   ├── grok_analyzer.py      # Grok API client with x-search
│   ├── signal_engine.py      # Orchestrator: data → analysis → signals
│   ├── report_generator.py   # HTML report generator (Jinja2)
│   └── models.py             # Data models (TickerSignal, MarketReport, etc.)
├── templates/
│   └── report.html           # Jinja2 HTML template
├── output/                   # Generated reports
├── requirements.txt
├── .env.example
└── README.md
```

## Configuration

### `config/settings.yaml`

| Setting | Default | Description |
|---------|---------|-------------|
| `nasdaq.rtat_table` | `NDAQ/RTAT` | RTAT table (use `NDAQ/RTAT10` for free top-10) |
| `nasdaq.stat_table` | `NDAQ/STAT` | STAT table |
| `nasdaq.rtat_lookback_days` | `30` | Days of RTAT history to fetch |
| `grok.model` | `grok-4-1-fast-reasoning` | Grok model to use |
| `grok.temperature` | `0.3` | Lower = more deterministic |
| `grok.x_search_enabled` | `true` | Enable X/Twitter search |
| `grok.x_search_lookback_days` | `7` | X search date window |
| `report.open_browser` | `true` | Auto-open report on completion |

## NASDAQ Datasets Used

### NDAQ/RTAT — Retail Trading Activity Tracker
- Tracks retail trading activity across 9,500+ US-listed securities
- **`activity`**: Share of total retail USD volume (0–1)
- **`sentiment`**: Net flow score over 10 days (−100 sell-heavy to +100 buy-heavy)

### NDAQ/STAT — Stock Statistics (E360)
- Daily fundamental snapshot per ticker
- Market cap, 52-week high/low, P/E, EPS, P/B, dividend yield, volume averages, free float

## Report Output

The HTML report includes:

- **🌍 Market Overview** — Broad sentiment, sector highlights, upcoming events
- **📋 Summary Table** — All tickers at a glance with signal badges + confidence bars
- **📊 Detailed Ticker Cards** — Per-ticker breakdown:
  - Retail flow analysis (RTAT)
  - Fundamental statistics (STAT)
  - X/Twitter sentiment (via Grok x-search)
  - Catalysts & risks
  - Recommended action

## ⚠️ Disclaimer

This tool is for **informational purposes only**. It does not constitute financial advice, investment recommendations, or solicitation to buy or sell securities. Always conduct your own research and consult a qualified financial advisor before making investment decisions. Past performance does not guarantee future results. Trading involves risk of loss.
