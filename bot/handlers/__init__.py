from aiogram import Router

from . import manual_entry, settings, shifts, start, stats


def build_router() -> Router:
    router = Router(name="main")
    router.include_router(start.router)
    router.include_router(shifts.router)
    router.include_router(stats.router)
    router.include_router(settings.router)
    router.include_router(manual_entry.router)
    return router
