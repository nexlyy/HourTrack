from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from zoneinfo import ZoneInfo

from ..database.queries import Shift, ShiftRepository, UserRepository
from ..utils.datetime_helpers import (
    days_until_payout,
    payout_date_for_period,
    period_bounds,
    previous_period_bounds,
)


@dataclass(frozen=True)
class PeriodSummary:
    period_start: datetime
    period_end: datetime
    payout_date: datetime
    days_to_payout: int
    shifts_count: int
    total_hours: Decimal
    hourly_rate: Decimal
    earned: Decimal
    forecast: Decimal


def _sum_hours(shifts: list[Shift]) -> Decimal:
    total = sum((shift.hours for shift in shifts), Decimal("0"))
    return Decimal(total).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class PayrollService:
    def __init__(
        self,
        users: UserRepository,
        shifts: ShiftRepository,
        tz: ZoneInfo,
    ) -> None:
        self._users = users
        self._shifts = shifts
        self._tz = tz

    async def current_period(self, telegram_id: int, reference: datetime) -> PeriodSummary:
        start, end = period_bounds(reference, self._tz)
        return await self._build_summary(telegram_id, reference, start, end, forecast=True)

    async def previous_period(self, telegram_id: int, reference: datetime) -> PeriodSummary:
        start, end = previous_period_bounds(reference, self._tz)
        return await self._build_summary(telegram_id, reference, start, end, forecast=False)

    async def _build_summary(
        self,
        telegram_id: int,
        reference: datetime,
        start: datetime,
        end: datetime,
        forecast: bool,
    ) -> PeriodSummary:
        rate = await self._users.get_hourly_rate(telegram_id)
        shifts = await self._shifts.list_in_range(telegram_id, start, end)
        total_hours = _sum_hours(shifts)
        earned = _money(total_hours * rate)
        payout = payout_date_for_period(start, self._tz)
        days_left = days_until_payout(reference, self._tz) if forecast else 0

        forecast_value = earned
        if forecast and total_hours > 0:
            days_passed = max(1, (min(reference, end) - start).days + 1)
            total_days = (end - start).days
            average_per_day = total_hours / Decimal(days_passed)
            projected_hours = average_per_day * Decimal(total_days)
            forecast_value = _money(projected_hours * rate)

        return PeriodSummary(
            period_start=start,
            period_end=end,
            payout_date=payout,
            days_to_payout=days_left,
            shifts_count=len(shifts),
            total_hours=total_hours,
            hourly_rate=rate,
            earned=earned,
            forecast=forecast_value,
        )

    async def list_shifts(
        self,
        telegram_id: int,
        start: datetime,
        end: datetime,
    ) -> list[Shift]:
        return await self._shifts.list_in_range(telegram_id, start, end)
