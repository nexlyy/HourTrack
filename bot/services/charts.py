from __future__ import annotations

import io
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib import font_manager

from ..database.queries import Shift
from ..utils.datetime_helpers import format_month_year_ru

logger = logging.getLogger(__name__)

CYRILLIC_FONT_CANDIDATES = (
    "DejaVu Sans",
    "Liberation Sans",
    "Noto Sans",
    "FreeSans",
    "Arial",
)


def _select_cyrillic_font() -> str:
    available = {font.name for font in font_manager.fontManager.ttflist}
    for name in CYRILLIC_FONT_CANDIDATES:
        if name in available:
            return name
    logger.warning("no preferred cyrillic font found, falling back to default sans-serif")
    return "sans-serif"


_SELECTED_FONT = _select_cyrillic_font()

plt.rcParams["font.family"] = _SELECTED_FONT
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 110


class ChartService:
    def __init__(self, tz: ZoneInfo, output_dir: Path) -> None:
        self._tz = tz
        self._output_dir = output_dir
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def build_monthly_chart(
        self,
        telegram_id: int,
        period_start: datetime,
        period_end: datetime,
        shifts: list[Shift],
    ) -> Path:
        total_days = (period_end - period_start).days
        days = [period_start + timedelta(days=offset) for offset in range(total_days)]
        hours_per_day = {day.date(): Decimal("0") for day in days}

        for shift in shifts:
            local_date = shift.start_time.astimezone(self._tz).date()
            if local_date in hours_per_day:
                hours_per_day[local_date] += shift.hours

        labels = [day.strftime("%d.%m") for day in days]
        values = [float(hours_per_day[day.date()]) for day in days]

        figure, axes = plt.subplots(figsize=(11, 5))
        bars = axes.bar(labels, values, color="#FF6B35", edgecolor="#C44A1A", linewidth=0.6)

        axes.set_title(
            f"Часы по дням — {format_month_year_ru(period_start)}",
            fontsize=13,
            pad=14,
        )
        axes.set_ylabel("Часы")
        axes.set_xlabel("День")
        axes.grid(axis="y", linestyle="--", alpha=0.4)
        axes.set_axisbelow(True)

        for label in axes.get_xticklabels():
            label.set_rotation(60)
            label.set_horizontalalignment("right")
            label.set_fontsize(8)

        max_value = max(values) if values else 0
        if max_value > 0:
            for bar, value in zip(bars, values):
                if value <= 0:
                    continue
                axes.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + max_value * 0.02,
                    f"{value:.1f}",
                    ha="center",
                    va="bottom",
                    fontsize=7,
                    color="#333333",
                )

        figure.tight_layout()

        timestamp = datetime.now(self._tz).strftime("%Y%m%d_%H%M%S")
        output_path = self._output_dir / f"chart_{telegram_id}_{timestamp}.png"

        buffer = io.BytesIO()
        figure.savefig(buffer, format="png", bbox_inches="tight")
        plt.close(figure)
        buffer.seek(0)

        output_path.write_bytes(buffer.getvalue())
        return output_path
