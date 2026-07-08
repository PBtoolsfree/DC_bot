# Modules 9-12 Enterprise Guide

This document outlines the architecture for the Enterprise Leveling, Roles, Welcome, and Backup modules.

## Module 9: Backup & Restore
- **Provider Pattern**: By default, uses `PostgresStorageProvider` to serialize backups as JSON straight into the database. `BackupStorageProvider` allows hooking into S3 or R2 easily in the future.
- **Restore Logic**: The engine is inherently destructive. Always utilize the "Diff" functionality to preview what will be deleted and recreated before execution.
- **Rollbacks**: If a restore fails midway, the system logs a `BACKUP_FAILED` event. Future enhancements include automatic rollback snapshots right before restore execution.

## Module 10: Welcome & Autorole
- **Image Generation**: Uses `PillowImageProvider` natively within Python to generate 800x250 Welcome Cards and XP Rank Cards without requiring external dependencies or heavy browser instances.
- **Autoroles**: Supports instant roles on join or delayed roles via the `GlobalSchedulerTask`. It supports targeting humans vs bots separately.

## Module 11: Reaction & Self Roles
- **Validation Engine**: Built cleanly in `ReactionRoleService`. It enforces minimums, maximums, required roles, and blacklists. If `max_roles=1` is set, the system automatically swaps roles instead of blocking the user, creating a smooth "Single Choice" UI experience.
- **Components**: The dashboard triggers `ReactionRoleView`, dynamically building Discord Buttons from the database state.

## Module 12: Leveling & XP
- **Provider Pattern**: XP sources are endless. I've built `MessageXPProvider` (with cooldown caching in Redis) and `VoiceXPProvider` (time-based XP).
- **Voice Tracking**: `VoiceSessionService` tracks state changes (`on_voice_state_update`) and calculates minutes. The `GlobalSchedulerTask` periodically commits this XP to the database to ensure users don't lose XP if the bot restarts mid-call.
- **Rewards**: Handled automatically in the `XPService` state machine on level up.
