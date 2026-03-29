-- Stock master data
CREATE TABLE IF NOT EXISTS stocks (
    symbol          TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    sector          TEXT,
    industry        TEXT,
    yahoo_symbol    TEXT NOT NULL,
    market_cap      REAL,
    exchange        TEXT DEFAULT 'NSE',
    is_active       INTEGER DEFAULT 1,
    updated_at      TEXT
);

-- Daily OHLCV cache
CREATE TABLE IF NOT EXISTS price_history (
    symbol          TEXT NOT NULL,
    date            TEXT NOT NULL,
    open            REAL,
    high            REAL,
    low             REAL,
    close           REAL,
    volume          INTEGER,
    delivery_pct    REAL,
    PRIMARY KEY (symbol, date),
    FOREIGN KEY (symbol) REFERENCES stocks(symbol)
);

-- Conviction scores
CREATE TABLE IF NOT EXISTS scores (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol          TEXT NOT NULL,
    computed_at     TEXT NOT NULL,
    total_score     REAL NOT NULL,
    technical_score REAL,
    fundamental_score REAL,
    quant_score     REAL,
    details_json    TEXT,
    FOREIGN KEY (symbol) REFERENCES stocks(symbol)
);

-- Fundamental data cache
CREATE TABLE IF NOT EXISTS fundamentals (
    symbol          TEXT PRIMARY KEY,
    pe_ratio        REAL,
    pb_ratio        REAL,
    roe             REAL,
    debt_to_equity  REAL,
    eps_growth      REAL,
    revenue_growth  REAL,
    promoter_holding REAL,
    market_cap      REAL,
    dividend_yield  REAL,
    info_json       TEXT,
    fetched_at      TEXT NOT NULL,
    FOREIGN KEY (symbol) REFERENCES stocks(symbol)
);

-- Sector aggregate scores
CREATE TABLE IF NOT EXISTS sector_scores (
    sector          TEXT,
    date            TEXT,
    avg_score       REAL,
    top_symbol      TEXT,
    top_score       REAL,
    stock_count     INTEGER,
    PRIMARY KEY (sector, date)
);

-- FII/DII daily data
CREATE TABLE IF NOT EXISTS fii_dii (
    date            TEXT PRIMARY KEY,
    fii_buy         REAL,
    fii_sell        REAL,
    dii_buy         REAL,
    dii_sell        REAL
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_scores_symbol_date ON scores(symbol, computed_at);
CREATE INDEX IF NOT EXISTS idx_scores_total ON scores(total_score DESC);
CREATE INDEX IF NOT EXISTS idx_price_symbol_date ON price_history(symbol, date DESC);
CREATE INDEX IF NOT EXISTS idx_stocks_sector ON stocks(sector);
