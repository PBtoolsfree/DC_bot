"""Reaction Role Views."""

import discord
from discord.ui import Button, View

from bot.database.core import db
from bot.services.roles.reaction_role_service import ReactionRoleService


class ReactionRoleView(View):
    """Dynamically generated buttons for a Reaction Role Panel."""

    def __init__(self, group_id: int, items: list):
        super().__init__(timeout=None)
        self.group_id = group_id

        for item in items:
            btn = Button(
                style=discord.ButtonStyle.secondary,
                label=item.label,
                emoji=item.emoji,
                custom_id=f"rr_{group_id}_{item.role_id}",
            )
            btn.callback = self.make_callback(item.role_id)
            self.add_item(btn)

    def make_callback(self, role_id: int):
        async def button_callback(interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            async with db.session() as session:
                _success, msg = await ReactionRoleService.toggle_role(
                    session, interaction.user, self.group_id, role_id  # type: ignore
                )
                await session.commit()

            await interaction.followup.send(msg, ephemeral=True)

        return button_callback
