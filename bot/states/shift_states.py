from aiogram.fsm.state import State, StatesGroup


class RateStates(StatesGroup):
    waiting_for_rate = State()


class ManualShiftStates(StatesGroup):
    waiting_for_date = State()
    waiting_for_hours = State()
