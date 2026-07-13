# Restore Guide

This guide explains how to restore the platform from a backup archive created by `deploy/backup.sh`.

⚠️ **WARNING:** Restoring a backup is a destructive operation. It will drop your current database and replace your current `.env` file and transcripts.

## How to Restore

1.  **Locate your backup archive.** Backups are typically stored in `/opt/discord-bot/data/backups/`.
    ```bash
    ls -lh /opt/discord-bot/data/backups/
    ```

2.  **Run the restore script:**
    ```bash
    cd /opt/discord-bot
    sudo ./deploy/restore.sh data/backups/full_backup_20260708_120000.tar.gz
    ```

3.  **Confirm the prompt.** The script will ask you to type `yes` to confirm the destructive operation.

### What `restore.sh` Does:
1.  **Stops Services:** Stops `discord-bot` and `discord-dashboard`.
2.  **Database Restore:** Drops the existing `discord_bot` database, recreates it, and imports the `database.sql` dump.
3.  **Config Restore:** Overwrites the current `.env` file with the backed-up version.
4.  **Transcript Restore:** Overwrites the `data/transcripts/` directory.
5.  **Restarts Services:** Starts `discord-bot` and `discord-dashboard` and checks their status.

## Manual Database Restore (Docker)

If you are using Docker and need to manually restore just the database:

```bash
# 1. Unzip the backup archive to extract database.sql
tar -xzf backup.tar.gz database.sql

# 2. Copy it to the postgres container
docker cp database.sql dc_bot-postgres-1:/tmp/database.sql

# 3. Drop and recreate database, then import
docker exec -it dc_bot-postgres-1 bash -c "
  dropdb -U postgres discord_bot && 
  createdb -U postgres discord_bot -O discord_bot && 
  psql -U discord_bot discord_bot < /tmp/database.sql
"
```
