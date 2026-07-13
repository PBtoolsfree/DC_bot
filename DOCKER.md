# Docker Deployment Guide

The platform includes full Docker support via multi-stage Dockerfiles and `docker-compose.yml`. This is the recommended deployment method for servers with >2GB RAM.

## Prerequisites
- Docker Engine 24+
- Docker Compose v2

## 1. Setup

```bash
# Clone the repository
git clone https://github.com/PBtoolsfree/DC_bot.git
cd DC_bot

# Generate secure secrets and configure .env
cp .env.production .env
nano .env 
```
*Note: Follow the instructions in `.env.production` to generate random secure hex strings for passwords and JWT keys.*

## 2. Start Services

Bring up the entire stack (PostgreSQL, Redis, Bot, Dashboard API, Nginx):

```bash
docker compose up -d
```

Check the status to ensure everything is healthy:
```bash
docker compose ps
```

## 3. Run Database Migrations

Once the database is up, you must apply the initial migrations:

```bash
docker compose exec bot alembic upgrade head
```

## 4. Viewing Logs

View combined logs:
```bash
docker compose logs -f
```

View specific service logs:
```bash
docker compose logs -f bot
docker compose logs -f dashboard-api
```

## 5. Updating

To update a Docker deployment:

```bash
git pull
docker compose build
docker compose up -d
docker compose exec bot alembic upgrade head
```

## Architecture Notes

*   **Network:** All services communicate on an internal Docker network. Only Nginx exposes ports 80/443 to the host.
*   **Volumes:**
    *   `pgdata`: Persistent PostgreSQL storage.
    *   `redisdata`: Persistent Redis storage.
    *   `bot_data`: Application data (transcripts, etc.).
*   **Reverse Proxy:** The included Nginx container routes `/api/*` and `/ws/*` to the FastAPI backend and serves the frontend. It includes built-in rate limiting and security headers.
