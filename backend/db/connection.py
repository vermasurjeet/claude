"""SQLite database connection and initialization."""

import aiosqlite
import os
from pathlib import Path

from backend.config import settings

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), settings.DB_PATH)
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


async def get_db() -> aiosqlite.Connection:
    """Get a database connection."""
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    return db


async def init_db():
    """Initialize database with schema."""
    schema = Path(SCHEMA_PATH).read_text()
    db = await get_db()
    try:
        await db.executescript(schema)
        await db.commit()
    finally:
        await db.close()


async def execute_query(query: str, params: tuple = (), fetch: str = "all"):
    """Execute a query and return results."""
    db = await get_db()
    try:
        cursor = await db.execute(query, params)
        if fetch == "all":
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        elif fetch == "one":
            row = await cursor.fetchone()
            return dict(row) if row else None
        else:
            await db.commit()
            return cursor.lastrowid
    finally:
        await db.close()


async def execute_many(query: str, data: list):
    """Execute a query with multiple parameter sets."""
    db = await get_db()
    try:
        await db.executemany(query, data)
        await db.commit()
    finally:
        await db.close()
