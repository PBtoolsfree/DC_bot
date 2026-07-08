#!/usr/bin/env bash
# ============================================================
# One-Click Update Script
# ============================================================
# Usage: sudo ./update.sh
# ============================================================

set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

log()   { echo -e "${GREEN}[✔]${NC} $1"; }
warn()  { echo -e "${YELLOW}[⚠]${NC} $1"; }
error() { echo -e "${RED}[✘]${NC} $1"; }

INSTALL_DIR="/opt/discord-bot"
BOT_USER="discordbot"
BACKUP_DIR="$INSTALL_DIR/data/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

if [[ $EUID -ne 0 ]]; then error "Run as root."; exit 1; fi
if [[ ! -d "$INSTALL_DIR" ]]; then error "Installation not found at $INSTALL_DIR"; exit 1; fi

cd "$INSTALL_DIR"

echo -e "${BOLD}${CYAN}══════════════════════════════════════${NC}"
echo -e "${BOLD} Discord Platform — Update${NC}"
echo -e "${BOLD}${CYAN}══════════════════════════════════════${NC}"

# 1. Pre-flight backup
log "Creating pre-update backup..."
mkdir -p "$BACKUP_DIR"
sudo -u postgres pg_dump discord_bot | gzip > "$BACKUP_DIR/pre_update_${TIMESTAMP}.sql.gz" 2>/dev/null || warn "DB backup skipped."
cp "$INSTALL_DIR/.env" "$BACKUP_DIR/.env.backup_${TIMESTAMP}" 2>/dev/null || true
log "Backup saved to $BACKUP_DIR"

# 2. Pull latest code
log "Pulling latest changes..."
sudo -u "$BOT_USER" git pull --rebase || { error "Git pull failed."; exit 1; }

# 3. Python dependencies
log "Updating Python dependencies..."
sudo -u "$BOT_USER" "$INSTALL_DIR/venv/bin/pip" install -r requirements.txt -q

# 4. Frontend rebuild
if [[ -d "$INSTALL_DIR/dashboard/frontend" ]] && [[ -f "$INSTALL_DIR/dashboard/frontend/package.json" ]]; then
    log "Rebuilding frontend..."
    cd "$INSTALL_DIR/dashboard/frontend"
    sudo -u "$BOT_USER" npm ci --silent 2>/dev/null || sudo -u "$BOT_USER" npm install --silent
    sudo -u "$BOT_USER" npm run build --silent 2>/dev/null || warn "Frontend build skipped."
    cd "$INSTALL_DIR"
fi

# 5. Alembic migrations (with rollback on failure)
log "Running database migrations..."
CURRENT_HEAD=$("$INSTALL_DIR/venv/bin/alembic" current 2>/dev/null | head -1 || echo "unknown")

if sudo -u "$BOT_USER" "$INSTALL_DIR/venv/bin/alembic" upgrade head; then
    log "Migrations applied successfully."
else
    error "Migration failed! Rolling back..."
    if [[ -f "$BACKUP_DIR/pre_update_${TIMESTAMP}.sql.gz" ]]; then
        gunzip -c "$BACKUP_DIR/pre_update_${TIMESTAMP}.sql.gz" | sudo -u postgres psql discord_bot
        warn "Database restored from pre-update backup."
    fi
    error "Update aborted. Please check the migration logs."
    exit 1
fi

# 6. Restart services
log "Restarting services..."
systemctl restart discord-bot discord-dashboard
sleep 3

# 7. Verify
if systemctl is-active --quiet discord-bot; then
    log "Discord Bot is running."
else
    error "Discord Bot failed to start! Check: journalctl -u discord-bot -n 50"
fi

if systemctl is-active --quiet discord-dashboard; then
    log "Dashboard API is running."
else
    error "Dashboard API failed to start! Check: journalctl -u discord-dashboard -n 50"
fi

echo ""
log "Update complete! Previous backup: $BACKUP_DIR/pre_update_${TIMESTAMP}.sql.gz"
