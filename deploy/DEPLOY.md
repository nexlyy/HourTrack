# Деплой HourTrack на VPS

Инструкция для Ubuntu 24.04. Подразумевается SSH-доступ к серверу по ключу.

Бот работает по long polling — открывать порты и трогать nginx не нужно.

## 1. Подключение и системные пакеты

```bash
ssh your-server
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3-pip git sqlite3 fonts-dejavu-core
```

`fonts-dejavu-core` критичен: без него matplotlib не сможет отрисовать кириллицу на графиках.

## 2. Системный пользователь

Бот должен работать от изолированного юзера без shell-доступа:

```bash
sudo useradd --system --no-create-home --shell /usr/sbin/nologin hourtrack
```

## 3. Каталоги и репозиторий

```bash
sudo mkdir -p /opt/hourtrack-bot
sudo mkdir -p /var/lib/hourtrack-bot
sudo mkdir -p /var/backups/hourtrack

sudo git clone https://github.com/<your-username>/hourtrack-bot.git /opt/hourtrack-bot
cd /opt/hourtrack-bot
```

## 4. Виртуальное окружение и зависимости

```bash
sudo python3.12 -m venv /opt/hourtrack-bot/venv
sudo /opt/hourtrack-bot/venv/bin/pip install --upgrade pip
sudo /opt/hourtrack-bot/venv/bin/pip install -r /opt/hourtrack-bot/requirements.txt
```

## 5. Конфигурация

```bash
sudo cp /opt/hourtrack-bot/.env.example /opt/hourtrack-bot/.env
sudo nano /opt/hourtrack-bot/.env
```

Заполни:

```
BOT_TOKEN=токен_от_BotFather
ALLOWED_USER_IDS=твой_telegram_id
DATABASE_PATH=/var/lib/hourtrack-bot/hourtrack.db
TIMEZONE=Europe/Warsaw
DEFAULT_CURRENCY=PLN
LOG_LEVEL=INFO
```

Свой Telegram ID можно узнать через бота `@userinfobot`. Несколько ID разделяй запятой:
`ALLOWED_USER_IDS=12345678,87654321`

Защити файл:

```bash
sudo chown hourtrack:hourtrack /opt/hourtrack-bot/.env
sudo chmod 600 /opt/hourtrack-bot/.env
```

## 6. Права на каталоги данных

```bash
sudo chown -R hourtrack:hourtrack /var/lib/hourtrack-bot
sudo chown -R hourtrack:hourtrack /var/backups/hourtrack
sudo chown -R hourtrack:hourtrack /opt/hourtrack-bot
```

## 7. systemd-юнит

```bash
sudo cp /opt/hourtrack-bot/deploy/hourtrack-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable hourtrack-bot
sudo systemctl start hourtrack-bot
```

## 8. Проверка

```bash
sudo systemctl status hourtrack-bot
sudo journalctl -u hourtrack-bot -f
```

В логах должно появиться `starting HourTrack bot` и `polling started`. После этого напиши боту `/start` в Telegram.

## 9. Бэкапы БД

```bash
sudo cp /opt/hourtrack-bot/deploy/backup.sh /usr/local/bin/hourtrack-backup.sh
sudo chmod +x /usr/local/bin/hourtrack-backup.sh
sudo crontab -e
```

Добавь строку:

```
0 4 * * * /usr/local/bin/hourtrack-backup.sh >> /var/log/hourtrack-backup.log 2>&1
```

Ротация — 14 дней, настраивается переменной `RETENTION_DAYS` в скрипте.

## 10. Обновление бота

```bash
ssh your-server
cd /opt/hourtrack-bot

sudo cp /var/lib/hourtrack-bot/hourtrack.db /var/backups/hourtrack/hourtrack.db.before-update-$(date +%Y%m%d_%H%M%S)

sudo -u hourtrack git pull
sudo /opt/hourtrack-bot/venv/bin/pip install -r requirements.txt

sudo systemctl restart hourtrack-bot
sudo systemctl status hourtrack-bot
```

## 11. Лимиты памяти

Юнит ограничен лимитом `MemoryMax=256M` — этого с запасом хватает на типовой VPS (1-4 ГБ RAM). Если памяти не хватает — снизить `MemoryMax` в `/etc/systemd/system/hourtrack-bot.service` и перезапустить:

```bash
sudo systemctl daemon-reload
sudo systemctl restart hourtrack-bot
```

## Troubleshooting

**Бот не стартует, в логах `BOT_TOKEN is not set`** — проверь `/opt/hourtrack-bot/.env`, права `chmod 600`, владельца `chown hourtrack:hourtrack`.

**`permission denied` на БД** — проверь владельца `/var/lib/hourtrack-bot/` и `ReadWritePaths` в юните.

**На графиках вместо букв квадратики** — не установлен `fonts-dejavu-core`. Поставить и перезапустить сервис.

**Бот отвечает «Доступ ограничен»** — твой Telegram ID не в `ALLOWED_USER_IDS`. Узнать ID через `@userinfobot`, добавить в `.env`, перезапустить сервис.

**Высокое потребление памяти** — посмотреть `systemctl status hourtrack-bot`, при необходимости увеличить `MemoryMax`.
