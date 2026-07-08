import re

def fix(path, old, new):
    with open(path, "r", encoding="utf-8") as f:
        c = f.read()
    c = c.replace(old, new)
    with open(path, "w", encoding="utf-8") as f:
        f.write(c)

# postgres_provider.py
fix("bot/services/backup/providers/postgres_provider.py",
    '"""The payload is already stored in the ServerBackup.payload column. We just return a pg URI."""',
    '"""The payload is already stored in the ServerBackup.payload column.\n        We just return a pg URI."""')

# restore_service.py
fix("bot/services/backup/restore_service.py",
    "session: AsyncSession, guild: discord.Guild, backup_id: int",
    "session: AsyncSession, _guild: discord.Guild, backup_id: int")

# history_service.py
fix("bot/services/history_service.py",
    'description=f"**Total Actions:** {total_actions}\\n**Active Warnings:** {active_warnings}",',
    'description=f"**Total Actions:** {total_actions}\\n"\n                            f"**Active Warnings:** {active_warnings}",')

# export_service.py
fix("bot/services/logging/export_service.py",
    '"<style>body { font-family: sans-serif; } table { border-collapse: collapse; width: 100%; }",',
    '"<style>body { font-family: sans-serif; } "\n            "table { border-collapse: collapse; width: 100%; }",')
fix("bot/services/logging/export_service.py",
    '"th, td { border: 1px solid #ddd; padding: 8px; } th { background-color: #f2f2f2; }</style>",',
    '"th, td { border: 1px solid #ddd; padding: 8px; } "\n            "th { background-color: #f2f2f2; }</style>",')

# logging_service.py
fix("bot/services/logging/logging_service.py",
    "if not target_channels and not is_immutable:\n            # If no channel is listening and it's not a forced immutable log, we might skip\n            # to save DB space, but enterprise systems log everything.\n            # However, for performance we'll only log if it's routed or if severity is high.\n            if severity < 3:",
    "if not target_channels and not is_immutable and severity < 3:\n            # If no channel is listening and it's not a forced immutable log, we might skip\n            # to save DB space, but enterprise systems log everything.\n            # However, for performance we'll only log if it's routed or if severity is high.")
log_code = """                    try:
                        await dest_channel.send(embed=embed)
                    except discord.HTTPException:
                        pass  # Permissions issue or channel deleted"""
log_new = """                    import contextlib
                    with contextlib.suppress(discord.HTTPException):
                        await dest_channel.send(embed=embed)"""
fix("bot/services/logging/logging_service.py", log_code, log_new)

# streaming_service.py
fix("bot/services/logging/streaming_service.py",
    "# In a real implementation, this would hold a reference to an aioredis connection or a WebSocket server",
    "# In a real implementation, this would hold a reference to an aioredis connection\n        # or a WebSocket server")

# moderation_service.py
fix("bot/services/moderation_service.py",
    'raise ModerationError(f"Invalid regex pattern: {e}")',
    'raise ModerationError(f"Invalid regex pattern: {e}") from None')

# punishment_service.py
fix("bot/services/punishment_service.py",
    '# Structure: {"warn_thresholds": {"3": {"action": "timeout", "duration": 3600}, "5": {"action": "kick"}}}',
    '# Structure: {"warn_thresholds": {"3": {"action": "timeout", "duration": 3600}, "5": ...}}')

# raid_detection_service.py
fix("bot/services/security/raid_detection_service.py",
    "# Using a slight microsecond offset or just current_time if we don't care about exact uniqueness",
    "# Using a slight microsecond offset or just current_time")
fix("bot/services/security/raid_detection_service.py",
    "# For simplicity in this implementation, we will use an incrementing counter or random string.",
    "# For simplicity we will use an incrementing counter or random string.")

# rollback_service.py
roll_code = """            if any(getattr(role.permissions, perm, False) for perm in dangerous_perms):
                if role < member.guild.me.top_role:"""
roll_new = """            if any(getattr(role.permissions, perm, False) for perm in dangerous_perms) and role < member.guild.me.top_role:"""
fix("bot/services/security/rollback_service.py", roll_code, roll_new)

# security_service.py
fix("bot/services/security/security_service.py",
    "# For Anti-Nuke, we track by executor. For Anti-Raid (e.g. mass join), we track globally for the guild.",
    "# For Anti-Nuke, we track by executor.\n        # For Anti-Raid (e.g. mass join), we track globally for the guild.")

# transcript_service.py
fix("bot/services/tickets/transcript_service.py",
    'filename = f"ticket_{ticket.id}_{dt.datetime.now(dt.timezone.utc).strftime(\'%Y%m%d%H%M%S\')}{provider.extension}"',
    'now_str = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d%H%M%S")\n        filename = f"ticket_{ticket.id}_{now_str}{provider.extension}"')
