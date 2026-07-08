"""Ticket Cog."""

import discord
from discord.ext import commands
from sqlalchemy import select

from bot.database.core import db
from bot.database.repositories.ticket_repo import TicketRepository
from bot.services.tickets.relay_service import RelayService
from bot.services.tickets.ticket_service import TicketService
from bot.ui.ticket_views import TicketPanelView


class TicketCog(commands.Cog):
    """Cog for Ticket System and Relay Mode."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @discord.app_commands.command(name="ticket_panel", description="Deploy a ticket panel")
    @discord.app_commands.default_permissions(administrator=True)
    async def ticket_panel(self, interaction: discord.Interaction, panel_id: int) -> None:
        """Deploy the ticket panel view."""
        await interaction.response.defer(ephemeral=True)

        async with db.session() as session:
            panel = await TicketRepository.get_panel(session, panel_id)
            if not panel:
                await interaction.followup.send("Panel not found.")
                return

            # Load categories
            from bot.database.models.tickets import TicketCategory

            stmt = select(TicketCategory).where(TicketCategory.id.in_(panel.categories))
            result = await session.execute(stmt)
            categories = list(result.scalars().all())

        embed = discord.Embed(
            title=panel.title, description=panel.description, color=discord.Color.green()
        )
        view = TicketPanelView(panel_id, categories)

        await interaction.channel.send(embed=embed, view=view)  # type: ignore
        await interaction.followup.send("Panel deployed.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Listen for messages in Ticket channels and DMs for Relay Mode and Hybrid Storage."""
        if message.author.bot:
            return

        # 1. Relay Mode (DM -> Channel)
        if isinstance(message.channel, discord.DMChannel):
            target_channel_id = await RelayService.get_target_channel(message.author.id)
            if target_channel_id:
                channel = self.bot.get_channel(target_channel_id)
                if channel:
                    await channel.send(f"**[Anonymous User]**: {message.content}")  # type: ignore

                    # Store message logic
                    async with db.session() as session:
                        ticket = await TicketRepository.get_ticket_by_channel(
                            session, target_channel_id
                        )
                        if ticket:
                            await TicketService.log_message(session, ticket.id, message)
                            await session.commit()
            return

        # 2. Hybrid Storage or Relay Mode (Channel -> DM)
        async with db.session() as session:
            ticket = await TicketRepository.get_ticket_by_channel(session, message.channel.id)
            if ticket:
                await TicketService.log_message(session, ticket.id, message)

                # If relay mode, relay staff message back to user DM
                if ticket.is_anonymous:
                    target_user_id = await RelayService.get_target_user(message.channel.id)
                    if target_user_id:
                        user = self.bot.get_user(target_user_id)
                        if user:
                            try:
                                await user.send(
                                    f"**[Staff {message.author.name}]**: {message.content}"
                                )
                            except discord.HTTPException:
                                pass

                await session.commit()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TicketCog(bot))
