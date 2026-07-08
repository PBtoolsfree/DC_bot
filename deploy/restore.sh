#!/usr/bin/env bash
# ============================================================
# Restore Script
# ============================================================
# Usage: sudo ./deploy/restore.sh <backup_archive.tar.gz>
# ============================================================

set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
log()   { echo -e "${GREEN}[✔]${NC} $1"; }
warn()  { echo -e "${YELLOW}[⚠]${NC} $1"; }
error() { echo -e "${RED}[✘]${NC} $1"; }

INSTALL_DIR="/opt/discord-bot"

if [[ $# -lt 1 ]]; then
    error "Usage: $0 <backup_archive.tar.gz>"
    echo "Available backups:"
    ls -lh "$INSTALL_DIR/data/backups/"*.tar.gz 2>/dev/null || echo "  No backups found."
    exit 1
fi

ARCHIVE="$1"
if [[ ! -f "$ARCHIVE" ]]; then
    error "Backup file not found: $ARCHIVE"
    exit 1
fi

echo -e "${YELLOW}${RED}WARNING: This will overwrite the current database and configuration!${NC}"
echo -e "Archive: $ARCHIVE"
read -rp "Are you sure? Type 'yes' to confirm: " CONFIRM
if [[ "$CONFIRM" != "yes" ]]; then
    error "Restore cancelled."
    exit 0
fi

WORK_DIR=$(mktemp -d)
log "Extracting backup..."
tar -xzf "$ARCHIVE" -C "$WORK_DIR"

# Stop services
log "Stopping services..."
systemctl stop discord-bot discord-dashboard 2>/dev/null || true

# Restore database
if [[ -f "$WORK_DIR/database.sql" ]]; then
    log "Restoring database..."
    sudo -u postgres psql -c "DROP DATABASE IF EXISTS discord_bot;" 2>/dev/null || true
    sudo -u postgres psql -c "CREATE DATABASE discord_bot OWNER discord_bot;" 2>/dev/null || true
    sudo -u postgres psql discord_bot < "$WORK_DIR/database.sql"
    log "Database restored."
else
    warn "No database dump found in backup."
fi

# Restore .env
if [[ -f "$WORK_DIR/.env" ]]; then
    cp "$WORK_DIR/.env" "$INSTALL_DIR/.env"
    chown discordbot:discordbot "$INSTALL_DIR/.env"
    chmod 600 "$INSTALL_DIR/.env"
    log ".env restored."
fi

# Restore transcripts
if [[ -d "$WORK_DIR/transcripts" ]]; then
    cp -r "$WORK_DIR/transcripts" "$INSTALL_DIR/data/"
    chown -R discordbot:discordbot "$INSTALL_DIR/data/transcripts"
    log "Transcripts restored."
fi

# Cleanup
rm -rf "$WORK_DIR"

# Restart
log "Starting services..."
systemctl start discord-bot discord-dashboard

sleep 3
if systemctl is-active --quiet discord-bot; then
    log "Restore complete. Bot is running."
else
    error "Bot failed to start after restore. Check: journalctl -u discord-bot -n 50"
fi
