HourTrack

A Telegram bot I built to track work shifts and calculate hourly pay. Punch in, punch out, the bot does the math. Also handles past shifts entered by hand, monthly stats and a chart.

Pay period runs from the 1st to the last day of the month, payout on the 10th of the next month.

Features

- Start/stop a shift with a button, hours counted automatically
- Add past shifts manually (date + hours)
- Current earnings, end-of-period forecast, days until payout
- Stats for current and previous period
- Bar chart of hours per day
- Private access via a Telegram ID whitelist

Stack

- Python 3.11+
- aiogram 3.x
- SQLite (aiosqlite)
- matplotlib

Run locally

Bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env


Fill in `.env`:

BOT_TOKEN=token from BotFather
ALLOWED_USER_IDS=your_telegram_id
PROFILE_OWNER_ID=your_telegram_id
DATABASE_PATH=./hourtrack.db
TIMEZONE=Europe/Warsaw
DEFAULT_CURRENCY=PLN
LOG_LEVEL=INFO


`ALLOWED_USER_IDS` takes several IDs separated by commas. `PROFILE_OWNER_ID` is whose data everyone in the whitelist sees — handy if someone else logs the shifts and you just want to watch. Get your ID from [@userinfobot](https://t.me/userinfobot).

Start it:
bash
python -m bot.main

Project layout


bot/
  main.py          entry point, DI and polling
  config.py        env loading and validation
  database/        sqlite connection + repositories
  handlers/        start, shifts, stats, settings, manual_entry
  keyboards/       reply keyboards
  middlewares/     access control
  services/        payroll math, chart generation
  states/          FSM states
  utils/           date/number helpers
deploy/
  hourtrack-bot.service
  backup.sh
  DEPLOY.md


Notes

- Money is handled with `Decimal`, not floats — no rounding drift on the cents.
- Hours are stored exactly; rounding happens only on display, so even a two-minute shift shows the right amount.
- The bot runs on long polling, so no open ports or webhook setup needed.
- Charts need a font with Cyrillic glyphs — `fonts-dejavu-core` on the server.

Deployment

Runs on a Linux VPS under systemd as an isolated user.

