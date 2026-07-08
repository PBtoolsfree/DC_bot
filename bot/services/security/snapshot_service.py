"""Service for creating and managing server snapshots."""

from __future__ import annotations

import discord
from typing import Any

from bot.database.repositories.security_repo import SecurityRepository
from sqlalchemy.ext.asyncio import AsyncSession


class SnapshotService:
    """Manages the creation and retrieval of server snapshots for disaster recovery."""

    @staticmethod
    def create_server_snapshot(guild: discord.Guild) -> dict[str, Any]:
        """Serialize the entire server layout into a dictionary."""
        snapshot = {
            "name": guild.name,
            "icon_url": guild.icon.url if guild.icon else None,
            "verification_level": guild.verification_level.value,
            "explicit_content_filter": guild.explicit_content_filter.value,
            "default_notifications": guild.default_notifications.value,
            "roles": [],
            "categories": [],
            "channels": [],
        }

        # Backup Roles
        for role in sorted(guild.roles, key=lambda r: r.position, reverse=True):
            if role.is_default():
                continue
            snapshot["roles"].append({
                "id": role.id,
                "name": role.name,
                "color": role.color.value,
                "hoist": role.hoist,
                "mentionable": role.mentionable,
                "permissions": role.permissions.value,
                "position": role.position,
            })

        # Backup Categories
        for category in guild.categories:
            snapshot["categories"].append({
                "id": category.id,
                "name": category.name,
                "position": category.position,
                "overwrites": [
                    {
                        "target_id": target.id,
                        "type": "role" if isinstance(target, discord.Role) else "member",
                        "allow": overwrite.pair()[0].value,
                        "deny": overwrite.pair()[1].value,
                    }
                    for target, overwrite in category.overwrites.items()
                ]
            })

        # Backup Channels (Text, Voice, Forum, Stage)
        for channel in guild.channels:
            if isinstance(channel, discord.CategoryChannel):
                continue
                
            channel_data = {
                "id": channel.id,
                "name": channel.name,
                "type": str(channel.type),
                "position": channel.position,
                "category_id": channel.category_id,
                "overwrites": [
                    {
                        "target_id": target.id,
                        "type": "role" if isinstance(target, discord.Role) else "member",
                        "allow": overwrite.pair()[0].value,
                        "deny": overwrite.pair()[1].value,
                    }
                    for target, overwrite in channel.overwrites.items()
                ]
            }
            
            if isinstance(channel, discord.TextChannel):
                channel_data["topic"] = channel.topic
                channel_data["nsfw"] = channel.is_nsfw()
                channel_data["slowmode_delay"] = channel.slowmode_delay
            elif isinstance(channel, discord.VoiceChannel):
                channel_data["bitrate"] = channel.bitrate
                channel_data["user_limit"] = channel.user_limit
                
            snapshot["channels"].append(channel_data)

        return snapshot

    @staticmethod
    async def save_snapshot(
        session: AsyncSession,
        guild: discord.Guild,
        created_by: discord.Member | discord.User,
        name: str | None = None,
        is_auto: bool = False,
    ) -> None:
        """Create and save a snapshot to the database."""
        snapshot_data = SnapshotService.create_server_snapshot(guild)
        name = name or f"Snapshot {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M')}"
        
        await SecurityRepository.create_snapshot(
            session=session,
            guild_id=guild.id,
            name=name,
            created_by_id=created_by.id,
            snapshot_data=snapshot_data,
            is_auto=is_auto
        )
