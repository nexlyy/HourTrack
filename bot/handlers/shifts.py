from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from aiogram import F, Router
from aiogram.types import Message

from ..database.queries import ActiveShiftRepository, ShiftRepository, UserRepository
from ..keyboards.reply import BTN_END_SHIFT, BTN_START_SHIFT, BTN_SALARY, main_menu
from ..services.payroll import PayrollService
from ..utils.datetime_helpers import (
    format_datetime,
    format_duration,
    format_hours,
    format_money,
    hours_between,
    now,
)

router = Router(name="shifts")

LONG_SHIFT_HOURS = Decimal("24")


@router.message(F.text == BTN_START_SHIFT)
async def handle_start_shift(
    message: Message,
    tz: ZoneInfo,
    active_shifts: ActiveShiftRepository,
    users: UserRepository,
    profile_id: int,
) -> None:
    await users.ensure_user(profile_id)

    existing = await active_shifts.get(profile_id)
    if existing is not None:
        await message.answer(
            f"Смена уже идёт с {format_datetime(existing.start_time, tz)}.",
            reply_markup=main_menu(True),
        )
        return

    started_at = now(tz)
    await active_shifts.start(profile_id, started_at)
    await message.answer(
        f"Смена начата в {format_datetime(started_at, tz)}.\n"
        "Когда закончишь — нажми «🔴 Выход со смены».",
        reply_markup=main_menu(True),
    )


@router.message(F.text == BTN_END_SHIFT)
async def handle_end_shift(
    message: Message,
    tz: ZoneInfo,
    active_shifts: ActiveShiftRepository,
    shifts: ShiftRepository,
    users: UserRepository,
    profile_id: int,
) -> None:
    existing = await active_shifts.get(profile_id)

    if existing is None:
        await message.answer(
            "Активной смены нет. Нажми «🟢 Вход на смену», чтобы начать.",
            reply_markup=main_menu(False),
        )
        return

    ended_at = now(tz)
    start_local = existing.start_time.astimezone(tz)

    if ended_at < start_local:
        await message.answer(
            "Системное время некорректно. Проверь часы устройства.",
            reply_markup=main_menu(True),
        )
        return

    worked = hours_between(start_local, ended_at)
    long_shift_warning = worked > LONG_SHIFT_HOURS

    await shifts.add_shift(
        telegram_id=profile_id,
        start_time=start_local,
        end_time=ended_at,
        hours=worked,
        is_manual=False,
    )
    await active_shifts.finish(profile_id)

    rate = await users.get_hourly_rate(profile_id)
    earned = (worked * rate).quantize(Decimal("0.01"))

    lines = [
        "Смена закрыта.",
        f"Начало: {format_datetime(start_local, tz)}",
        f"Конец: {format_datetime(ended_at, tz)}",
        f"Отработано: {format_duration(worked)}",
        f"За смену: {format_money(earned, 'PLN')}",
    ]
    if long_shift_warning:
        lines.append(
            "\n⚠️ Длительность превышает 24 часа. "
            "Проверь корректность смены — при необходимости пересохрани вручную."
        )

    await message.answer("\n".join(lines), reply_markup=main_menu(False))


@router.message(F.text == BTN_SALARY)
async def handle_salary(
    message: Message,
    tz: ZoneInfo,
    payroll: PayrollService,
    active_shifts: ActiveShiftRepository,
    profile_id: int,
) -> None:
    summary = await payroll.current_period(profile_id, now(tz))
    active = await active_shifts.get(profile_id)

    period_end_inclusive = summary.period_end - timedelta(seconds=1)
    lines = [
        "💰 Текущая зарплата",
        "",
        f"Период: {summary.period_start.strftime('%d.%m.%Y')} — "
        f"{period_end_inclusive.strftime('%d.%m.%Y')}",
        f"Смен: {summary.shifts_count}",
        f"Часов отработано: {format_hours(summary.total_hours)}",
        f"Ставка: {format_money(summary.hourly_rate, 'PLN')}/ч",
        f"Заработано: {format_money(summary.earned, 'PLN')}",
        f"Прогноз до конца периода: {format_money(summary.forecast, 'PLN')}",
        "",
        f"Выплата: {summary.payout_date.strftime('%d.%m.%Y')}",
        f"До выплаты: {summary.days_to_payout} дн.",
    ]
    await message.answer("\n".join(lines), reply_markup=main_menu(active is not None))
