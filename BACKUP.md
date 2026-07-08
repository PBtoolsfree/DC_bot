# Backup Guide

Backups are critical for production systems. The platform includes automated and manual backup tools.

## Automated Backups

If you used the One-Click Installer, a cron job is automatically configured to run every 6 hours.

To manually install the cron job:
```bash
crontab -u discordbot -e
```
Add the following line:
```
0 */6 * * * /opt/discord-bot/deploy/backup.sh
```

## Manual Backup

You can trigger a full backup at any time:

```bash
cd /opt/discord-bot
sudo ./deploy/backup.sh
```

### What is Backed Up?
The `backup.sh` script creates a timestamped `.tar.gz` archive containing:
1.  **Database Dump:** Full PostgreSQL database export (`database.sql`).
2.  **Environment Variables:** Your `.env` file containing secrets.
3.  **Transcripts:** HTML/PDF ticket transcripts stored in `data/transcripts/`.
4.  **Logs:** Application logs from the last 7 days.
5.  **Migration State:** Current Alembic version for safe restoration.

Backups are stored in `/opt/discord-bot/data/backups/`.
The script automatically cleans up backups older than 30 days.

## Offsite Backups (Highly Recommended)

We strongly recommend copying your backup archives to an offsite location (e.g., AWS S3, Google Cloud Storage, or a separate server) using a tool like `rclone` or `rsync`.

Example cron job for offsite sync (requires `rclone` setup):
```bash
# Sync backups to S3 bucket daily at 2 AM
0 2 * * * rclone sync /opt/discord-bot/data/backups/ remote:my-bot-backups/
```
