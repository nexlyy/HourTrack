from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from .db import Database


@dataclass(frozen=True)
class Shift:
    id: int
    telegram_id: int
    start_time: datetime
    end_time: datetime
    hours: Decimal
    is_manual: bool


@dataclass(frozen=True)
class ActiveShift:
    telegram_id: int
    start_time: datetime


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _fmt_dt(value: datetime) -> str:
    return value.isoformat()


class UserRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    async def ensure_user(self, telegram_id: int) -> None:
        await self._db.connection.execute(
            "INSERT OR IGNORE INTO users (telegram_id) VALUES (?)",
            (telegram_id,),
        )
        await self._db.connection.commit()

    async def get_hourly_rate(self, telegram_id: int) -> Decimal:
        async with self._db.connection.execute(
            "SELECT hourly_rate FROM users WHERE telegram_id = ?",
            (telegram_id,),
        ) as cursor:
            row = await cursor.fetchone()
        if row is None:
            return Decimal("0")
        return Decimal(row["hourly_rate"])

    async def set_hourly_rate(self, telegram_id: int, rate: Decimal) -> None:
        await self.ensure_user(telegram_id)
        await self._db.connection.execute(
            "UPDATE users SET hourly_rate = ? WHERE telegram_id = ?",
            (str(rate), telegram_id),
        )
        await self._db.connection.commit()


class ShiftRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    async def add_shift(
        self,
        telegram_id: int,
        start_time: datetime,
        end_time: datetime,
        hours: Decimal,
        is_manual: bool,
    ) -> int:
        cursor = await self._db.connection.execute(
            """
            INSERT INTO shifts (telegram_id, start_time, end_time, hours, is_manual)
            VALUES (?, ?, ?, ?, ?)
            """,
            (telegram_id, _fmt_dt(start_time), _fmt_dt(end_time), str(hours), int(is_manual)),
        )
        await self._db.connection.commit()
        return cursor.lastrowid or 0

    async def list_in_range(
        self,
        telegram_id: int,
        start: datetime,
        end: datetime,
    ) -> list[Shift]:
        async with self._db.connection.execute(
            """
            SELECT id, telegram_id, start_time, end_time, hours, is_manual
            FROM shifts
            WHERE telegram_id = ? AND start_time >= ? AND start_time < ?
            ORDER BY start_time ASC
            """,
            (telegram_id, _fmt_dt(start), _fmt_dt(end)),
        ) as cursor:
            rows = await cursor.fetchall()
        return [
            Shift(
                id=row["id"],
                telegram_id=row["telegram_id"],
                start_time=_parse_dt(row["start_time"]),
                end_time=_parse_dt(row["end_time"]),
                hours=Decimal(row["hours"]),
                is_manual=bool(row["is_manual"]),
            )
            for row in rows
        ]


class ActiveShiftRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    async def get(self, telegram_id: int) -> ActiveShift | None:
        async with self._db.connection.execute(
            "SELECT telegram_id, start_time FROM active_shifts WHERE telegram_id = ?",
            (telegram_id,),
        ) as cursor:
            row = await cursor.fetchone()
        if row is None:
            return None
        return ActiveShift(
            telegram_id=row["telegram_id"],
            start_time=_parse_dt(row["start_time"]),
        )

    async def start(self, telegram_id: int, start_time: datetime) -> None:
        await self._db.connection.execute(
            """
            INSERT INTO active_shifts (telegram_id, start_time)
            VALUES (?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET start_time = excluded.start_time
            """,
            (telegram_id, _fmt_dt(start_time)),
        )
        await self._db.connection.commit()

    async def finish(self, telegram_id: int) -> None:
        await self._db.connection.execute(
            "DELETE FROM active_shifts WHERE telegram_id = ?",
            (telegram_id,),
        )
        await self._db.connection.commit()
