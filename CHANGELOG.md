# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-07-08

### Added
- **Phase 1 Production Release**
- **Module 1 - Foundation:** Custom bot subclass, lifecycle management, database engine, dependency injection.
- **Module 2 - Moderation:** Warnings, kicks, bans, mutes, purge with comprehensive DB tracking.
- **Module 3 - Auto Moderation:** Regex-based rule engine, link filtering, caps/spam detection.
- **Module 4 - Security & Anti-Nuke:** Raid detection, webhook protection, channel/role lockdown protocols.
- **Module 5 - Enterprise Logging & Audit:** Detailed webhook-based logging for all guild events.
- **Module 6 - Enterprise Dashboard:** FastAPI backend with JWT auth, RBAC, and WebSocket streaming.
- **Module 7 - Enterprise Verification:** Captcha generation (Image, Math, Word) with dynamic risk scoring.
- **Module 8 - Enterprise Ticket System:** Redis-backed anonymous relay, HTML/PDF transcripts.
- **Module 9 - Backup & Restore:** Server state serialization for roles, channels, and permissions.
- **Module 10 - Welcome & AutoRole:** Customizable welcome embeds and dynamic role assignment on join.
- **Module 11 - Reaction & Self Roles:** Interactive panels with multiple restriction modes (unique, verify).
- **Module 12 - Enterprise Leveling:** Message and Voice XP tracking with dynamic cooldowns and role rewards.
- **Deployment Automation:** One-click installer for Ubuntu/Oracle Cloud, automated update, backup, and restore scripts.
- **Infrastructure:** Full Docker Compose support, systemd service generation, Nginx reverse proxy configuration.
- **CI/CD:** GitHub Actions pipeline for linting, type-checking, and pytest validation.

### Changed
- Complete architecture migration to async SQLAlchemy 2.0.
- Unified configuration via Pydantic Settings.

### Fixed
- Stabilized Redis fallback logic during high load.
- Resolved memory leak in WeasyPrint PDF generation by offloading to isolated processes.
