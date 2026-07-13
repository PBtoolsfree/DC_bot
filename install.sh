#!/usr/bin/env bash
# ============================================================
# Enterprise Discord Management Platform — One-Click Installer
# ============================================================
# Tested on: Ubuntu 22.04 / 24.04 LTS (Oracle Cloud Always Free)
#
# Usage:
#   chmod +x install.sh && sudo ./install.sh
#
# Or remote:
#   curl -fsSL https://raw.githubusercontent.com/PBtoolsfree/DC_bot/main/install.sh | sudo bash
# ============================================================

set -euo pipefail

# ── Colors ──────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

log()   { echo -e "${GREEN}[✔]${NC} $1"; }
warn()  { echo -e "${YELLOW}[⚠]${NC} $1"; }
error() { echo -e "${RED}[✘]${NC} $1"; }
info()  { echo -e "${CYAN}[i]${NC} $1"; }
header(){ echo -e "\n${BOLD}${BLUE}══════════════════════════════════════${NC}"; echo -e "${BOLD} $1${NC}"; echo -e "${BOLD}${BLUE}══════════════════════════════════════${NC}\n"; }

# ── Root check ──────────────────────────────────────────────
if [[ $EUID -ne 0 ]]; then
    error "This script must be run as root (sudo ./install.sh)"
    exit 1
fi

# ── OS Detection ────────────────────────────────────────────
header "Enterprise Discord Platform Installer"

if [[ ! -f /etc/os-release ]]; then
    error "Cannot detect OS. Only Ubuntu 22.04/24.04 is supported."
    exit 1
fi

source /etc/os-release
if [[ "$ID" != "ubuntu" ]]; then
    error "Unsupported OS: $ID. Only Ubuntu is supported."
    exit 1
fi

log "Detected: $PRETTY_NAME"

# ── Configuration Variables ─────────────────────────────────
INSTALL_DIR="/opt/discord-bot"
BOT_USER="discordbot"
REPO_URL="https://github.com/PBtoolsfree/DC_bot.git"
PYTHON_VERSION="3.10"
NODE_VERSION="20"

# ── Interactive Prompts ─────────────────────────────────────

header "Configuration"

read -rp "$(echo -e "${CYAN}Enter Discord Bot Token: ${NC}")" DISCORD_TOKEN < /dev/tty
while [[ -z "$DISCORD_TOKEN" ]]; do
    error "Bot token is required."
    read -rp "$(echo -e "${CYAN}Enter Discord Bot Token: ${NC}")" DISCORD_TOKEN < /dev/tty
done

read -rp "$(echo -e "${CYAN}Enter Discord OAuth2 Client ID: ${NC}")" OAUTH2_CLIENT_ID < /dev/tty
read -rp "$(echo -e "${CYAN}Enter Discord OAuth2 Client Secret: ${NC}")" OAUTH2_CLIENT_SECRET < /dev/tty
read -rp "$(echo -e "${CYAN}Enter Bot Owner Discord ID(s) (comma-separated): ${NC}")" OWNER_IDS < /dev/tty
read -rp "$(echo -e "${CYAN}Enter your domain name (e.g. bot.example.com): ${NC}")" DOMAIN_NAME < /dev/tty
read -rp "$(echo -e "${CYAN}Enter email for SSL certificates: ${NC}")" SSL_EMAIL < /dev/tty

# Auto-generate secrets
DB_PASSWORD=$(openssl rand -hex 24)
REDIS_PASSWORD=$(openssl rand -hex 24)
JWT_SECRET=$(openssl rand -hex 32)

info "Database password auto-generated."
info "Redis password auto-generated."
info "JWT secret auto-generated."

# ── Docker Mode ─────────────────────────────────────────────
echo ""
echo -e "${CYAN}Installation Mode:${NC}"
echo "  1) Native (recommended for Oracle Always Free — lower RAM)"
echo "  2) Docker Compose"
read -rp "$(echo -e "${CYAN}Select [1/2]: ${NC}")" INSTALL_MODE < /dev/tty
INSTALL_MODE=${INSTALL_MODE:-1}

USE_SSL="y"
read -rp "$(echo -e "${CYAN}Install SSL with Certbot? [Y/n]: ${NC}")" USE_SSL < /dev/tty
USE_SSL=${USE_SSL:-y}

