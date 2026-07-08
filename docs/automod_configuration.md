# AutoMod Configuration Guide

The Discord Management Platform features a highly customizable, enterprise-grade AutoMod system. Configuration is stored per-guild in the database as a JSON blob inside the `GuildModuleSettings` model.

This guide explains the structure of the JSON payload.

## Master Schema Structure

```json
{
  "spam_messages": {
    "enabled": true,
    "threshold": 5,
    "cooldown_seconds": 10,
    "actions": [
      {
        "type": "warn",
        "message": "Please slow down your messages."
      },
      {
        "type": "timeout",
        "duration_seconds": 3600
      }
    ],
    "ignored_roles": [123456789012345678],
    "ignored_channels": [987654321098765432]
  },
  "links_invites": {
    "enabled": true,
    "whitelist": ["allowed_server_code"],
    "actions": [{"type": "delete"}]
  },
  "escalation_rules": [
    {
      "violation_count": 3,
      "time_window_seconds": 3600,
      "actions": [{"type": "kick"}]
    },
    {
      "violation_count": 5,
      "time_window_seconds": 86400,
      "actions": [{"type": "ban"}]
    }
  ]
}
```

## Available Rule Categories

- `spam_messages`: Message flood detection.
- `spam_caps`: Excessive capitalization (threshold is %).
- `spam_emojis`: Excessive emojis.
- `spam_mentions`: Mentions in a single message.
- `spam_mass_mentions`: Mentions across multiple messages (cooldown_seconds).
- `spam_duplicates`: Duplicate message text detection.
- `links_invites`: Discord invite links.
- `links_external`: Generic external links.
- `links_scam`: Malicious/phishing domains.
- `words_profanity`: Bad words (supports leetspeak parsing).
- `words_regex`: Advanced pattern matching.
- `abuse_zalgo`: Zalgo/glitch text.
- `abuse_invisible`: Zero-width characters.

## Actions

The following punishments are supported under `"type"`:

- `delete`: Deletes the offending message.
- `warn`: Issues a formal warning and logs to the DB.
- `timeout`: Applies a Discord timeout (requires `duration_seconds`).
- `kick`: Removes the user from the server.
- `ban`: Permanently bans the user.
- `softban`: Bans and immediately unbans to clear recent messages.
- `lock_channel`: Prevents anyone from sending messages in the channel.
- `slowmode`: Applies a channel slowmode (requires `duration_seconds`).
- `notify_staff`: Sends a discrete alert to the staff log.
- `dm_user`: Sends a direct message to the offender.

## Escalations

Escalation rules allow you to increase the severity of punishments for repeat offenders. If a user triggers *any* AutoMod rule, their recent history is checked against `escalation_rules`.

If they meet the `violation_count` within the `time_window_seconds`, the default actions of the rule are **overridden** by the escalation actions.
