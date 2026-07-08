"""Ticket UI Components."""

import logging

import discord
from discord.ui import Button, Select, View

from bot.database.core import db
from bot.database.repositories.ticket_repo import TicketRepository
from bot.services.tickets.archive_service import ArchiveService
from bot.services.tickets.claim_service import ClaimService
from bot.services.tickets.ticket_service import TicketService

logger = logging.getLogger(__name__)


class TicketControlView(View):
    """Buttons inside a ticket channel (Close, Claim)."""

    def __init__(self, ticket_id: int):
        super().__init__(timeout=None)
        self.ticket_id = ticket_id

    @discord.ui.button(label="Claim", style=discord.ButtonStyle.primary, custom_id="ticket_claim")
    async def claim_btn(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer(ephemeral=True)
        async with db.session() as session:
            ticket = await TicketRepository.get_ticket_by_id(session, self.ticket_id)
            if not ticket:
                return

            success = await ClaimService.claim_ticket(session, ticket, interaction.user)  # type: ignore
            await session.commit()

            if success:
                await interaction.followup.send("You claimed this ticket.")
                button.disabled = True
                await interaction.message.edit(view=self)  # type: ignore
            else:
                await interaction.followup.send("Ticket already claimed or error.")

    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger, custom_id="ticket_close")
    async def close_btn(self, interaction: discord.Interaction, _button: Button):
        await interaction.response.defer()
        async with db.session() as session:
            ticket = await TicketRepository.get_ticket_by_id(session, self.ticket_id)
            if not ticket:
                return

            # Change status to closed, then archive immediately for this demo
            await ArchiveService.archive_ticket(
                session, interaction.guild, ticket, interaction.user.id
            )  # type: ignore
            await session.commit()


class TicketPanelView(View):
    """The public persistent panel to open tickets."""

    def __init__(self, panel_id: int, categories: list):
        super().__init__(timeout=None)
        self.panel_id = panel_id

        # Create a dropdown for categories
        options = [
            discord.SelectOption(label=cat.name, description=cat.description, value=str(cat.id))
            for cat in categories
        ]

        self.select = Select(
            placeholder="Select a category...", options=options, custom_id=f"panel_{panel_id}"
        )
        self.select.callback = self.select_callback
        self.add_item(self.select)

    async def select_callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        cat_id = int(self.select.values[0])

        async with db.session() as session:
            category = await TicketRepository.get_category(session, cat_id)
            if not category:
                await interaction.followup.send("Category not found.", ephemeral=True)
                return

            # Open ticket
            ticket = await TicketService.open_ticket(
                session, interaction.guild, interaction.user, category
            )  # type: ignore
            await session.commit()

            if ticket.channel_id:
                await interaction.followup.send(
                    f"Ticket opened: <#{ticket.channel_id}>", ephemeral=True
                )

                # Send control view to the new channel
                channel = interaction.guild.get_channel(ticket.channel_id)  # type: ignore
                if channel:
                    embed = discord.Embed(
                        title=f"Ticket: {category.name}",
                        description="Support will be with you shortly.",
                    )
                    await channel.send(embed=embed, view=TicketControlView(ticket.id))  # type: ignore
            else:
                await interaction.followup.send(
                    "Ticket opened anonymously. We will DM you.", ephemeral=True
                )