echo ""
echo -e "${BOLD}═══════════════════════════════════════${NC}"
echo -e "  Token:    ${DISCORD_TOKEN:0:10}..."
echo -e "  Domain:   ${DOMAIN_NAME}"
echo -e "  Mode:     $([ "$INSTALL_MODE" = "1" ] && echo "Native" || echo "Docker")"
echo -e "  SSL:      ${USE_SSL}"
echo -e "${BOLD}═══════════════════════════════════════${NC}"
echo ""
read -rp "$(echo -e "${YELLOW}Proceed with installation? [Y/n]: ${NC}")" CONFIRM < /dev/tty
CONFIRM=${CONFIRM:-y}
if [[ "${CONFIRM,,}" != "y" ]]; then
    error "Installation cancelled."
    exit 0
fi

# ── System Update ───────────────────────────────────────────
header "System Setup"

log "Updating system packages..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get upgrade -y -qq

# ── Install System Dependencies ─────────────────────────────
log "Installing system dependencies..."
apt-get install -y -qq \
    git curl wget unzip software-properties-common \
    build-essential gcc g++ make \
    python3 python3-venv python3-pip python3-dev \
    libffi-dev libssl-dev libpq-dev \
    libjpeg-dev libpng-dev zlib1g-dev \
    libpango-1.0-0 libpangocairo-1.0-0 libcairo2 libgdk-pixbuf-2.0-0 \
    ffmpeg fonts-liberation fonts-dejavu-core \
    ufw fail2ban logrotate chrony \
    postgresql postgresql-contrib \
    redis-server \
    nginx certbot python3-certbot-nginx \
    jq acl

# ── Node.js ─────────────────────────────────────────────────
if ! command -v node &>/dev/null; then
    log "Installing Node.js ${NODE_VERSION}..."
    curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | bash -
    apt-get install -y -qq nodejs
fi
log "Node.js $(node --version) installed."

# ── Swap (Oracle Always Free = 1GB RAM) ─────────────────────
header "Oracle Cloud Optimization"

TOTAL_RAM_MB=$(free -m | awk '/^Mem:/{print $2}')
if [[ $TOTAL_RAM_MB -lt 2048 ]]; then
    if [[ ! -f /swapfile ]]; then
        log "Creating 2GB swap (low RAM detected: ${TOTAL_RAM_MB}MB)..."
        fallocate -l 2G /swapfile
        chmod 600 /swapfile
        mkswap /swapfile
        swapon /swapfile
        echo '/swapfile none swap sw 0 0' >> /etc/fstab
        log "Swap enabled."
    else
        info "Swap already exists."
    fi
fi

# ── Sysctl Tuning ───────────────────────────────────────────
log "Applying kernel optimizations..."
cat > /etc/sysctl.d/99-discord-bot.conf <<'SYSCTL'
# Network
net.core.somaxconn = 1024
net.ipv4.tcp_max_syn_backlog = 1024
net.ipv4.tcp_tw_reuse = 1
net.ipv4.ip_local_port_range = 1024 65535

# Memory
vm.swappiness = 10
vm.overcommit_memory = 1

# File descriptors
fs.file-max = 65536
SYSCTL
sysctl --system -q

# ── Systemd Limits ──────────────────────────────────────────
mkdir -p /etc/systemd/system.conf.d
cat > /etc/systemd/system.conf.d/limits.conf <<'LIMITS'
[Manager]
DefaultLimitNOFILE=65536
DefaultLimitNPROC=4096
LIMITS
systemctl daemon-reload

# ── Timezone & NTP ──────────────────────────────────────────
timedatectl set-timezone UTC
systemctl enable --now chrony

# ── Automatic Security Updates ──────────────────────────────
log "Configuring automatic security updates..."
apt-get install -y -qq unattended-upgrades
dpkg-reconfigure -plow unattended-upgrades 2>/dev/null || true

# ── PostgreSQL Configuration ────────────────────────────────
header "Database Setup"

log "Configuring PostgreSQL..."
sudo -u postgres psql -c "CREATE USER discord_bot WITH PASSWORD '${DB_PASSWORD}';" 2>/dev/null || true
sudo -u postgres psql -c "ALTER USER discord_bot WITH PASSWORD '${DB_PASSWORD}';" 2>/dev/null || true
sudo -u postgres psql -c "CREATE DATABASE discord_bot OWNER discord_bot;" 2>/dev/null || true
sudo -u postgres psql -c "ALTER DATABASE discord_bot OWNER TO discord_bot;" 2>/dev/null || true
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE discord_bot TO discord_bot;" 2>/dev/null || true

