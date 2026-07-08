# Enterprise Logging & Audit System Guide

The Management Bot Logging System tracks every critical event in your server, from deleted messages and voice channel moves to role changes and automated moderation actions.

## Architecture

Unlike simple bots that immediately push a message to a Discord channel, this bot utilizes a robust **ActionLog** database architecture.

1. **Database-First**: Every event is instantly stored in the `action_logs` database table.
2. **Correlation IDs**: Each action gets a unique UUID, allowing you to trace complex chains of events across the dashboard and Discord.
3. **Data Masking**: Emails and IP addresses in message content are masked before storage by default (configurable).
4. **Discord Push**: Once stored, the system builds an enterprise-formatted embed and pushes it to your designated logging channels.

## Available Modules

You can route different event types to different channels. Available categories include:
- `Message`: message_delete, message_edit, bulk_delete, message_pin
- `Member`: member_join, member_leave, nick_change, role_update, avatar_change
- `Server`: channel_create/delete/update, role_create/delete/update, emoji/sticker updates
- `Voice`: voice_join, voice_leave, voice_move, voice_mute, voice_deaf
- `Advanced`: thread_create, webhook_create, stage_event, scheduled_event
- `Security`: automod_violation, security_incident, moderation_action

## Searching Logs

You don't need to scroll endlessly through a `#message-logs` channel. Use the `/logs search` slash command to quickly filter the database!

**/logs search action:message_delete user:@RogueUser days:7**
This will instantly return the last 10 messages deleted by `@RogueUser` in the past week.

## Exporting Logs

For enterprise compliance, you can export your server's logs using `/logs export`.
The bot will compile the thousands of `ActionLog` entries into your chosen format:
- **CSV**: Perfect for Excel or Google Sheets.
- **JSON**: Perfect for API integration.
- **HTML**: A clean, readable timeline.

## Data Retention
To prevent database bloat, the system includes an automated background worker (`RetentionService`).
By default, logs are kept for **30 days** before being purged. Server Administrators can modify this retention period via the web dashboard.
