# Deployment Guide

## Prerequisites

- Docker Engine 24+ and Docker Compose v2
- A registered Discord Application with Bot Token and OAuth2 credentials
- A domain name (for the dashboard)

---

## Quick Start (Docker)

```bash
# 1. Clone the repository
git clone https://github.com/your-org/discord-management-platform.git
cd discord-management-platform

# 2. Generate secrets
python -c "import secrets; print(secrets.token_hex(32))"

# 3. Configure environment
cp .env.production .env
# Edit .env with your Discord token, database password, JWT secret, and OAuth2 credentials

# 4. Start all services
docker compose up -d

# 5. Run database migrations
docker compose exec bot alembic upgrade head

# 6. Verify
docker compose ps
docker compose logs bot --tail 50
curl http://localhost/health
```

---

## Bare-Metal Deployment

```bash
# 1. Create system user
sudo useradd -r -s /bin/false discordbot

# 2. Install to /opt
sudo mkdir -p /opt/discord-bot
sudo chown discordbot:discordbot /opt/discord-bot

# 3. Setup virtual environment
cd /opt/discord-bot
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Configure environment
cp .env.production .env
# Edit .env

# 5. Run migrations
alembic upgrade head

# 6. Install systemd services
sudo cp deploy/discord-bot.service /etc/systemd/system/
sudo cp deploy/discord-dashboard.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now discord-bot discord-dashboard

# 7. Setup Nginx
sudo cp nginx/nginx.conf /etc/nginx/nginx.conf
sudo systemctl restart nginx

# 8. Setup backup cron
sudo crontab -u discordbot -e
# Add: 0 */6 * * * /opt/discord-bot/deploy/backup_db.sh
```

---

## Updating

```bash
# Docker
git pull
docker compose build
docker compose exec bot alembic upgrade head
docker compose up -d

# Bare-metal
git pull
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
sudo systemctl restart discord-bot discord-dashboard
```

---

## Monitoring

- **Health**: `GET /health`
- **Logs (Docker)**: `docker compose logs -f bot`
- **Logs (Systemd)**: `journalctl -u discord-bot -f`
- **Sentry**: Set `SENTRY_DSN` in `.env` for automatic error tracking
- **Database backups**: Check `/opt/discord-bot/backups/`
