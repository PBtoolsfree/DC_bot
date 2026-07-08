"""Tests for the embed_builder utility module."""

from __future__ import annotations

from unittest.mock import MagicMock

import discord

from bot.utils.constants import Colors, Emojis
from bot.utils.embed_builder import EmbedBuilder


class TestEmbedBuilderSuccess:
    """Tests for EmbedBuilder.success()."""

    def test_success_embed_has_green_color(self) -> None:
        """Success embeds should use the SUCCESS color."""
        embed = EmbedBuilder.success(title="Done", description="Action completed.")
        assert embed.color == Colors.SUCCESS

    def test_success_embed_has_check_emoji(self) -> None:
        """Success embed title should be prefixed with ✅."""
        embed = EmbedBuilder.success(title="Done")
        assert embed.title is not None
        assert embed.title.startswith(Emojis.SUCCESS)

    def test_success_embed_has_footer(self) -> None:
        """Success embed should have the standard footer."""
        embed = EmbedBuilder.success(title="Done")
        assert embed.footer is not None
        assert embed.footer.text is not None

    def test_success_embed_has_timestamp(self) -> None:
        """Success embed should include a timestamp."""
        embed = EmbedBuilder.success(title="Done")
        assert embed.timestamp is not None


class TestEmbedBuilderError:
    """Tests for EmbedBuilder.error()."""

    def test_error_embed_has_red_color(self) -> None:
        """Error embeds should use the ERROR color."""
        embed = EmbedBuilder.error(title="Failed", description="Something broke.")
        assert embed.color == Colors.ERROR

    def test_error_embed_has_x_emoji(self) -> None:
        """Error embed title should be prefixed with ❌."""
        embed = EmbedBuilder.error(title="Failed")
        assert embed.title is not None
        assert embed.title.startswith(Emojis.ERROR)


class TestEmbedBuilderWarning:
    """Tests for EmbedBuilder.warning()."""

    def test_warning_embed_has_yellow_color(self) -> None:
        """Warning embeds should use the WARNING color."""
        embed = EmbedBuilder.warning(title="Caution")
        assert embed.color == Colors.WARNING


class TestEmbedBuilderInfo:
    """Tests for EmbedBuilder.info()."""

    def test_info_embed_has_blurple_color(self) -> None:
        """Info embeds should use the INFO color."""
        embed = EmbedBuilder.info(title="Info")
        assert embed.color == Colors.INFO


class TestEmbedBuilderModeration:
    """Tests for EmbedBuilder.moderation()."""

    def test_moderation_embed_has_correct_fields(self) -> None:
        """Moderation embed should have Target, Moderator, and Reason fields."""
        embed = EmbedBuilder.moderation(
            action="Ban",
            target="TestUser#1234",
            moderator="Admin#5678",
            reason="Spamming",
        )
        field_names = [f.name for f in embed.fields]
        assert "Target" in field_names
        assert "Moderator" in field_names
        assert "Reason" in field_names

    def test_moderation_embed_with_duration(self) -> None:
        """Moderation embed should include Duration field when provided."""
        embed = EmbedBuilder.moderation(
            action="Timeout",
            target="TestUser#1234",
            moderator="Admin#5678",
            reason="Spamming",
            duration="2 hours",
        )
        field_names = [f.name for f in embed.fields]
        assert "Duration" in field_names

    def test_moderation_embed_with_case_id(self) -> None:
        """Moderation embed title should include case ID when provided."""
        embed = EmbedBuilder.moderation(
            action="Warn",
            target="TestUser#1234",
            moderator="Admin#5678",
            case_id=42,
        )
        assert embed.title is not None
        assert "Case #42" in embed.title

    def test_moderation_embed_with_member_thumbnail(self) -> None:
        """Moderation embed should set thumbnail to target's avatar."""
        target = MagicMock(spec=discord.Member)
        target.__str__ = lambda _self: "TestUser"
        target.display_avatar = MagicMock()
        target.display_avatar.url = "https://cdn.discordapp.com/embed/avatars/0.png"

        embed = EmbedBuilder.moderation(
            action="Ban",
            target=target,
            moderator="Admin",
        )
        assert embed.thumbnail is not None
        assert embed.thumbnail.url == "https://cdn.discordapp.com/embed/avatars/0.png"


class TestEmbedBuilderNullTitle:
    """Tests for embeds with None title."""

    def test_success_with_no_title(self) -> None:
        """Should handle None title gracefully."""
        embed = EmbedBuilder.success(description="Just a description.")
        assert embed.title is None

    def test_error_with_no_title(self) -> None:
        """Should handle None title gracefully."""
        embed = EmbedBuilder.error(description="Just a description.")
        assert embed.title is None
