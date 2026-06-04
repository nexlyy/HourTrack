from __future__ import annotations

from datetime import date as date_cls, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from ..database.queries import ActiveShiftRepository, ShiftRepository, UserRepository
from ..keyboards.reply import BTN_ADD_MANUAL, BTN_CANCEL, cancel_menu, main_menu
from ..states.shift_states import ManualShiftStates
from ..utils.datetime_helpers import (
    format_date,
    format_hours,
    format_money,
    midnight,
    parse_hours,
    parse_user_date,
)

router = Router(name="manual_entry")


@router.message(F.text == BTN_ADD_MANUAL)
async def handle_add_manual(message: Message, state: FSMContext) -> None:
    await state.set_state(ManualShiftStates.waiting_for_date)
    await message.answer(
        "Введи дату смены.\n"
        "Поддерживаются форматы: 15.04.2026, 2026-04-15, «вчера», «позавчера», «сегодня».",
        reply_markup=cancel_menu(),
    )


@router.message(ManualShiftStates.waiting_for_date, F.text == BTN_CANCEL)
async def cancel_date(
    message: Message,
    state: FSMContext,
    active_shifts: ActiveShiftRepository,
    profile_id: int,
) -> None:
    await state.clear()
    active = await active_shifts.get(profile_id)
    await message.answer("Добавление отменено.", reply_markup=main_menu(active is not None))


@router.message(ManualShiftStates.waiting_for_date)
async def receive_date(
    message: Message,
    state: FSMContext,
    tz: ZoneInfo,
) -> None:
    parsed = parse_user_date(message.text or "", tz)
    if parsed is None:
        await message.answer(
            "Не удалось распознать дату. Пример: 15.04.2026 или «вчера».",
            reply_markup=cancel_menu(),
        )
        return

    await state.update_data(shift_date=parsed.isoformat())
    await state.set_state(ManualShiftStates.waiting_for_hours)
    await message.answer(
        f"Дата: {format_date(parsed)}\nТеперь введи количество отработанных часов (например 7.5).",
        reply_markup=cancel_menu(),
    )


@router.message(ManualShiftStates.waiting_for_hours, F.text == BTN_CANCEL)
async def cancel_hours(
    message: Message,
    state: FSMContext,
    active_shifts: ActiveShiftRepository,
    profile_id: int,
) -> None:
    await state.clear()
    active = await active_shifts.get(profile_id)
    await message.answer("Добавление отменено.", reply_markup=main_menu(active is not None))


@router.message(ManualShiftStates.waiting_for_hours)
async def receive_hours(
    message: Message,
    state: FSMContext,
    tz: ZoneInfo,
    shifts: ShiftRepository,
    users: UserRepository,
    active_shifts: ActiveShiftRepository,
    profile_id: int,
) -> None:
    hours = parse_hours(message.text or "")
    if hours is None:
        await message.answer(
            "Часы должны быть положительным числом до 24. Пример: 7.5",
            reply_markup=cancel_menu(),
        )
        return

    data = await state.get_data()
    raw_date = data.get("shift_date")
    if not raw_date:
        await state.clear()
        active = await active_shifts.get(profile_id)
        await message.answer(
            "Сессия потеряна. Начни заново через «✍️ Добавить смену вручную».",
            reply_markup=main_menu(active is not None),
        )
        return

    shift_date = date_cls.fromisoformat(raw_date)
    start_dt = midnight(shift_date, tz).replace(hour=9, minute=0)
    end_dt = start_dt + timedelta(hours=float(hours))

    await users.ensure_user(profile_id)
    await shifts.add_shift(
        telegram_id=profile_id,
        start_time=start_dt,
        end_time=end_dt,
        hours=hours,
        is_manual=True,
    )

    rate = await users.get_hourly_rate(profile_id)
    earned = (hours * rate).quantize(Decimal("0.01"))

    await state.clear()
    active = await active_shifts.get(profile_id)
    await message.answer(
        "Смена добавлена.\n"
        f"Дата: {format_date(shift_date)}\n"
        f"Часов: {format_hours(hours)}\n"
        f"Заработок: {format_money(earned, 'PLN')}",
        reply_markup=main_menu(active is not None),
    )
