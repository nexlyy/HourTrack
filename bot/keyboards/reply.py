from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

BTN_START_SHIFT = "🟢 Вход на смену"
BTN_END_SHIFT = "🔴 Выход со смены"
BTN_ADD_MANUAL = "✍️ Добавить смену вручную"
BTN_STATS = "📊 Статистика"
BTN_SALARY = "💰 Текущая зарплата"
BTN_SETTINGS = "⚙️ Настройки"

BTN_STATS_CURRENT = "Текущий период"
BTN_STATS_PREVIOUS = "Прошлый период"
BTN_STATS_CHART = "График по дням"
BTN_BACK = "⬅️ Назад"

BTN_SETTINGS_RATE = "Изменить ставку"
BTN_SETTINGS_SHOW = "Показать ставку"

BTN_CANCEL = "Отмена"


def main_menu(has_active_shift: bool) -> ReplyKeyboardMarkup:
    shift_button = BTN_END_SHIFT if has_active_shift else BTN_START_SHIFT
    rows = [
        [KeyboardButton(text=shift_button)],
        [KeyboardButton(text=BTN_ADD_MANUAL), KeyboardButton(text=BTN_SALARY)],
        [KeyboardButton(text=BTN_STATS), KeyboardButton(text=BTN_SETTINGS)],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def stats_menu() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=BTN_STATS_CURRENT), KeyboardButton(text=BTN_STATS_PREVIOUS)],
        [KeyboardButton(text=BTN_STATS_CHART)],
        [KeyboardButton(text=BTN_BACK)],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def settings_menu() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=BTN_SETTINGS_SHOW), KeyboardButton(text=BTN_SETTINGS_RATE)],
        [KeyboardButton(text=BTN_BACK)],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def cancel_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_CANCEL)]],
        resize_keyboard=True,
    )


def remove_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()
