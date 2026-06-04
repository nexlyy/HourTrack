#!/usr/bin/env bash
set -euo pipefail

DB_PATH="/var/lib/hourtrack-bot/hourtrack.db"
BACKUP_DIR="/var/backups/hourtrack"
RETENTION_DAYS=14

mkdir -p "$BACKUP_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/hourtrack_${TIMESTAMP}.db"

sqlite3 "$DB_PATH" ".backup '$BACKUP_FILE'"
gzip -9 "$BACKUP_FILE"

find "$BACKUP_DIR" -name 'hourtrack_*.db.gz' -mtime +${RETENTION_DAYS} -delete
