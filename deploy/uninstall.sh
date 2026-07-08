#!/usr/bin/env bash
# ============================================================
# Uninstaller
# ============================================================
# Usage: sudo ./deploy/uninstall.sh
# ============================================================

set -uo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BOLD='\033[1m'; NC='\033[0m'

INSTALL_DIR="/opt/discord-bot"
BOT_USER="discordbot"

if [[ $EUID -ne 0 ]]; then echo -e "${RED}Run as root.${NC}"; exit 1; fi

echo -e "${BOLD}${RED}══════════════════════════════════════${NC}"
echo -e "${BOLD} Discord Platform — Uninstaller${NC}"
echo -e "${BOLD}${RED}══════════════════════════════════════${NC}\n"

ask() {
    read -rp "$(echo -e "${YELLOW}$1 [y/N]: ${NC}")" answer
    [[ "${answer,,}" == "y" ]]
}

KEEP_DB=true; KEEP_BACKUPS=true; KEEP_LOGS=true

ask "Remove PostgreSQL database?" && KEEP_DB=false
ask "Remove backup archives?" && KEEP_BACKUPS=false
ask "Remove log files?" && KEEP_LOGS=false

echo ""
echo -e "${RED}${BOLD}This will permanently remove the Discord Platform.${NC}"
read -rp "Type 'UNINSTALL' to confirm: " CONFIRM
if [[ "$CONFIRM" != "UNINSTALL" ]]; then
    echo "Cancelled."; exit 0
fi

# 1. Stop services
echo -e "\n${GREEN}[1/8]${NC} Stopping services..."
systemctl stop discord-bot discord-dashboard 2>/dev/null || true
systemctl disable discord-bot discord-dashboard 2>/dev/null || true

# 2. Remove systemd units
echo -e "${GREEN}[2/8]${NC} Removing systemd services..."
rm -f /etc/systemd/system/discord-bot.service
rm -f /etc/systemd/system/discord-dashboard.service
systemctl daemon-reload

# 3. Remove Nginx config
echo -e "${GREEN}[3/8]${NC} Removing Nginx configuration..."
rm -f /etc/nginx/sites-enabled/discord-bot
rm -f /etc/nginx/sites-available/discord-bot
systemctl restart nginx 2>/dev/null || true

# 4. Remove cron jobs
echo -e "${GREEN}[4/8]${NC} Removing cron jobs..."
crontab -u "$BOT_USER" -r 2>/dev/null || true

# 5. Remove database
if [[ "$KEEP_DB" == false ]]; then
    echo -e "${GREEN}[5/8]${NC} Dropping database..."
    sudo -u postgres psql -c "DROP DATABASE IF EXISTS discord_bot;" 2>/dev/null || true
    sudo -u postgres psql -c "DROP USER IF EXISTS discord_bot;" 2>/dev/null || true
else
    echo -e "${GREEN}[5/8]${NC} Database preserved."
fi

# 6. Remove project directory
echo -e "${GREEN}[6/8]${NC} Removing project files..."
if [[ "$KEEP_BACKUPS" == true ]] && [[ -d "$INSTALL_DIR/data/backups" ]]; then
    BACKUP_SAVE="/tmp/discord_bot_backups_$(date +%s)"
    mv "$INSTALL_DIR/data/backups" "$BACKUP_SAVE"
    echo "  Backups saved to: $BACKUP_SAVE"
fi

if [[ "$KEEP_LOGS" == true ]]; then
    echo "  Logs preserved in journalctl."
fi

rm -rf "$INSTALL_DIR"

# 7. Remove system user
echo -e "${GREEN}[7/8]${NC} Removing system user..."
userdel -r "$BOT_USER" 2>/dev/null || true

# 8. Remove kernel tuning
echo -e "${GREEN}[8/8]${NC} Removing kernel optimizations..."
rm -f /etc/sysctl.d/99-discord-bot.conf
rm -f /etc/logrotate.d/discord-bot
rm -f /etc/fail2ban/jail.local
sysctl --system -q 2>/dev/null || true

echo -e "\n${GREEN}${BOLD}Uninstall complete.${NC}"
[[ "$KEEP_DB" == true ]] && echo -e "  Database preserved in PostgreSQL."
[[ "$KEEP_BACKUPS" == true ]] && echo -e "  Backups saved to: ${BACKUP_SAVE:-N/A}"
