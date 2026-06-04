from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from aiogram import F, Router
from aiogram.types import FSInputFile, Message

from ..database.queries import ActiveShiftRepository
from ..keyboards.reply import (
    BTN_STATS,
    BTN_STATS_CHART,
    BTN_STATS_CURRENT,
    BTN_STATS_PREVIOUS,
    main_menu,
    stats_menu,
)
from ..services.charts import ChartService
from ..services.payroll import PayrollService, PeriodSummary
from ..utils.datetime_helpers import (
    format_hours,
    format_money,
    format_month_year_ru,
    now,
    period_bounds,
)

router = Router(name="stats")


def _format_summary(summary: PeriodSummary, title: str) -> str:
    period_end_inclusive = summary.period_end - timedelta(seconds=1)
    lines = [
        title,
        "",
        f"Период: {summary.period_start.strftime('%d.%m.%Y')} — "
        f"{period_end_inclusive.strftime('%d.%m.%Y')}",
        f"Смен: {summary.shifts_count}",
        f"Часов: {format_hours(summary.total_hours)}",
        f"Заработано: {format_money(summary.earned, 'PLN')}",
        f"Ставка: {format_money(summary.hourly_rate, 'PLN')}/ч",
    ]
    return "\n".join(lines)


@router.message(F.text == BTN_STATS)
async def handle_stats_menu(message: Message) -> None:
    await message.answer("Раздел статистики", reply_markup=stats_menu())


@router.message(F.text == BTN_STATS_CURRENT)
async def handle_current_stats(
    message: Message,
    tz: ZoneInfo,
    payroll: PayrollService,
    profile_id: int,
) -> None:
    summary = await payroll.current_period(profile_id, now(tz))
    extra = await _detailed_block(payroll, profile_id, summary)
    await message.answer(_format_summary(summary, "📊 Текущий период") + extra)


@router.message(F.text == BTN_STATS_PREVIOUS)
async def handle_previous_stats(
    message: Message,
    tz: ZoneInfo,
    payroll: PayrollService,
    profile_id: int,
) -> None:
    summary = await payroll.previous_period(profile_id, now(tz))
    extra = await _detailed_block(payroll, profile_id, summary)
    await message.answer(_format_summary(summary, "📊 Прошлый период") + extra)


@router.message(F.text == BTN_STATS_CHART)
async def handle_chart(
    message: Message,
    tz: ZoneInfo,
    payroll: PayrollService,
    charts: ChartService,
    active_shifts: ActiveShiftRepository,
    profile_id: int,
) -> None:
    reference = now(tz)
    start, end = period_bounds(reference, tz)
    shifts = await payroll.list_shifts(profile_id, start, end)

    if not shifts:
        active = await active_shifts.get(profile_id)
        await message.answer(
            "За текущий период ещё нет смен. График строить не из чего.",
            reply_markup=main_menu(active is not None),
        )
        return

    chart_path = charts.build_monthly_chart(profile_id, start, end, shifts)
    await message.answer_photo(
        FSInputFile(chart_path),
        caption=f"График часов за {format_month_year_ru(start)}",
    )


async def _detailed_block(
    payroll: PayrollService,
    profile_id: int,
    summary: PeriodSummary,
) -> str:
    if summary.shifts_count == 0:
        return "\n\nЗа период пока нет смен."

    shifts = await payroll.list_shifts(profile_id, summary.period_start, summary.period_end)
    hours = [shift.hours for shift in shifts]
    longest = max(hours)
    shortest = min(hours)
    average = (sum(hours, Decimal("0")) / Decimal(len(hours))).quantize(Decimal("0.01"))

    return (
        "\n\n"
        f"Средняя смена: {format_hours(average)}\n"
        f"Самая длинная: {format_hours(longest)}\n"
        f"Самая короткая: {format_hours(shortest)}"
    )
