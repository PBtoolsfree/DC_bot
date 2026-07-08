# Troubleshooting Guide

## Bot Fails to Start

### 1. `asyncpg.exceptions.InvalidPasswordError`
**Issue:** The bot cannot connect to PostgreSQL.
**Fix:** Verify the `DATABASE_URL` in `.env`. Ensure the password exactly matches what you set when creating the database user. If using Docker, ensure `POSTGRES_PASSWORD` matches the URL.

### 2. `discord.errors.LoginFailure: Improper token has been passed.`
**Issue:** Invalid Discord Bot Token.
**Fix:** Reset your token in the Discord Developer Portal and update `DISCORD_TOKEN` in your `.env` file. Do not include `Bot ` prefix in the .env file.

### 3. `ModuleNotFoundError: No module named 'weasyprint'`
**Issue:** Missing Python dependencies or system libraries.
**Fix:** Run `pip install -r requirements.txt`. If it fails during building, ensure system dependencies are installed: `sudo apt install libffi-dev libssl-dev libpango-1.0-0 libcairo2`.

---

## Dashboard / API Issues

### 1. CORS Errors in Browser Console
**Issue:** The frontend cannot communicate with the API due to Cross-Origin Resource Sharing restrictions.
**Fix:** Ensure `DASHBOARD_URL` in `.env` exactly matches the URL you are visiting in the browser (including `https://` and no trailing slash). The backend uses this to set the `allow_origins` header.

### 2. "502 Bad Gateway" from Nginx
**Issue:** Nginx is running, but the FastAPI backend is down.
**Fix:** Check backend logs:
```bash
sudo journalctl -u discord-dashboard -n 50
# or for Docker
docker compose logs dashboard-api
```
Usually caused by an invalid `.env` configuration crashing the FastAPI process on startup.

---

## Database Migration Issues

### 1. `alembic.util.exc.CommandError: Can't locate revision identified by 'head'`
**Issue:** Alembic history is corrupted or missing.
**Fix:** Check the `alembic/versions/` directory. If the files are there, check the `alembic_version` table in PostgreSQL.
To force sync (WARNING: Ensure your DB schema actually matches the code):
```bash
alembic stamp head
```

### 2. `sqlalchemy.exc.OperationalError: FATAL: too many clients already`
**Issue:** PostgreSQL connection limit reached.
**Fix:** Check `.env` and lower `DATABASE_POOL_SIZE` and `DATABASE_MAX_OVERFLOW`. If using Oracle Cloud Always Free, keep `POOL_SIZE=20`.

---

## Performance Issues (Oracle Cloud Always Free)

### Bot is randomly killed (OOM)
**Issue:** The OS is killing the bot because it ran out of RAM.
**Fix:** Check if swap is enabled: `free -h`. If swap is 0, run the One-Click installer again or manually create a 2GB swap file:
```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```