# Tuning for low-memory Oracle VMs
PG_CONF=$(find /etc/postgresql -name postgresql.conf | head -1)
if [[ -n "$PG_CONF" ]]; then
    cat >> "$PG_CONF" <<'PGTUNING'

# Discord Bot Tuning (Oracle Always Free)
shared_buffers = 128MB
effective_cache_size = 256MB
work_mem = 4MB
maintenance_work_mem = 64MB
max_connections = 50
wal_buffers = 4MB
checkpoint_completion_target = 0.9
random_page_cost = 1.1
PGTUNING
    systemctl restart postgresql
fi
log "PostgreSQL configured."

# ── Redis Configuration ─────────────────────────────────────
log "Configuring Redis..."
REDIS_CONF="/etc/redis/redis.conf"
if [[ -f "$REDIS_CONF" ]]; then
    sed -i "s/^# requirepass .*/requirepass ${REDIS_PASSWORD}/" "$REDIS_CONF"
    sed -i "s/^requirepass .*/requirepass ${REDIS_PASSWORD}/" "$REDIS_CONF"
    # If no requirepass line exists, add it
    grep -q "^requirepass" "$REDIS_CONF" || echo "requirepass ${REDIS_PASSWORD}" >> "$REDIS_CONF"

    sed -i 's/^# maxmemory .*/maxmemory 128mb/' "$REDIS_CONF"
    grep -q "^maxmemory " "$REDIS_CONF" || echo "maxmemory 128mb" >> "$REDIS_CONF"
    grep -q "^maxmemory-policy" "$REDIS_CONF" || echo "maxmemory-policy allkeys-lru" >> "$REDIS_CONF"

    systemctl restart redis-server
fi
log "Redis configured."

# ── Create Bot User ─────────────────────────────────────────
header "Application Setup"

if ! id "$BOT_USER" &>/dev/null; then
    useradd -r -m -s /bin/bash "$BOT_USER"
    log "Created system user: $BOT_USER"
fi

# ── Clone Repository ────────────────────────────────────────
if [[ -d "$INSTALL_DIR" ]]; then
    warn "Directory $INSTALL_DIR already exists. Pulling latest..."
    cd "$INSTALL_DIR"
    sudo -u "$BOT_USER" git fetch --all
    sudo -u "$BOT_USER" git reset --hard origin/main
    sudo -u "$BOT_USER" git clean -fd
    sudo -u "$BOT_USER" git pull || true
    sudo -u "$BOT_USER" git submodule update --init --recursive || true
else
    log "Cloning repository..."
    git clone --recurse-submodules "$REPO_URL" "$INSTALL_DIR"
    chown -R "$BOT_USER":"$BOT_USER" "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

# ── Python Virtual Environment ──────────────────────────────
log "Creating Python virtual environment..."
sudo -u "$BOT_USER" python3 -m venv "$INSTALL_DIR/venv"
sudo -u "$BOT_USER" "$INSTALL_DIR/venv/bin/pip" install --upgrade pip setuptools wheel -q
sudo -u "$BOT_USER" "$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt" -q
log "Python dependencies installed."

# ── Frontend Build ──────────────────────────────────────────
if [[ -d "$INSTALL_DIR/dashboard/frontend" ]] && [[ -f "$INSTALL_DIR/dashboard/frontend/package.json" ]]; then
    log "Building Next.js dashboard (this may take a few minutes)..."
    cd "$INSTALL_DIR/dashboard/frontend"
    sudo -u "$BOT_USER" npm install || warn "npm install failed, continuing anyway..."
    sudo -u "$BOT_USER" npm run build || warn "Frontend build failed or skipped."
    cd "$INSTALL_DIR"
else
    info "No frontend package.json found. Skipping frontend build."
fi

# ── Generate .env ───────────────────────────────────────────
header "Environment Configuration"

REDIS_URL="redis://:${REDIS_PASSWORD}@localhost:6379/0"
DATABASE_URL="postgresql+asyncpg://discord_bot:${DB_PASSWORD}@localhost:5432/discord_bot"
DASHBOARD_URL="https://${DOMAIN_NAME}"

cat > "$INSTALL_DIR/.env" <<ENVFILE
# ============================================================
# Auto-generated by install.sh on $(date -u +"%Y-%m-%dT%H:%M:%SZ")
# ============================================================

