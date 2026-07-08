"""Service for core logging operations."""

from __future__ import annotations

import re
import uuid
from typing import Any

import discord
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models.logging import ActionLog
from bot.database.repositories.log_repo import LogRepository
from bot.database.schemas.logging import LoggingSettings
from bot.services.logging.streaming_service import StreamingService
from bot.utils.embed_builder import EmbedBuilder
from bot.utils.logger import get_logger

logger = get_logger(__name__)


class LoggingService:
    """Master orchestrator for all logging events."""
    
    IP_REGEX = re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")
    EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b")

    def __init__(self, bot: Any) -> None:
        self.bot = bot
        self.streaming_service = StreamingService()

    @classmethod
    def mask_sensitive_data(cls, text: str, settings: LoggingSettings) -> str:
        """Mask sensitive information in logs if configured."""
        if not text:
            return text
            
        if settings.mask_ips:
            text = cls.IP_REGEX.sub("[REDACTED IP]", text)
        if settings.mask_emails:
            text = cls.EMAIL_REGEX.sub("[REDACTED EMAIL]", text)
            
        return text

    async def emit_log(
        self,
        session: AsyncSession,
        guild: discord.Guild,
        settings: LoggingSettings,
        action_type: str,
        severity: int = 1,
        executor: discord.Member | discord.User | None = None,
        target_id: int | None = None,
        channel: discord.abc.GuildChannel | None = None,
        before: dict[str, Any] | None = None,
        after: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        is_immutable: bool = False,
        embed: discord.Embed | None = None,
    ) -> ActionLog | None:
        """Process, store, and dispatch a log event."""
        if not settings.enabled:
            return None
            
        # Determine if any configured channel is listening for this event
        target_channels = []
        for channel_name, config in settings.channels.items():
            if config.enabled and action_type in config.events and config.channel_id:
                target_channels.append(config.channel_id)
                
        if not target_channels and not is_immutable:
            # If no channel is listening and it's not a forced immutable log, we might skip
            # to save DB space, but enterprise systems log everything.
            # However, for performance we'll only log if it's routed or if severity is high.
            if severity < 3:
                return None

        # Mask sensitive data in before/after if they are string-based
        # (This is a simplified masking pass. In production, we'd recursively search the dict)
        if before and "content" in before and isinstance(before["content"], str):
            before["content"] = self.mask_sensitive_data(before["content"], settings)
        if after and "content" in after and isinstance(after["content"], str):
            after["content"] = self.mask_sensitive_data(after["content"], settings)

        correlation_id = str(uuid.uuid4())

        # 1. Database Insertion
        try:
            log_entry = await LogRepository.create_log(
                session=session,
                guild_id=guild.id,
                action_type=action_type,
                severity=severity,
                executor_id=executor.id if executor else None,
                target_id=target_id,
                channel_id=channel.id if channel else None,
                before_data=before,
                after_data=after,
                metadata_json=metadata,
                correlation_id=correlation_id,
                is_immutable=is_immutable,
            )
        except Exception as e:
            logger.error("logging.db_insert_failed", error=str(e), guild_id=guild.id)
            return None

        # 2. Discord Dispatch
        if target_channels and embed:
            embed.set_footer(text=f"Correlation ID: {correlation_id}")
            
            for dest_channel_id in target_channels:
                dest_channel = guild.get_channel(dest_channel_id)
                if isinstance(dest_channel, discord.TextChannel):
                    try:
                        await dest_channel.send(embed=embed)
                    except discord.HTTPException:
                        pass # Permissions issue or channel deleted
                        
        # 3. Live Dashboard WebSocket Stream
        self.streaming_service.broadcast_event(
            guild_id=guild.id,
            action_type=action_type,
            severity=severity,
            payload={
                "executor": executor.id if executor else None,
                "target": target_id,
                "correlation_id": correlation_id
            }
        )
        
        return log_entry
