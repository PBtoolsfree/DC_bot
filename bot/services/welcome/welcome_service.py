"""Welcome Service."""

import discord
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models.welcome import WelcomeSettings
from bot.services.logging.streaming_service import StreamingService
from bot.services.welcome.providers.pillow_provider import PillowImageProvider


class WelcomeService:
    """Handles formatting and sending welcome/goodbye messages."""

    def __init__(self) -> None:
        self.image_provider = PillowImageProvider()

    def _format_message(self, template: str, member: discord.Member) -> str:
        """Replaces placeholders."""
        return template.format(
            user=member.mention,
            username=member.name,
            userid=member.id,
            guild=member.guild.name,
            membercount=len(member.guild.members),
        )

    async def handle_member_join(self, session: AsyncSession, member: discord.Member) -> None:
        """Processes the welcome config when a member joins."""

        stmt = select(WelcomeSettings).where(WelcomeSettings.guild_id == member.guild.id)
        result = await session.execute(stmt)
        settings = result.scalar_one_or_none()

        if not settings or not settings.welcome_enabled or not settings.welcome_channel_id:
            return

        channel = member.guild.get_channel(settings.welcome_channel_id)
        if not channel:
            return

        content = self._format_message(
            settings.welcome_message or "Welcome {user} to {guild}!", member
        )

        # Generate Image if URL provided
        file = None
        if settings.welcome_image_url:
            try:
                img_bytes = await self.image_provider.generate_welcome_card(
                    member, settings.welcome_image_url
                )
                import io

                file = discord.File(fp=io.BytesIO(img_bytes), filename="welcome.png")
            except Exception:
                pass  # Fallback to text only

        await channel.send(content=content, file=file)  # type: ignore

        await StreamingService.broadcast(
            guild_id=member.guild.id, event_type="WELCOME_SENT", payload={"user_id": str(member.id)}
        )
