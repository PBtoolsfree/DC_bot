# Installation Guide

The Enterprise Discord Management Platform can be installed in several ways. We recommend the One-Click Installer for Ubuntu/Oracle Cloud.

## Option 1: One-Click Installer (Recommended)

Tested on Ubuntu 22.04 and 24.04 LTS. Perfect for Oracle Cloud Always Free instances.

### Prerequisites
- A fresh Ubuntu server
- A registered Discord Bot Token
- A domain name pointing to your server's IP address (for SSL and Dashboard)

### Command
```bash
curl -fsSL https://raw.githubusercontent.com/PBtoolsfree/DC_bot/main/install.sh | sudo bash
```
Follow the interactive prompts to configure your bot, database, and domain.

---

## Option 2: Docker Compose

If you prefer containerized deployment, see [DOCKER.md](DOCKER.md) for detailed instructions.

```bash
git clone https://github.com/PBtoolsfree/DC_bot.git
cd DC_bot
cp .env.production .env
# Edit .env with your secrets
docker compose up -d
docker compose exec bot alembic upgrade head
```

---

## Option 3: Manual Installation (Bare Metal)

If you want to set up everything manually:

1.  **System Dependencies:**
    ```bash
    sudo apt update
    sudo apt install python3.10 python3-venv postgresql redis-server nginx certbot python3-certbot-nginx libpango-1.0-0 libpangocairo-1.0-0 libcairo2 libgdk-pixbuf-2.0-0
    ```

2.  **Database Setup:**
    ```sql
    CREATE USER discord_bot WITH PASSWORD 'your_password';
    CREATE DATABASE discord_bot OWNER discord_bot;
    ```

3.  **Project Setup:**
    ```bash
    git clone https://github.com/PBtoolsfree/DC_bot.git /opt/discord-bot
    cd /opt/discord-bot
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

4.  **Configuration:**
    Copy `.env.production` to `.env` and fill in your values.

5.  **Database Migrations:**
    ```bash
    alembic upgrade head
    ```

6.  **Services:**
    Copy systemd service files from `deploy/` to `/etc/systemd/system/` and start them.

See `deploy/verify.sh` to check your deployment health.
