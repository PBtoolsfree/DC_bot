"""Paginator — button-based paginated embed navigation.

Provides a reusable View for navigating through multi-page embeds
with First/Previous/Next/Last/Stop buttons.

Usage:
    from bot.utils.paginator import Paginator

    pages = [embed1, embed2, embed3]
    paginator = Paginator(pages=pages, author_id=interaction.user.id)
    await paginator.start(interaction)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord

from bot.utils.constants import Emojis

if TYPE_CHECKING:
    pass


class PaginatorView(discord.ui.View):
    """Interactive button-based paginator for embed lists.

    Features:
    - First / Previous / Page Counter / Next / Last buttons
    - Stop button to dismiss
    - Author-only interaction (only the command invoker can navigate)
    - Automatic timeout after 3 minutes of inactivity
    - Disables buttons when at first/last page

    Attributes:
        pages: List of embeds to paginate through.
        current_page: Zero-indexed current page number.
        author_id: Discord user ID who can interact with the paginator.
    """

    def __init__(
        self,
        pages: list[discord.Embed],
        author_id: int,
        timeout: float = 180.0,
    ) -> None:
        """Initialize the paginator.

        Args:
            pages: List of embeds to display.
            author_id: Only this user can interact with the buttons.
            timeout: Seconds before the view auto-disables (default: 3 min).
        """
        super().__init__(timeout=timeout)
        self.pages = pages
        self.current_page = 0
        self.author_id = author_id
        self.message: discord.Message | None = None
        self._update_buttons()

    @property
    def total_pages(self) -> int:
        """Total number of pages."""
        return len(self.pages)

    def _update_buttons(self) -> None:
        """Enable/disable buttons based on current page position."""
        self.first_page_button.disabled = self.current_page == 0
        self.prev_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page >= self.total_pages - 1
        self.last_page_button.disabled = self.current_page >= self.total_pages - 1

        self.page_counter.label = f"{self.current_page + 1}/{self.total_pages}"

    def _get_current_embed(self) -> discord.Embed:
        """Get the embed for the current page with footer updated."""
        embed = self.pages[self.current_page]
        return embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Ensure only the original author can interact."""
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                f"{Emojis.ERROR} Only the command author can use these buttons.",
                ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self) -> None:
        """Disable all buttons when the view times out."""
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True

        if self.message is not None:
            try:
                await self.message.edit(view=self)
            except discord.NotFound:
                pass

    async def start(self, interaction: discord.Interaction) -> None:
        """Send the first page and attach the view.

        Args:
            interaction: The slash command interaction to respond to.
        """
        if not self.pages:
            await interaction.response.send_message(
                f"{Emojis.ERROR} No pages to display.",
                ephemeral=True,
            )
            return

        # Single page — no buttons needed
        if self.total_pages == 1:
            await interaction.response.send_message(embed=self.pages[0])
            return

        self._update_buttons()
        await interaction.response.send_message(
            embed=self._get_current_embed(),
            view=self,
        )
        self.message = await interaction.original_response()

    # ------------------------------------------------------------------
    # Buttons
    # ------------------------------------------------------------------

    @discord.ui.button(
        label="≪",
        style=discord.ButtonStyle.secondary,
        custom_id="paginator:first",
    )
    async def first_page_button(
        self, interaction: discord.Interaction, button: discord.ui.Button[PaginatorView]
    ) -> None:
        """Jump to the first page."""
        self.current_page = 0
        self._update_buttons()
        await interaction.response.edit_message(
            embed=self._get_current_embed(),
            view=self,
        )

    @discord.ui.button(
        label="◀",
        style=discord.ButtonStyle.primary,
        custom_id="paginator:prev",
    )
    async def prev_button(
        self, interaction: discord.Interaction, button: discord.ui.Button[PaginatorView]
    ) -> None:
        """Go to the previous page."""
        self.current_page = max(0, self.current_page - 1)
        self._update_buttons()
        await interaction.response.edit_message(
            embed=self._get_current_embed(),
            view=self,
        )

    @discord.ui.button(
        label="1/1",
        style=discord.ButtonStyle.secondary,
        disabled=True,
        custom_id="paginator:counter",
    )
    async def page_counter(
        self, interaction: discord.Interaction, button: discord.ui.Button[PaginatorView]
    ) -> None:
        """Page counter (non-interactive)."""
        await interaction.response.defer()

    @discord.ui.button(
        label="▶",
        style=discord.ButtonStyle.primary,
        custom_id="paginator:next",
    )
    async def next_button(
        self, interaction: discord.Interaction, button: discord.ui.Button[PaginatorView]
    ) -> None:
        """Go to the next page."""
        self.current_page = min(self.total_pages - 1, self.current_page + 1)
        self._update_buttons()
        await interaction.response.edit_message(
            embed=self._get_current_embed(),
            view=self,
        )

    @discord.ui.button(
        label="≫",
        style=discord.ButtonStyle.secondary,
        custom_id="paginator:last",
    )
    async def last_page_button(
        self, interaction: discord.Interaction, button: discord.ui.Button[PaginatorView]
    ) -> None:
        """Jump to the last page."""
        self.current_page = self.total_pages - 1
        self._update_buttons()
        await interaction.response.edit_message(
            embed=self._get_current_embed(),
            view=self,
        )

    @discord.ui.button(
        label="✕",
        style=discord.ButtonStyle.danger,
        custom_id="paginator:stop",
    )
    async def stop_button(
        self, interaction: discord.Interaction, button: discord.ui.Button[PaginatorView]
    ) -> None:
        """Stop the paginator and remove buttons."""
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True

        await interaction.response.edit_message(view=self)
        self.stop()


