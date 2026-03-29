"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.db.connection import init_db
from backend.data.universe import populate_stock_universe
from backend.scheduler import start_scheduler, stop_scheduler
from backend.routers import stocks, sectors, scores, config_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: init DB, populate universe, start scheduler."""
    logger.info("Starting Stock Analyzer...")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Populate stock universe
    count = await populate_stock_universe()
    logger.info(f"Stock universe populated: {count} stocks")

    # Start scheduler
    start_scheduler()

    yield

    # Shutdown
    stop_scheduler()
    logger.info("Stock Analyzer stopped")


app = FastAPI(
    title="Indian Stock Market Analyzer",
    description="Automated high-conviction stock identification system",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(stocks.router)
app.include_router(sectors.router)
app.include_router(scores.router)
app.include_router(config_router.router)


@app.get("/")
async def root():
    return {
        "name": "Indian Stock Market Analyzer",
        "version": "1.0.0",
        "docs": "/docs",
    }
