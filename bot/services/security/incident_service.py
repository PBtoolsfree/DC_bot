"""Service for tracking incidents and timeline events."""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

import discord

from bot.database.repositories.security_repo import SecurityRepository
from bot.utils.embed_builder import EmbedBuilder

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from bot.database.models.security import IncidentReport


class IncidentService:
    """Manages recording incidents and sending alerts to the log channel."""

    @staticmethod
    async def log_incident(
        session: AsyncSession,
        guild: discord.Guild,
        action: str,
        target_id: int | None = None,
        executor_id: int | None = None,
        reason: str | None = None,
        rollback_status: str = "NONE",
        metadata: dict | None = None,
        log_channel_id: int | None = None,
    ) -> IncidentReport:
        """Create an incident report in the DB and alert the designated channel."""
        # 1. DB Entry
        incident = await SecurityRepository.create_incident(
            session=session,
            guild_id=guild.id,
            action=action,
            executor_id=executor_id,
            target_id=target_id,
            reason=reason,
            rollback_status=rollback_status,
            metadata_json=metadata,
        )

        # 2. Discord Log Channel
        if log_channel_id:
            channel = guild.get_channel(log_channel_id)
            if isinstance(channel, discord.TextChannel):
                embed = EmbedBuilder.security_alert(
                    title=f"Security Incident: {action.replace('_', ' ').title()}",
                    description=reason or "A security incident was detected.",
                )
                if executor_id:
                    embed.add_field(name="Executor ID", value=str(executor_id), inline=True)
                if target_id:
                    embed.add_field(name="Target ID", value=str(target_id), inline=True)

                embed.add_field(name="Rollback Status", value=rollback_status, inline=True)
                embed.set_footer(text=f"Incident ID: {incident.id}")

                with contextlib.suppress(discord.HTTPException):
                    await channel.send(embed=embed)

        return incident
