# Indian Stock Market Analyzer

Automated system for identifying high-conviction stocks from the Indian stock market. Combines **technical**, **fundamental**, and **quantitative** analysis into a single conviction score (0-100) per stock.

## Features

- **16 scoring factors** across 3 analysis domains
- **Real-time dashboard** with filterable stock table
- **Candlestick charts** (TradingView lightweight-charts)
- **Sector heatmap** with aggregate scores
- **Historical score tracking** with trend visualization
- **Automated daily refresh** via APScheduler
- **Free data sources** — Yahoo Finance + NSE India

## Architecture

```
backend/   → Python FastAPI (REST API, scoring engine, scheduler)
frontend/  → React + Vite (dashboard with charts)
SQLite     → Local database (no external DB needed)
```

## Quick Start

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

Backend runs at http://localhost:8000 — API docs at http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at http://localhost:5173

### First Run

1. Start the backend
2. Hit `POST /api/refresh` (or click "Refresh Scores" in the dashboard) to fetch data and compute scores
3. Wait a few minutes for all stocks to be processed
4. View results in the dashboard

## Scoring Algorithm

| Domain | Weight | Factors |
|--------|--------|---------|
| Technical (40%) | RSI, MACD, Moving Averages, Bollinger Bands, ADX, Volume Breakout |
| Fundamental (35%) | PE Ratio, ROE, Debt/Equity, EPS Growth, Revenue Growth, Promoter Holding |
| Quantitative (25%) | Momentum, Mean Reversion, Relative Strength vs Nifty50, Sector Rotation |

Each factor produces a 0-100 sub-score. Weighted combination produces the final conviction score.

## API Endpoints

- `GET /api/stocks` — Filterable stock list with scores
- `GET /api/stocks/{symbol}` — Detailed stock info
- `GET /api/sectors` — Sector aggregates
- `GET /api/scores/top` — Top stocks by conviction
- `POST /api/refresh` — Trigger data refresh

## Tech Stack

**Backend:** FastAPI, yfinance, jugaad-data, pandas, ta (technical analysis), APScheduler, aiosqlite

**Frontend:** React 18, Vite, TailwindCSS, TanStack Query/Table, lightweight-charts, Recharts
