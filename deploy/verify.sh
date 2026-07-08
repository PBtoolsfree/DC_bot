#!/usr/bin/env bash
# ============================================================
# Production Verification Script
# ============================================================
# Usage: sudo ./deploy/verify.sh
# ============================================================

set -uo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

PASS=0; WARN=0; FAIL=0

check_pass() { echo -e "  ${GREEN}✅ PASS${NC}  $1"; ((PASS++)); }
check_warn() { echo -e "  ${YELLOW}⚠️  WARN${NC}  $1"; ((WARN++)); }
check_fail() { echo -e "  ${RED}❌ FAIL${NC}  $1"; ((FAIL++)); }

echo -e "\n${BOLD}${CYAN}══════════════════════════════════════════${NC}"
echo -e "${BOLD} Production Deployment Verification${NC}"
echo -e "${BOLD}${CYAN}══════════════════════════════════════════${NC}\n"

INSTALL_DIR="/opt/discord-bot"

# ── System ──────────────────────────────────────────────────
echo -e "${BOLD}System${NC}"
command -v python3 &>/dev/null && check_pass "Python3 $(python3 --version 2>&1 | cut -d' ' -f2)" || check_fail "Python3 not found"
command -v node &>/dev/null && check_pass "Node.js $(node --version)" || check_warn "Node.js not found"
command -v nginx &>/dev/null && check_pass "Nginx installed" || check_fail "Nginx not found"

# ── Services ────────────────────────────────────────────────
echo -e "\n${BOLD}Services${NC}"
systemctl is-active --quiet postgresql && check_pass "PostgreSQL running" || check_fail "PostgreSQL not running"
systemctl is-active --quiet redis-server && check_pass "Redis running" || check_fail "Redis not running"
systemctl is-active --quiet nginx && check_pass "Nginx running" || check_fail "Nginx not running"
systemctl is-active --quiet discord-bot && check_pass "Discord Bot running" || check_fail "Discord Bot not running"
systemctl is-active --quiet discord-dashboard && check_pass "Dashboard API running" || check_fail "Dashboard API not running"

# ── Connectivity ────────────────────────────────────────────
echo -e "\n${BOLD}Connectivity${NC}"
curl -sf http://localhost:8000/health > /dev/null 2>&1 && check_pass "API Health endpoint responding" || check_fail "API Health endpoint not responding"
sudo -u postgres psql -c "SELECT 1;" &>/dev/null && check_pass "PostgreSQL accepting connections" || check_fail "PostgreSQL connection failed"
redis-cli ping &>/dev/null && check_pass "Redis accepting connections" || check_fail "Redis connection failed"

# ── Security ────────────────────────────────────────────────
echo -e "\n${BOLD}Security${NC}"
ufw status | grep -q "Status: active" && check_pass "UFW firewall active" || check_warn "UFW not active"
systemctl is-active --quiet fail2ban && check_pass "Fail2Ban running" || check_warn "Fail2Ban not running"
[[ -f "$INSTALL_DIR/.env" ]] && [[ $(stat -c %a "$INSTALL_DIR/.env") == "600" ]] && check_pass ".env permissions (600)" || check_warn ".env permissions not restricted"

# ── SSL ─────────────────────────────────────────────────────
echo -e "\n${BOLD}SSL${NC}"
DOMAIN=$(grep "DASHBOARD_URL" "$INSTALL_DIR/.env" 2>/dev/null | cut -d'=' -f2 | sed 's|https://||')
if [[ -n "$DOMAIN" ]]; then
    curl -sf "https://${DOMAIN}/health" > /dev/null 2>&1 && check_pass "SSL working for $DOMAIN" || check_warn "SSL not verified for $DOMAIN"
else
    check_warn "No domain configured"
fi

# ── Resources ───────────────────────────────────────────────
echo -e "\n${BOLD}Resources${NC}"
DISK_USED=$(df -h / | awk 'NR==2{print $5}' | tr -d '%')
RAM_USED=$(free | awk '/^Mem:/{printf "%.0f", $3/$2*100}')
[[ $DISK_USED -lt 80 ]] && check_pass "Disk usage: ${DISK_USED}%" || check_warn "Disk usage high: ${DISK_USED}%"
[[ $RAM_USED -lt 90 ]] && check_pass "RAM usage: ${RAM_USED}%" || check_warn "RAM usage high: ${RAM_USED}%"
swapon --show | grep -q "/" && check_pass "Swap enabled" || check_warn "No swap configured"

# ── Environment ─────────────────────────────────────────────
echo -e "\n${BOLD}Environment${NC}"
[[ -f "$INSTALL_DIR/.env" ]] && check_pass ".env file exists" || check_fail ".env missing"
[[ -d "$INSTALL_DIR/venv" ]] && check_pass "Virtual environment exists" || check_fail "venv missing"
grep -q "ENVIRONMENT=production" "$INSTALL_DIR/.env" 2>/dev/null && check_pass "Production mode" || check_warn "Not in production mode"

# ── Summary ─────────────────────────────────────────────────
TOTAL=$((PASS + WARN + FAIL))
echo -e "\n${BOLD}${CYAN}══════════════════════════════════════════${NC}"
echo -e "  ${GREEN}Passed: $PASS${NC}  ${YELLOW}Warnings: $WARN${NC}  ${RED}Failed: $FAIL${NC}  Total: $TOTAL"

if [[ $FAIL -eq 0 ]]; then
    echo -e "\n  ${GREEN}${BOLD}🎉 Deployment is HEALTHY${NC}\n"
elif [[ $FAIL -le 2 ]]; then
    echo -e "\n  ${YELLOW}${BOLD}⚠️  Deployment has minor issues${NC}\n"
else
    echo -e "\n  ${RED}${BOLD}❌ Deployment has critical issues${NC}\n"
fi
echo -e "${BOLD}${CYAN}══════════════════════════════════════════${NC}\n"