# Discord
DISCORD_TOKEN=${DISCORD_TOKEN}
DISCORD_CLIENT_ID=${OAUTH2_CLIENT_ID}
DISCORD_CLIENT_SECRET=${OAUTH2_CLIENT_SECRET}
DISCORD_REDIRECT_URI=https://${DOMAIN_NAME}/auth/callback
DISCORD_DEV_GUILD_ID=
BOT_OWNER_IDS=${OWNER_IDS}

# Database
DATABASE_URL=${DATABASE_URL}
DATABASE_ECHO=false
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
DATABASE_POOL_RECYCLE=3600

# Redis
REDIS_URL=${REDIS_URL}
REDIS_MAX_CONNECTIONS=50

# Celery
CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@localhost:6379/1
CELERY_RESULT_BACKEND=redis://:${REDIS_PASSWORD}@localhost:6379/2

# API
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=2

# Dashboard
DASHBOARD_URL=${DASHBOARD_URL}

# Authentication
JWT_SECRET_KEY=${JWT_SECRET}

# OAuth2
OAUTH2_CLIENT_ID=${OAUTH2_CLIENT_ID}
OAUTH2_CLIENT_SECRET=${OAUTH2_CLIENT_SECRET}
OAUTH2_REDIRECT_URI=${DASHBOARD_URL}/api/auth/callback

# JWT
JWT_SECRET_KEY=${JWT_SECRET}
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

# AI
AI_PROVIDER=none
GEMINI_API_KEY=
OPENAI_API_KEY=

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Environment
ENVIRONMENT=production
DEBUG=false

# Sentry
SENTRY_DSN=
ENVFILE

chown "$BOT_USER":"$BOT_USER" "$INSTALL_DIR/.env"
chmod 600 "$INSTALL_DIR/.env"
log ".env generated with secure permissions (600)."

# ── Alembic Migrations ──────────────────────────────────────
log "Running database migrations..."
cd "$INSTALL_DIR"
sudo -u "$BOT_USER" "$INSTALL_DIR/venv/bin/alembic" upgrade head
log "Migrations applied."

# ── Create Data Directories ─────────────────────────────────
mkdir -p "$INSTALL_DIR/data/transcripts" "$INSTALL_DIR/data/backups" "$INSTALL_DIR/logs"
chown -R "$BOT_USER":"$BOT_USER" "$INSTALL_DIR/data" "$INSTALL_DIR/logs"

# ── Systemd Services ───────────────────────────────────────
header "Systemd Services"

cat > /etc/systemd/system/discord-bot.service <<SERVICE
[Unit]
Description=Discord Management Bot
After=network.target postgresql.service redis-server.service
Requires=postgresql.service redis-server.service

[Service]
Type=simple
User=${BOT_USER}
Group=${BOT_USER}
WorkingDirectory=${INSTALL_DIR}
EnvironmentFile=${INSTALL_DIR}/.env
ExecStart=${INSTALL_DIR}/venv/bin/python -m bot
Restart=always
RestartSec=10
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=${INSTALL_DIR}/data ${INSTALL_DIR}/logs
PrivateTmp=true
LimitNOFILE=65536
MemoryMax=384M
StandardOutput=journal
StandardError=journal
SyslogIdentifier=discord-bot

[Install]
WantedBy=multi-user.target
SERVICE

cat > /etc/systemd/system/discord-dashboard.service <<SERVICE
[Unit]
Description=Discord Dashboard API (FastAPI)
After=network.target postgresql.service redis-server.service
Requires=postgresql.service redis-server.service

[Service]
Type=simple
User=${BOT_USER}
Group=${BOT_USER}
WorkingDirectory=${INSTALL_DIR}
EnvironmentFile=${INSTALL_DIR}/.env
ExecStart=${INSTALL_DIR}/venv/bin/uvicorn dashboard.backend.main:app --host 127.0.0.1 --port 8000 --workers 2
Restart=always
RestartSec=5
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true
LimitNOFILE=65536
MemoryMax=512M
StandardOutput=journal
StandardError=journal
SyslogIdentifier=discord-dashboard

[Install]
WantedBy=multi-user.target
SERVICE

cat > /etc/systemd/system/discord-frontend.service <<SERVICE
[Unit]
Description=Discord Dashboard Frontend (Next.js)
After=network.target

