from __future__ import annotations

import calendar
from datetime import date, datetime, time, timedelta
from decimal import Decimal, ROUND_HALF_UP
from zoneinfo import ZoneInfo

DATE_FORMATS = ("%d.%m.%Y", "%d.%m.%y", "%d/%m/%Y", "%Y-%m-%d")
RELATIVE_TOKENS = {
    "сегодня": 0,
    "вчера": -1,
    "позавчера": -2,
}


def now(tz: ZoneInfo) -> datetime:
    return datetime.now(tz)


def period_bounds(reference: datetime, tz: ZoneInfo) -> tuple[datetime, datetime]:
    start = datetime.combine(reference.date().replace(day=1), time.min, tzinfo=tz)
    last_day = calendar.monthrange(reference.year, reference.month)[1]
    next_month_first = datetime.combine(
        date(reference.year, reference.month, last_day) + timedelta(days=1),
        time.min,
        tzinfo=tz,
    )
    return start, next_month_first


def previous_period_bounds(reference: datetime, tz: ZoneInfo) -> tuple[datetime, datetime]:
    current_start, _ = period_bounds(reference, tz)
    prev_end = current_start
    prev_reference = current_start - timedelta(days=1)
    prev_start, _ = period_bounds(prev_reference.astimezone(tz), tz)
    return prev_start, prev_end


def payout_date_for_period(period_start: datetime, tz: ZoneInfo) -> datetime:
    if period_start.month == 12:
        payout = datetime(period_start.year + 1, 1, 10, tzinfo=tz)
    else:
        payout = datetime(period_start.year, period_start.month + 1, 10, tzinfo=tz)
    return payout


def days_until_payout(reference: datetime, tz: ZoneInfo) -> int:
    period_start, _ = period_bounds(reference, tz)
    payout = payout_date_for_period(period_start, tz)
    delta = payout.date() - reference.date()
    return delta.days


def parse_user_date(raw: str, tz: ZoneInfo) -> date | None:
    cleaned = raw.strip().lower()
    if cleaned in RELATIVE_TOKENS:
        return (now(tz).date() + timedelta(days=RELATIVE_TOKENS[cleaned]))
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue
    return None


def parse_hours(raw: str) -> Decimal | None:
    cleaned = raw.strip().replace(",", ".").replace(" ", "")
    if not cleaned:
        return None
    try:
        value = Decimal(cleaned)
    except (ArithmeticError, ValueError):
        return None
    if value <= 0 or value > Decimal("24"):
        return None
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def parse_rate(raw: str) -> Decimal | None:
    cleaned = raw.strip().replace(",", ".").replace(" ", "")
    if not cleaned:
        return None
    try:
        value = Decimal(cleaned)
    except (ArithmeticError, ValueError):
        return None
    if value <= 0 or value > Decimal("10000"):
        return None
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def hours_between(start: datetime, end: datetime) -> Decimal:
    seconds = Decimal((end - start).total_seconds())
    return seconds / Decimal("3600")


def format_money(amount: Decimal, currency: str) -> str:
    quantized = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{quantized} {currency}"


def format_hours(value: Decimal) -> str:
    return f"{value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)} ч"


def format_duration(value: Decimal) -> str:
    total_minutes = int((value * Decimal("60")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    hours_part = total_minutes // 60
    minutes_part = total_minutes % 60
    quantized_hours = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if hours_part == 0:
        return f"{minutes_part} мин ({quantized_hours} ч)"
    if minutes_part == 0:
        return f"{hours_part} ч"
    return f"{hours_part} ч {minutes_part} мин ({quantized_hours} ч)"


def format_datetime(value: datetime, tz: ZoneInfo) -> str:
    return value.astimezone(tz).strftime("%d.%m.%Y %H:%M")


def format_date(value: date) -> str:
    return value.strftime("%d.%m.%Y")


def midnight(value: date, tz: ZoneInfo) -> datetime:
    return datetime.combine(value, time.min, tzinfo=tz)


MONTH_NAMES_RU = {
    1: "Январь",
    2: "Февраль",
    3: "Март",
    4: "Апрель",
    5: "Май",
    6: "Июнь",
    7: "Июль",
    8: "Август",
    9: "Сентябрь",
    10: "Октябрь",
    11: "Ноябрь",
    12: "Декабрь",
}


def format_month_year_ru(value: datetime) -> str:
    return f"{MONTH_NAMES_RU[value.month]} {value.year}"
