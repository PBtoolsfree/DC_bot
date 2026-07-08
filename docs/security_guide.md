# Enterprise Security & Anti-Nuke Guide

The Management Bot Security System protects your server from rogue admins, token-logged moderators, and coordinated raids. It operates with enterprise-grade caching, background rollbacks, and risk-assessment engines.

## Overview

The security system runs multiple independent background services:

1. **Raid Detection Engine**: Tracks velocity of user actions (e.g., joins per minute, pings per second) using highly-available Redis sliding windows.
2. **Anti-Nuke Rollback Service**: Reverts destructive actions (e.g., mass channel deletions) automatically.
3. **Risk Health Engine**: Evaluates your server's configuration and role permissions to assign a security score (0-100).
4. **Snapshot Manager**: Creates full backups of your channels, categories, and roles for disaster recovery.

## Configuration

Security settings are managed via the web dashboard (or database JSON) under the `security` module.

### Anti-Nuke Rules
Each Anti-Nuke rule supports custom thresholds and actions. Supported rules:
- `channel_create`, `channel_delete`, `channel_update`
- `role_create`, `role_delete`, `role_update`
- `webhook_create`, `webhook_delete`
- `emoji_create`, `emoji_delete`
- `sticker_create`, `sticker_delete`
- `member_ban`, `member_kick`

### Anti-Raid Rules
- `mass_join`
- `invite_spam`
- `everyone_ping`
- `bot_add`

## Simulation Mode
Before deploying punishments in a production environment, you can enable `simulation_mode`. When active, the bot will log triggers and send alerts to the `log_channel_id` but will **not** ban members or strip permissions.

## Snapshots & Rollbacks
You can manually create a server snapshot using `/security snapshot`. Automatic weekly backups run in the background via the `SecurityTasksCog`.

In the event of an Anti-Nuke trigger (e.g. 5 channels deleted in 10 seconds), the `RollbackService` will immediately attempt to recreate the deleted channels and restore their positions/permissions using the most recent Discord Audit Log entries.

## Risk Score
Use `/security status` to view your server's Health Score. The engine deducts points for:
- Lack of Community/Verification requirements.
- Too many administrative roles.
- Missing crucial Anti-Nuke rules.