[Service]
Type=simple
User=${BOT_USER}
Group=${BOT_USER}
WorkingDirectory=${INSTALL_DIR}/dashboard/frontend
Environment="NODE_ENV=production"
ExecStart=$(command -v npm) run start
Restart=always
RestartSec=5
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true
LimitNOFILE=65536
MemoryMax=512M
StandardOutput=journal
StandardError=journal
SyslogIdentifier=discord-frontend

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable discord-bot discord-dashboard discord-frontend
systemctl restart discord-bot discord-dashboard discord-frontend
log "Systemd services created and started."

# ── Nginx Configuration ────────────────────────────────────
header "Nginx & SSL"

cat > /etc/nginx/sites-available/discord-bot <<NGINX
# Rate limiting
limit_req_zone \$binary_remote_addr zone=api:10m rate=30r/s;
limit_req_zone \$binary_remote_addr zone=auth:10m rate=5r/m;

server {
    listen 80;
    server_name ${DOMAIN_NAME};

    # Security headers
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Frontend
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # API
    location /api/ {
        limit_req zone=api burst=50 nodelay;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 10s;
        proxy_read_timeout 30s;
    }

    location /api/v1/auth/ {
        limit_req zone=auth burst=5 nodelay;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # WebSocket
    location /api/v1/ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_read_timeout 86400;
    }

    # Health
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
    }

    # Deny dotfiles
    location ~ /\\. { deny all; }
}
NGINX

ln -sf /etc/nginx/sites-available/discord-bot /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx
log "Nginx configured."

# SSL
if [[ "${USE_SSL,,}" == "y" ]] && [[ -n "$DOMAIN_NAME" ]] && [[ -n "$SSL_EMAIL" ]]; then
    log "Requesting SSL certificate..."
    certbot --nginx -d "$DOMAIN_NAME" --non-interactive --agree-tos -m "$SSL_EMAIL" --redirect || warn "SSL setup failed. You can retry with: sudo certbot --nginx -d $DOMAIN_NAME"
fi

# ── Firewall ────────────────────────────────────────────────
header "Security"

log "Configuring firewall..."
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
log "UFW enabled (SSH, HTTP, HTTPS)."

# ── Fail2Ban ────────────────────────────────────────────────
log "Configuring Fail2Ban..."
cat > /etc/fail2ban/jail.local <<'F2B'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
action = iptables-multiport[name=ReqLimit, port="http,https"]
logpath = /var/log/nginx/error.log
F2B
systemctl enable --now fail2ban
log "Fail2Ban configured."

# ── Log Rotation ────────────────────────────────────────────
cat > /etc/logrotate.d/discord-bot <<'LOGROTATE'
/opt/discord-bot/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    copytruncate
}
LOGROTATE

# ── Backup Cron ─────────────────────────────────────────────
if [[ -f "$INSTALL_DIR/deploy/backup.sh" ]]; then
    chmod +x "$INSTALL_DIR/deploy/backup.sh"
    crontab -u "$BOT_USER" -l 2>/dev/null | grep -v "backup.sh" | { cat; echo "0 */6 * * * ${INSTALL_DIR}/deploy/backup.sh"; } | crontab -u "$BOT_USER" -
    log "Backup cron installed (every 6 hours)."
fi

# ── Final Summary ───────────────────────────────────────────
header "Installation Complete!"

echo -e "${GREEN}${BOLD}"
echo "  ✅ Discord Bot      → systemctl status discord-bot"
echo "  ✅ Dashboard API    → systemctl status discord-dashboard"
echo "  ✅ PostgreSQL       → systemctl status postgresql"
echo "  ✅ Redis            → systemctl status redis-server"
echo "  ✅ Nginx            → https://${DOMAIN_NAME}"
echo "  ✅ Firewall (UFW)   → ufw status"
echo "  ✅ Fail2Ban         → fail2ban-client status"
echo "  ✅ Auto Backups     → crontab -u ${BOT_USER} -l"
echo ""
echo "  📁 Install Dir:     ${INSTALL_DIR}"
echo "  📁 Logs:            journalctl -u discord-bot -f"
echo "  📁 .env:            ${INSTALL_DIR}/.env"
echo ""
echo "  🔧 Update:          ${INSTALL_DIR}/update.sh"
echo "  🔧 Backup:          ${INSTALL_DIR}/deploy/backup.sh"
echo "  🔧 Verify:          ${INSTALL_DIR}/deploy/verify.sh"
echo -e "${NC}"
