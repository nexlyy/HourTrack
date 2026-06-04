import os
from dataclasses import dataclass, field
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    bot_token: str
    allowed_user_ids: frozenset[int]
    profile_owner_id: int
    database_path: Path
    timezone: ZoneInfo
    currency: str
    log_level: str
    charts_dir: Path = field(default_factory=lambda: Path("/tmp/hourtrack_charts"))


def _parse_user_ids(raw: str) -> frozenset[int]:
    if not raw:
        return frozenset()
    result = set()
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        try:
            result.add(int(chunk))
        except ValueError as exc:
            raise ValueError(f"Invalid user id in ALLOWED_USER_IDS: {chunk!r}") from exc
    return frozenset(result)


def _parse_single_id(raw: str, var_name: str) -> int:
    cleaned = raw.strip()
    if not cleaned:
        raise RuntimeError(f"{var_name} is not set")
    try:
        return int(cleaned)
    except ValueError as exc:
        raise ValueError(f"Invalid value in {var_name}: {cleaned!r}") from exc


def load_config() -> Config:
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("BOT_TOKEN is not set")

    allowed_ids = _parse_user_ids(os.getenv("ALLOWED_USER_IDS", ""))
    if not allowed_ids:
        raise RuntimeError("ALLOWED_USER_IDS is empty; bot would be unusable")

    profile_owner_id = _parse_single_id(os.getenv("PROFILE_OWNER_ID", ""), "PROFILE_OWNER_ID")

    if profile_owner_id not in allowed_ids:
        raise RuntimeError(
            "PROFILE_OWNER_ID must be present in ALLOWED_USER_IDS"
        )

    db_path = Path(os.getenv("DATABASE_PATH", "hourtrack.db")).expanduser().resolve()
    tz_name = os.getenv("TIMEZONE", "Europe/Warsaw")
    currency = os.getenv("DEFAULT_CURRENCY", "PLN")
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    return Config(
        bot_token=token,
        allowed_user_ids=allowed_ids,
        profile_owner_id=profile_owner_id,
        database_path=db_path,
        timezone=ZoneInfo(tz_name),
        currency=currency,
        log_level=log_level,
    )
