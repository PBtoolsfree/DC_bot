"""Master Security Service orchestrator."""

from __future__ import annotations

import discord
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.schemas.security import SecuritySettings
from bot.services.security.incident_service import IncidentService
from bot.services.security.raid_detection_service import RaidDetectionService
from bot.services.security.rollback_service import RollbackService
from bot.services.security.whitelist_service import WhitelistService
from bot.utils.logger import get_logger

logger = get_logger(__name__)


class SecurityService:
    """Master orchestrator for all security-related features."""

    def __init__(self, raid_service: RaidDetectionService, bot_owner_ids: set[int]) -> None:
        self.raid_service = raid_service
        self.bot_owner_ids = bot_owner_ids

    async def handle_action(
        self,
        session: AsyncSession,
        guild: discord.Guild,
        settings: SecuritySettings,
        action_type: str,
        executor: discord.Member,
        target_id: int | None = None,
        audit_entry: discord.AuditLogEntry | None = None,
    ) -> bool:
        """Handle a security action event. Returns True if a punishment was triggered."""
        if not settings.enabled:
            return False

        # 1. Whitelist Check
        if WhitelistService.is_exempt(executor, settings.whitelist, self.bot_owner_ids):
            return False

        # 2. Get relevant rule (Anti-Nuke or Anti-Raid)
        rule = None
        is_nuke = False

        if action_type.startswith("anti_raid_"):
            rule = getattr(settings.anti_raid, action_type.replace("anti_raid_", ""), None)
        else:
            rule = getattr(settings.anti_nuke, action_type, None)
            is_nuke = True

        if not rule or not rule.enabled:
            return False

        # 3. Check Velocity / Raid Tracker
        # For Anti-Nuke, we track by executor. For Anti-Raid (e.g. mass join), we track globally for the guild.
        tracker_target = executor.id if is_nuke else None

        exceeded = await self.raid_service.add_action_and_check(
            guild_id=guild.id, action_type=action_type, rule=rule, target_id=tracker_target
        )

        if not exceeded:
            return False

        # 4. Trigger Defense Protocol
        logger.warning(
            "security.threshold_exceeded",
            guild_id=guild.id,
            executor_id=executor.id,
            action=action_type,
        )

        # Determine simulation mode
        if settings.simulation_mode.enabled:
            await IncidentService.log_incident(
                session=session,
                guild=guild,
                action=f"SIMULATION: {action_type}",
                executor_id=executor.id,
                target_id=target_id,
                reason="Threshold exceeded (Simulation Mode Active)",
                log_channel_id=settings.simulation_mode.log_channel_id or settings.log_channel_id,
            )
            return True

        # Apply Punishment
        punishment_success = await self._apply_punishment(executor, rule.action, action_type)

        # Queue Rollback if applicable
        rollback_status = "NONE"
        if is_nuke and audit_entry:
            rollback_status = await self._queue_rollback(guild, action_type, audit_entry)

        # Log Incident
        await IncidentService.log_incident(
            session=session,
            guild=guild,
            action=action_type,
            executor_id=executor.id,
            target_id=target_id,
            reason=f"Security Threshold Exceeded. Punishment: {rule.action}.",
            rollback_status=rollback_status,
            log_channel_id=settings.log_channel_id,
        )

        # [NEW ENTERPRISE FEATURE] Broadcast Live Dashboard Event Stub
        self._broadcast_dashboard_event(
            guild.id, "security_trigger", {"action": action_type, "executor": executor.id}
        )

        return True

    async def _apply_punishment(self, member: discord.Member, action: str, reason: str) -> bool:
        """Apply the configured punishment to the executor."""
        try:
            full_reason = f"Security Auto-Punish: {reason}"
            if action == "ban":
                await member.ban(reason=full_reason)
            elif action == "kick":
                await member.kick(reason=full_reason)
            elif action == "remove_roles":
                await RollbackService.strip_dangerous_roles(member, reason=full_reason)
            elif action == "timeout":
                from datetime import datetime, timedelta, timezone

                await member.timeout(
                    datetime.now(timezone.utc) + timedelta(hours=1), reason=full_reason
                )
            return True
        except discord.Forbidden:
            return False
        except discord.HTTPException:
            return False

    async def _queue_rollback(
        self, guild: discord.Guild, action_type: str, audit_entry: discord.AuditLogEntry
    ) -> str:
        """Attempt to immediately rollback the destructive action."""
        # For a truly massive system, this would push to a Redis queue.
        # Here we attempt immediate restoration.
        if action_type == "channel_delete":
            channel = await RollbackService.restore_channel(guild, audit_entry)
            return "SUCCESS" if channel else "FAILED"
        if action_type == "role_delete":
            role = await RollbackService.restore_role(guild, audit_entry)
            return "SUCCESS" if role else "FAILED"

        return "PENDING"

    def _broadcast_dashboard_event(self, guild_id: int, event_type: str, payload: dict) -> None:
        """Stub for Live Dashboard Events and WebSocket Sync."""
        # In the future, this will push to a Redis pub/sub channel for the FastAPI backend.
