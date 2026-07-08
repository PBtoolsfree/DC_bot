# Enterprise Discord Management Platform

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-00a393)
![Discord.py](https://img.shields.io/badge/discord.py-2.3%2B-5865F2)

A production-grade, enterprise-ready Discord server management platform. Built with Clean Architecture, featuring 12 complete modules for advanced moderation, logging, auto-moderation, anti-nuke security, ticketing, verification, leveling, and a Next.js web dashboard.

## 🚀 Features

*   **Foundation & Dashboard:** Next.js web dashboard, JWT auth, RBAC, settings management.
*   **Moderation & AutoMod:** Advanced moderation tools, robust regex-based auto-moderation, warning systems.
*   **Security & Anti-Nuke:** Raid detection, anti-spam, lockdown protocols, webhook protection.
*   **Enterprise Logging:** Comprehensive audit logging for all server events.
*   **Verification System:** Image/math/word captchas, risk-based verification, alternate account detection.
*   **Ticket System:** Multi-category tickets, anonymous relay mode, HTML/PDF transcripts.
*   **Backup & Restore:** Server state backups, roles, channels, permissions.
*   **Welcome & AutoRole:** Customizable welcome messages, auto-role assignment on join.
*   **Reaction & Self Roles:** Interactive role assignment panels.
*   **Leveling & XP:** Voice and message XP tracking, role rewards, leaderboards.

## 📦 Quick Install (Ubuntu 22.04 / 24.04 & Oracle Cloud)

Deploy the entire platform with a single command on a fresh Ubuntu server:

```bash
curl -fsSL https://raw.githubusercontent.com/your-org/discord-management-platform/main/install.sh | sudo bash
```

See [INSTALL.md](INSTALL.md) for detailed installation instructions.

## 📚 Documentation

*   [Installation Guide](INSTALL.md)
*   [Oracle Cloud Deployment](DEPLOY_ORACLE.md)
*   [Docker Deployment](DOCKER.md)
*   [Update Guide](UPDATE.md)
*   [Backup & Restore](BACKUP.md) / [RESTORE.md](RESTORE.md)
*   [Uninstall Guide](UNINSTALL.md)
*   [FAQ](FAQ.md)
*   [Troubleshooting](TROUBLESHOOTING.md)
*   [Security Policy](SECURITY.md)
*   [Contributing](CONTRIBUTING.md)
*   [Changelog](CHANGELOG.md)

## 🏗️ Architecture

*   **Bot:** Python 3.10, discord.py, SQLAlchemy 2.0 (Async), asyncpg.
*   **API:** FastAPI, JWT authentication, Uvicorn.
*   **Frontend:** Next.js 14, Tailwind CSS, TypeScript.
*   **Database:** PostgreSQL 16.
*   **Cache & PubSub:** Redis 7.

## 🛡️ License

This project is licensed under the MIT License - see the LICENSE file for details.