class Paginator:
    """High-level paginator that creates embeds from a list of items.

    Handles splitting items into pages and creating embed pages automatically.

    Usage:
        paginator = Paginator.from_items(
            items=warning_list,
            formatter=lambda w: f"**#{w.id}** — {w.reason}",
            title="Warnings",
            per_page=10,
            author_id=interaction.user.id,
        )
        await paginator.start(interaction)
    """

    def __init__(
        self,
        pages: list[discord.Embed],
        author_id: int,
        timeout: float = 180.0,
    ) -> None:
        """Initialize with pre-built embed pages.

        Args:
            pages: List of embed pages.
            author_id: Only this user can navigate.
            timeout: View timeout in seconds.
        """
        self.view = PaginatorView(
            pages=pages,
            author_id=author_id,
            timeout=timeout,
        )

    async def start(self, interaction: discord.Interaction) -> None:
        """Start the paginator by responding to the interaction."""
        await self.view.start(interaction)

    @classmethod
    def from_items(
        cls,
        items: list[str],
        author_id: int,
        title: str = "Results",
        color: discord.Color = discord.Color.blurple(),
        per_page: int = 10,
        timeout: float = 180.0,
    ) -> Paginator:
        """Create a paginator from a list of formatted strings.

        Args:
            items: List of pre-formatted strings (one per line).
            author_id: Only this user can navigate.
            title: Embed title for each page.
            color: Embed color.
            per_page: Items per page.
            timeout: View timeout in seconds.

        Returns:
            A Paginator instance ready to start.
        """
        if not items:
            # Single empty page
            embed = discord.Embed(
                title=title,
                description="No items to display.",
                color=color,
            )
            return cls(pages=[embed], author_id=author_id, timeout=timeout)

        # Split into chunks
        chunks = [items[i : i + per_page] for i in range(0, len(items), per_page)]
        pages: list[discord.Embed] = []

        for i, chunk in enumerate(chunks):
            description = "\n".join(chunk)
            embed = discord.Embed(
                title=title,
                description=description,
                color=color,
            )
            embed.set_footer(text=f"Page {i + 1}/{len(chunks)}")
            pages.append(embed)

        return cls(pages=pages, author_id=author_id, timeout=timeout)
