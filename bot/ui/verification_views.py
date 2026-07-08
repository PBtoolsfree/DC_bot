"""Verification Discord UI Components."""

import discord
from discord.ui import Button, Modal, TextInput, View

from bot.database.core import db
from bot.services.verification.verification_service import VerificationService
from bot.utils.localization import locales


class VerificationModal(Modal):
    """Modal for users to submit their Captcha answer."""

    def __init__(self, token: str, language: str):
        title = locales.get_string(
            language, "verification", "CAPTCHA_TITLE", fallback="Solve Captcha"
        )
        super().__init__(title=title)
        self.token = token
        self.language = language

        self.answer = TextInput(
            label=locales.get_string(language, "verification", "MODAL_LABEL", fallback="Answer"),
            style=discord.TextStyle.short,
            required=True,
            max_length=50,
        )
        self.add_item(self.answer)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """Process the submitted answer."""
        await interaction.response.defer(ephemeral=True)

        service = VerificationService()
        async with db.session() as session:
            # We would normally fetch the guild settings here to get max_attempts and other config
            from bot.database.repositories.verification_repo import VerificationRepository

            settings = await VerificationRepository.get_settings(session, interaction.guild_id)
            if not settings:
                return

            success = await service.process_answer(
                session=session,
                member=interaction.user,
                token=self.token,
                user_provided=self.answer.value,
                settings=settings,
            )

            if success:
                msg = locales.get_string(self.language, "verification", "VERIFICATION_SUCCESS")
                await interaction.followup.send(msg, ephemeral=True)
            else:
                msg = locales.get_string(
                    self.language,
                    "verification",
                    "VERIFICATION_FAILED",
                    attempts=settings.max_attempts,
                )
                await interaction.followup.send(msg, ephemeral=True)


class VerificationView(View):
    """The static View attached to the verification channel."""

    def __init__(self, language: str):
        super().__init__(timeout=None)
        self.language = language

        btn = Button(
            label=locales.get_string(
                language, "verification", "VERIFY_BUTTON_LABEL", fallback="Verify"
            ),
            style=discord.ButtonStyle.green,
            custom_id="verification_start_btn",
        )
        btn.callback = self.start_verification
        self.add_item(btn)

    async def start_verification(self, interaction: discord.Interaction) -> None:
        """Initiate the verification flow for the user."""
        await interaction.response.defer(ephemeral=True)

        service = VerificationService()
        async with db.session() as session:
            from bot.database.repositories.verification_repo import VerificationRepository

            settings = await VerificationRepository.get_settings(session, interaction.guild_id)

            if not settings or not settings.enabled:
                await interaction.followup.send(
                    "Verification is currently disabled.", ephemeral=True
                )
                return

            v_session = await service.initiate_verification(session, interaction.user, settings)

            if not v_session:
                await interaction.followup.send(
                    "An error occurred. Please contact an admin.", ephemeral=True
                )
                return

            if v_session.state == "manual_review":
                msg = locales.get_string(settings.language, "verification", "VERIFICATION_MANUAL")
                await interaction.followup.send(msg, ephemeral=True)
                return

            if v_session.verification_type == "button":
                # User passed via button immediately if score was low and type was button/adaptive
                success = await service.process_answer(
                    session, interaction.user, v_session.session_id, "", settings
                )
                msg = locales.get_string(
                    settings.language,
                    "verification",
                    "VERIFICATION_SUCCESS" if success else "VERIFICATION_FAILED",
                )
                await interaction.followup.send(msg, ephemeral=True)
                return

            # Need to present captcha
            # We would normally generate the image buffer here from the provider if it's an image.
            # But the challenge was already generated during initiate_verification.
            # To fetch the image again we'd need to cache the BytesIO or regenerate.
            # For this enterprise design, the provider returns the image in initiate_verification,
            # so the orchestrator needs to pass it back. Let's assume we show the modal directly for Math/Word.

            # Since discord.ui.Modal can't easily hold an image attached in the prompt,
            # We first send the image to the user as an ephemeral message, THEN they click "Answer"

            msg = locales.get_string(settings.language, "verification", "CAPTCHA_DESC")

            # Create a button to open the modal
            class AnswerView(View):
                @discord.ui.button(label="Answer", style=discord.ButtonStyle.primary)
                async def ans(self, interaction: discord.Interaction, button: Button):
                    await interaction.response.send_modal(
                        VerificationModal(v_session.session_id, settings.language)
                    )

            await interaction.followup.send(msg, view=AnswerView(), ephemeral=True)
