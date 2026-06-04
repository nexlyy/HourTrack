from __future__ import annotations

from pathlib import Path

import aiosqlite

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    telegram_id   INTEGER PRIMARY KEY,
    hourly_rate   TEXT NOT NULL DEFAULT '0',
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS shifts (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id   INTEGER NOT NULL,
    start_time    TEXT NOT NULL,
    end_time      TEXT NOT NULL,
    hours         TEXT NOT NULL,
    is_manual     INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (telegram_id) REFERENCES users(telegram_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_shifts_user_start
    ON shifts(telegram_id, start_time);

CREATE TABLE IF NOT EXISTS active_shifts (
    telegram_id   INTEGER PRIMARY KEY,
    start_time    TEXT NOT NULL,
    FOREIGN KEY (telegram_id) REFERENCES users(telegram_id) ON DELETE CASCADE
);
"""


class Database:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._conn: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(self._path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA foreign_keys = ON")
        await self._conn.execute("PRAGMA journal_mode = WAL")
        await self._conn.executescript(SCHEMA)
        await self._conn.commit()

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

    @property
    def connection(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError("Database is not connected")
        return self._conn
