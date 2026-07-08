"""Pillow-based Image Generator."""

import io
from PIL import Image, ImageDraw, ImageFont
import discord
import aiohttp

from bot.services.welcome.providers.base import ImageProvider


class PillowImageProvider(ImageProvider):
    """Generates Welcome and Rank cards using Python Pillow natively."""

    async def _fetch_image(self, url: str) -> Image.Image | None:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.read()
                        return Image.open(io.BytesIO(data)).convert("RGBA")
        except Exception:
            pass
        return None

    async def generate_welcome_card(self, member: discord.Member, background_url: str | None = None) -> bytes:
        """Generates a simple 800x250 Welcome card."""
        
        # Base canvas
        img = Image.new("RGBA", (800, 250), color=(35, 39, 42))
        
        # Load background if provided
        if background_url:
            bg = await self._fetch_image(background_url)
            if bg:
                bg = bg.resize((800, 250))
                img.paste(bg, (0, 0))
                
        draw = ImageDraw.Draw(img)
        
        # Add Avatar
        if member.display_avatar:
            avatar = await self._fetch_image(member.display_avatar.replace(size=128).url)
            if avatar:
                avatar = avatar.resize((150, 150))
                # Circular mask
                mask = Image.new('L', (150, 150), 0)
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.ellipse((0, 0, 150, 150), fill=255)
                img.paste(avatar, (50, 50), mask)
                
        # We don't have TrueType fonts loaded by default on this environment, so we use default
        font = ImageFont.load_default()
        
        # Welcome text
        draw.text((230, 80), "WELCOME", font=font, fill=(255, 255, 255))
        draw.text((230, 120), f"{member.name}", font=font, fill=(255, 255, 255))
        draw.text((230, 160), f"Member #{len(member.guild.members)}", font=font, fill=(185, 187, 190))
        
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()

    async def generate_rank_card(self, member: discord.Member, xp: int, level: int, rank: int) -> bytes:
        """Generates a 800x250 Rank card."""
        
        img = Image.new("RGBA", (800, 250), color=(35, 39, 42))
        draw = ImageDraw.Draw(img)
        
        if member.display_avatar:
            avatar = await self._fetch_image(member.display_avatar.replace(size=128).url)
            if avatar:
                avatar = avatar.resize((150, 150))
                mask = Image.new('L', (150, 150), 0)
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.ellipse((0, 0, 150, 150), fill=255)
                img.paste(avatar, (50, 50), mask)
                
        font = ImageFont.load_default()
        
        draw.text((230, 80), f"{member.name}", font=font, fill=(255, 255, 255))
        draw.text((650, 80), f"RANK #{rank}", font=font, fill=(255, 255, 255))
        draw.text((650, 110), f"LEVEL {level}", font=font, fill=(0, 176, 244))
        
        # Progress bar
        draw.rectangle([230, 160, 750, 180], fill=(79, 84, 92), outline=None)
        draw.rectangle([230, 160, 500, 180], fill=(0, 176, 244), outline=None) # mock 50%
        
        draw.text((650, 190), f"{xp} XP", font=font, fill=(185, 187, 190))
        
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()
