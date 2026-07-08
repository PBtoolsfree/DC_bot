"""Listeners for member-related events."""

from __future__ import annotations

import discord
from discord.ext import commands

from bot.core.bot import ManagementBot
from bot.database.repositories.guild_repo import GuildRepository
from bot.database.schemas.logging import LoggingSettings
from bot.services.logging.audit_service import AuditLogService
from bot.services.logging.logging_service import LoggingService
from bot.utils.embed_builder import EmbedBuilder


class MemberLogsCog(commands.Cog):
    """Handles logging for member joins, leaves, and updates."""

    def __init__(self, bot: ManagementBot) -> None:
        self.bot = bot
        self.logging_service = LoggingService(bot)
        self.audit_service = AuditLogService()

    async def _get_settings(self, guild_id: int) -> LoggingSettings | None:
        async with self.bot.db.session() as session:
            db_settings = await GuildRepository.get_module_settings(session, guild_id, "logging")
            if not db_settings or not db_settings.enabled:
                return None
            return LoggingSettings.from_dict(db_settings.config)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        settings = await self._get_settings(member.guild.id)
        if not settings:
            return

        embed = EmbedBuilder.log(
            action="Member Joined",
            target=member,
            color=discord.Color.green()
        )
        
        account_age = discord.utils.utcnow() - member.created_at
        embed.add_field(name="Account Created", value=f"<t:{int(member.created_at.timestamp())}:R>", inline=True)
        embed.add_field(name="Account Age", value=f"{account_age.days} days", inline=True)

        async with self.bot.db.session() as session:
            await self.logging_service.emit_log(
                session=session,
                guild=member.guild,
                settings=settings,
                action_type="member_join",
                severity=1,
                executor=member,
                target_id=member.id,
                after={"account_age_days": account_age.days, "bot": member.bot},
                embed=embed
            )

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        settings = await self._get_settings(member.guild.id)
        if not settings:
            return

        # Could be a kick/ban, audit service would be used in a real implementation
        executor = member
        audit_user = await self.audit_service.get_executor_for_action(
            member.guild, discord.AuditLogAction.kick, member.id, 5
        )
        if audit_user:
            executor = audit_user

        embed = EmbedBuilder.log(
            action="Member Left / Kicked",
            target=member,
            executor=executor if executor.id != member.id else None,
            color=discord.Color.dark_red()
        )
        
        roles = [r.mention for r in member.roles if not r.is_default()]
        if roles:
            embed.add_field(name="Roles", value=" ".join(roles)[:1024], inline=False)

        async with self.bot.db.session() as session:
            await self.logging_service.emit_log(
                session=session,
                guild=member.guild,
                settings=settings,
                action_type="member_leave",
                severity=2 if audit_user else 1,
                executor=executor,
                target_id=member.id,
                before={"roles": [r.id for r in member.roles]},
                embed=embed
            )

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        settings = await self._get_settings(before.guild.id)
        if not settings:
            return

        if before.nick != after.nick:
            embed = EmbedBuilder.log(
                action="Nickname Changed",
                target=after,
                executor=after,
                color=discord.Color.blue()
            )
            embed.add_field(name="Before", value=before.nick or "[No Nickname]", inline=True)
            embed.add_field(name="After", value=after.nick or "[No Nickname]", inline=True)
            
            async with self.bot.db.session() as session:
                await self.logging_service.emit_log(
                    session=session, guild=after.guild, settings=settings,
                    action_type="nick_change", severity=1, executor=after, target_id=after.id,
                    before={"nick": before.nick}, after={"nick": after.nick}, embed=embed
                )
                
        elif before.roles != after.roles:
            added = [r for r in after.roles if r not in before.roles]
            removed = [r for r in before.roles if r not in after.roles]
            
            executor = after
            audit_user = await self.audit_service.get_executor_for_action(
                after.guild, discord.AuditLogAction.member_role_update, after.id, 5
            )
            if audit_user:
                executor = audit_user
                
            embed = EmbedBuilder.log(
                action="Roles Updated",
                target=after,
                executor=executor,
                color=discord.Color.blue()
            )
            if added:
                embed.add_field(name="Added", value=" ".join([r.mention for r in added]), inline=False)
            if removed:
                embed.add_field(name="Removed", value=" ".join([r.mention for r in removed]), inline=False)
                
            async with self.bot.db.session() as session:
                await self.logging_service.emit_log(
                    session=session, guild=after.guild, settings=settings,
                    action_type="role_update", severity=2, executor=executor, target_id=after.id,
                    before={"roles": [r.id for r in before.roles]}, after={"roles": [r.id for r in after.roles]}, embed=embed
                )
