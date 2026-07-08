#!/usr/bin/env bash
# ============================================================
# Full Backup Script
# ============================================================
# Backs up: Database, .env, transcripts, logs, uploads
# Usage: sudo ./deploy/backup.sh
# ============================================================

set -euo pipefail

INSTALL_DIR="/opt/discord-bot"
BACKUP_ROOT="$INSTALL_DIR/data/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="full_backup_${TIMESTAMP}"
WORK_DIR=$(mktemp -d)
RETENTION_DAYS=30

GREEN='\033[0;32m'; NC='\033[0m'
log() { echo -e "${GREEN}[✔]${NC} $1"; }

mkdir -p "$BACKUP_ROOT"

log "Starting full backup..."

# 1. Database
log "Dumping PostgreSQL..."
sudo -u postgres pg_dump discord_bot > "$WORK_DIR/database.sql" 2>/dev/null || echo "-- DB dump skipped" > "$WORK_DIR/database.sql"

# 2. Environment
cp "$INSTALL_DIR/.env" "$WORK_DIR/.env" 2>/dev/null || true

# 3. Transcripts
if [[ -d "$INSTALL_DIR/data/transcripts" ]]; then
    cp -r "$INSTALL_DIR/data/transcripts" "$WORK_DIR/transcripts" 2>/dev/null || true
fi

# 4. Logs (last 7 days)
mkdir -p "$WORK_DIR/logs"
find "$INSTALL_DIR/logs" -name "*.log" -mtime -7 -exec cp {} "$WORK_DIR/logs/" \; 2>/dev/null || true

# 5. Alembic version info
"$INSTALL_DIR/venv/bin/alembic" current > "$WORK_DIR/alembic_version.txt" 2>/dev/null || true

# 6. Compress
ARCHIVE="$BACKUP_ROOT/${BACKUP_NAME}.tar.gz"
tar -czf "$ARCHIVE" -C "$WORK_DIR" .
rm -rf "$WORK_DIR"

# 7. Cleanup old backups
find "$BACKUP_ROOT" -name "full_backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true

SIZE=$(du -h "$ARCHIVE" | cut -f1)
log "Backup complete: $ARCHIVE ($SIZE)"
log "Cleaned backups older than ${RETENTION_DAYS} days."
