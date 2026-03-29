"""Application configuration using Pydantic Settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DB_PATH: str = "stock_analyzer.db"

    # Stock universe
    STOCK_UNIVERSE: str = "NIFTY50"  # NIFTY50 or NIFTY500

    # Scoring weights (must sum to 1.0)
    WEIGHT_TECHNICAL: float = 0.40
    WEIGHT_FUNDAMENTAL: float = 0.35
    WEIGHT_QUANTITATIVE: float = 0.25

    # Technical indicator weights (must sum to 1.0)
    W_RSI: float = 0.20
    W_MACD: float = 0.20
    W_MOVING_AVG: float = 0.20
    W_BOLLINGER: float = 0.15
    W_ADX: float = 0.15
    W_VOLUME: float = 0.10

    # Fundamental indicator weights (must sum to 1.0)
    W_PE: float = 0.20
    W_ROE: float = 0.20
    W_DEBT_EQUITY: float = 0.15
    W_EPS_GROWTH: float = 0.20
    W_REVENUE_GROWTH: float = 0.15
    W_PROMOTER: float = 0.10

    # Quantitative indicator weights (must sum to 1.0)
    W_MOMENTUM: float = 0.30
    W_MEAN_REVERSION: float = 0.25
    W_RELATIVE_STRENGTH: float = 0.25
    W_SECTOR_ROTATION: float = 0.20

    # Data fetching
    YAHOO_RATE_LIMIT_SECONDS: float = 0.5
    YAHOO_BATCH_SIZE: int = 50
    OHLCV_PERIOD: str = "1y"

    # Scheduler
    REFRESH_HOUR: int = 18  # 6 PM IST
    REFRESH_MINUTE: int = 0

    # API
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    model_config = {"env_prefix": "STOCK_", "env_file": ".env"}


settings = Settings()
