# Update Guide

To keep your Enterprise Discord Management Platform up to date, we provide an automated update script that handles pulling changes, updating dependencies, running migrations, and restarting services safely.

## Automated Update (Recommended)

Run the included update script with root privileges:

```bash
cd /opt/discord-bot
sudo ./update.sh
```

### What `update.sh` Does:
1.  **Pre-flight Backup:** Creates a database dump and backs up your `.env` file to `data/backups/`.
2.  **Git Pull:** Fetches the latest changes from the `main` branch.
3.  **Dependencies:** Updates Python and Node.js dependencies.
4.  **Frontend Build:** Rebuilds the Next.js dashboard if changes were made.
5.  **Database Migrations:** Runs `alembic upgrade head`. **If this fails, it automatically rolls back your database using the pre-flight backup.**
6.  **Service Restart:** Restarts the Discord Bot and Dashboard API systemd services.
7.  **Verification:** Checks if services started successfully.

## Manual Update (Docker)

If you deployed using Docker Compose:

```bash
cd /opt/discord-bot

# 1. Pull latest code
git pull

# 2. Rebuild images
docker compose build

# 3. Apply migrations
docker compose exec bot alembic upgrade head

# 4. Restart services
docker compose up -d
```

## Manual Update (Bare Metal)

If you prefer to update manually:

```bash
cd /opt/discord-bot

# 1. Pull changes
git pull

# 2. Update Python dependencies
source venv/bin/activate
pip install -r requirements.txt

# 3. Run migrations
alembic upgrade head

# 4. Rebuild frontend
cd dashboard/frontend
npm install
npm run build
cd ../../

# 5. Restart services
sudo systemctl restart discord-bot discord-dashboard
```
