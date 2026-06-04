from __future__ import annotations

import asyncio
import logging
import sys
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import TelegramObject

from .config import Config, load_config
from .database.db import Database
from .database.queries import ActiveShiftRepository, ShiftRepository, UserRepository
from .handlers import build_router
from .middlewares.access import AccessControlMiddleware
from .services.charts import ChartService
from .services.payroll import PayrollService


def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s %(levelname)-7s %(name)s — %(message)s",
        stream=sys.stdout,
    )
    logging.getLogger("aiogram.event").setLevel(logging.WARNING)


def build_dependency_injector(
    config: Config,
    users: UserRepository,
    shifts: ShiftRepository,
    active_shifts: ActiveShiftRepository,
    payroll: PayrollService,
    charts: ChartService,
) -> Callable[
    [Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]], TelegramObject, dict[str, Any]],
    Awaitable[Any],
]:
    async def injector(
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        data["users"] = users
        data["shifts"] = shifts
        data["active_shifts"] = active_shifts
        data["payroll"] = payroll
        data["charts"] = charts
        data["tz"] = config.timezone
        data["profile_id"] = config.profile_owner_id
        return await handler(event, data)

    return injector


async def run() -> None:
    config = load_config()
    setup_logging(config.log_level)
    logger = logging.getLogger(__name__)
    logger.info("starting HourTrack bot")

    database = Database(config.database_path)
    await database.connect()

    users = UserRepository(database)
    shifts = ShiftRepository(database)
    active_shifts = ActiveShiftRepository(database)
    payroll = PayrollService(users, shifts, config.timezone)
    charts = ChartService(config.timezone, config.charts_dir)

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=None),
    )
    dispatcher = Dispatcher(storage=MemoryStorage())

    dispatcher.update.outer_middleware(AccessControlMiddleware(config.allowed_user_ids))
    dispatcher.update.middleware(
        build_dependency_injector(config, users, shifts, active_shifts, payroll, charts)
    )

    dispatcher.include_router(build_router())

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("polling started")
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()
        await database.close()
        logger.info("shutdown complete")


def main() -> None:
    try:
        asyncio.run(run())
    except (KeyboardInterrupt, SystemExit):
        pass


if __name__ == "__main__":
    main()
