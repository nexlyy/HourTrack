from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

logger = logging.getLogger(__name__)


class AccessControlMiddleware(BaseMiddleware):
    def __init__(self, allowed_ids: frozenset[int]) -> None:
        super().__init__()
        self._allowed_ids = allowed_ids

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = getattr(event, "from_user", None)
        if user is None:
            return await handler(event, data)

        if user.id in self._allowed_ids:
            return await handler(event, data)

        logger.warning("access denied for user_id=%s username=%s", user.id, user.username)

        denial_text = "Доступ ограничен. Этот бот используется приватно."

        if isinstance(event, Message):
            await event.answer(denial_text)
        elif isinstance(event, CallbackQuery):
            await event.answer(denial_text, show_alert=True)

        return None
