# Uninstall Guide

If you need to completely remove the Enterprise Discord Management Platform from your server, we provide an interactive uninstaller script.

## Using the Uninstaller

Run the script with root privileges:

```bash
cd /opt/discord-bot
sudo ./deploy/uninstall.sh
```

### Interactive Prompts
The script will ask you if you want to keep certain data:
1.  **"Remove PostgreSQL database?"** — If you say No, the `discord_bot` database and user will remain in PostgreSQL.
2.  **"Remove backup archives?"** — If you say No, the script will move your backups to `/tmp/discord_bot_backups_TIMESTAMP` before deleting the project directory.
3.  **"Remove log files?"** — Regardless of choice, systemd journal logs (`journalctl -u discord-bot`) remain unless you manually clear your system journals.

### What the Script Removes:
*   Stops and disables systemd services (`discord-bot`, `discord-dashboard`).
*   Removes systemd unit files.
*   Removes Nginx configurations (`/etc/nginx/sites-available/discord-bot`).
*   Removes the dedicated cron jobs for the `discordbot` user.
*   Drops the PostgreSQL database (optional).
*   Deletes the entire `/opt/discord-bot` directory (including the virtual environment).
*   Removes the `discordbot` system user.
*   Removes sysctl, logrotate, and fail2ban configurations.

---

## Manual Uninstallation

If the script is unavailable, you can perform these steps manually:

```bash
# 1. Stop services
sudo systemctl stop discord-bot discord-dashboard
sudo systemctl disable discord-bot discord-dashboard

# 2. Remove systemd files
sudo rm /etc/systemd/system/discord-bot.service
sudo rm /etc/systemd/system/discord-dashboard.service
sudo systemctl daemon-reload

# 3. Remove Nginx config
sudo rm /etc/nginx/sites-enabled/discord-bot
sudo rm /etc/nginx/sites-available/discord-bot
sudo systemctl restart nginx

# 4. Remove database
sudo -u postgres psql -c "DROP DATABASE discord_bot;"
sudo -u postgres psql -c "DROP USER discord_bot;"

# 5. Remove project directory
sudo rm -rf /opt/discord-bot

# 6. Remove user
sudo userdel -r discordbot
```
