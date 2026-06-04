from __future__ import annotations

from zoneinfo import ZoneInfo

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from ..database.queries import ActiveShiftRepository, UserRepository
from ..keyboards.reply import (
    BTN_CANCEL,
    BTN_SETTINGS,
    BTN_SETTINGS_RATE,
    BTN_SETTINGS_SHOW,
    cancel_menu,
    main_menu,
    settings_menu,
)
from ..states.shift_states import RateStates
from ..utils.datetime_helpers import format_money, parse_rate

router = Router(name="settings")


@router.message(F.text == BTN_SETTINGS)
async def handle_settings(message: Message) -> None:
    await message.answer("Настройки", reply_markup=settings_menu())


@router.message(F.text == BTN_SETTINGS_SHOW)
async def handle_show_rate(
    message: Message,
    users: UserRepository,
    profile_id: int,
) -> None:
    rate = await users.get_hourly_rate(profile_id)
    if rate == 0:
        await message.answer("Ставка не задана. Установи её в настройках.")
        return
    await message.answer(f"Текущая ставка: {format_money(rate, 'PLN')}/ч")


@router.message(F.text == BTN_SETTINGS_RATE)
async def handle_change_rate(message: Message, state: FSMContext) -> None:
    await state.set_state(RateStates.waiting_for_rate)
    await message.answer(
        "Введи новую почасовую ставку в PLN (например: 28 или 28.50).",
        reply_markup=cancel_menu(),
    )


@router.message(RateStates.waiting_for_rate, F.text == BTN_CANCEL)
async def cancel_rate(
    message: Message,
    state: FSMContext,
    active_shifts: ActiveShiftRepository,
    profile_id: int,
) -> None:
    await state.clear()
    active = await active_shifts.get(profile_id)
    await message.answer("Изменение ставки отменено.", reply_markup=main_menu(active is not None))


@router.message(RateStates.waiting_for_rate)
async def receive_rate(
    message: Message,
    state: FSMContext,
    users: UserRepository,
    active_shifts: ActiveShiftRepository,
    profile_id: int,
) -> None:
    rate = parse_rate(message.text or "")
    if rate is None:
        await message.answer(
            "Не удалось распознать ставку. Введи положительное число, например 28.50.",
            reply_markup=cancel_menu(),
        )
        return

    await users.set_hourly_rate(profile_id, rate)
    await state.clear()
    active = await active_shifts.get(profile_id)
    await message.answer(
        f"Ставка сохранена: {format_money(rate, 'PLN')}/ч",
        reply_markup=main_menu(active is not None),
    )
