#!/bin/bash
# ============================================================
# Discord Management Platform — Database Backup Script
# ============================================================
# Recommended: Run via cron every 6 hours.
# crontab -e → 0 */6 * * * /opt/discord-bot/deploy/backup_db.sh
# ============================================================

set -euo pipefail

# Configuration
BACKUP_DIR="/opt/discord-bot/backups"
RETENTION_DAYS=30
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/discord_bot_${TIMESTAMP}.sql.gz"

# Ensure backup directory exists
mkdir -p "${BACKUP_DIR}"

# Run pg_dump inside the Docker container (or directly if bare-metal)
if command -v docker &> /dev/null && docker ps --format '{{.Names}}' | grep -q postgres; then
    # Docker deployment
    docker exec postgres pg_dump -U "${POSTGRES_USER:-postgres}" discord_bot | gzip > "${BACKUP_FILE}"
else
    # Bare-metal deployment
    pg_dump -h localhost -U "${POSTGRES_USER:-postgres}" discord_bot | gzip > "${BACKUP_FILE}"
fi

echo "[$(date)] Backup created: ${BACKUP_FILE}"

# Cleanup old backups
find "${BACKUP_DIR}" -name "*.sql.gz" -mtime +${RETENTION_DAYS} -delete
echo "[$(date)] Cleaned backups older than ${RETENTION_DAYS} days."
