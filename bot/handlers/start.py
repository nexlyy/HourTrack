from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from ..database.queries import ActiveShiftRepository, UserRepository
from ..keyboards.reply import BTN_BACK, main_menu

router = Router(name="start")

WELCOME_TEXT = (
    "HourTrack — учёт смен и зарплаты.\n\n"
    "Что умеет бот:\n"
    "• фиксирует начало и конец смены по кнопке;\n"
    "• считает заработок по почасовой ставке;\n"
    "• ведёт период с 1-го по последнее число месяца, выплата — 10-го числа;\n"
    "• позволяет добавить прошлые смены вручную;\n"
    "• показывает статистику и график часов за месяц.\n\n"
    "Перед первой сменой задай ставку в разделе «⚙️ Настройки»."
)

HELP_TEXT = (
    "Команды:\n"
    "/start — главное меню\n"
    "/help — помощь\n"
    "/cancel — отмена текущего действия"
)


@router.message(CommandStart())
async def handle_start(
    message: Message,
    state: FSMContext,
    users: UserRepository,
    active_shifts: ActiveShiftRepository,
    profile_id: int,
) -> None:
    await state.clear()
    await users.ensure_user(profile_id)
    active = await active_shifts.get(profile_id)
    await message.answer(WELCOME_TEXT, reply_markup=main_menu(active is not None))


@router.message(Command("help"))
async def handle_help(message: Message) -> None:
    await message.answer(HELP_TEXT)


@router.message(Command("cancel"))
async def handle_cancel(
    message: Message,
    state: FSMContext,
    active_shifts: ActiveShiftRepository,
    profile_id: int,
) -> None:
    await state.clear()
    active = await active_shifts.get(profile_id)
    await message.answer("Действие отменено.", reply_markup=main_menu(active is not None))


@router.message(F.text == BTN_BACK)
async def handle_back(
    message: Message,
    state: FSMContext,
    active_shifts: ActiveShiftRepository,
    profile_id: int,
) -> None:
    await state.clear()
    active = await active_shifts.get(profile_id)
    await message.answer("Главное меню", reply_markup=main_menu(active is not None))
