import re

def fix(path, old, new):
    with open(path, "r", encoding="utf-8") as f:
        c = f.read()
    c = c.replace(old, new)
    with open(path, "w", encoding="utf-8") as f:
        f.write(c)

# archive_service.py
fix("bot/services/tickets/archive_service.py",
"""                try:
                    await channel.delete(reason="Ticket Archived")  # type: ignore
                except discord.HTTPException:
                    pass""",
"""                import contextlib
                with contextlib.suppress(discord.HTTPException):
                    await channel.delete(reason="Ticket Archived")  # type: ignore""")

# assignment_service.py
fix("bot/services/tickets/assignment_service.py",
"session: AsyncSession, guild: discord.Guild, ticket: Ticket, category: TicketCategory",
"session: AsyncSession, guild: discord.Guild, _ticket: Ticket, category: TicketCategory")

# html_provider.py
fix("bot/services/tickets/providers/html_provider.py",
"env = Environment(loader=BaseLoader())",
"env = Environment(loader=BaseLoader(), autoescape=True)")

# relay_service.py
fix("bot/services/tickets/relay_service.py",
"_redis_cache: dict[str, int] = {}",
"import typing\n    _redis_cache: typing.ClassVar[dict[str, int]] = {}")

# transcript_service.py
# Use aiofiles for file writes
trans_code = """        filename = f"ticket_{ticket.id}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}{provider.extension}"
        filepath = self.export_dir / filename

        with open(filepath, "wb") as f:
            f.write(data)"""
trans_new = """        import datetime as dt
        filename = f"ticket_{ticket.id}_{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%d%H%M%S')}{provider.extension}"
        filepath = self.export_dir / filename

        import aiofiles
        async with aiofiles.open(filepath, "wb") as f:
            await f.write(data)"""
fix("bot/services/tickets/transcript_service.py", trans_code, trans_new)

# approval_service.py
fix("bot/services/verification/approval_service.py", "token: str, moderator_id: int", "token: str, _moderator_id: int")

# image_provider.py
fix("bot/services/verification/providers/image_provider.py", "self, user_id: int", "self, _user_id: int")
fix("bot/services/verification/providers/image_provider.py",
    'expected = "".join(random.choices(chars, k=6))',
    'import secrets\n        expected = "".join(secrets.choice(chars) for _ in range(6))')

# math_provider.py
fix("bot/services/verification/providers/math_provider.py", "self, user_id: int", "self, _user_id: int")
math_code2 = """        op = random.choice(operations)

        if op == "*":
            a = random.randint(2, 9)
            b = random.randint(2, 9)"""
math_new2 = """        import secrets
        op = secrets.choice(operations)

        if op == "*":
            a = secrets.randbelow(8) + 2
            b = secrets.randbelow(8) + 2"""
fix("bot/services/verification/providers/math_provider.py", math_code2, math_new2)

# test_cogs_automod.py
test_am = 'await cog.toggle.callback.__wrapped__(\n            cog, mock_interaction, app_commands.Choice(name="Enable", value="enable")\n        )'
test_am_new = 'await cog.toggle.callback.__wrapped__(\n            cog, mock_interaction,\n            app_commands.Choice(name="Enable", value="enable")\n        )'
fix("tests/test_cogs_automod.py", test_am, test_am_new)

# message_provider.py
fix("bot/services/xp/providers/message_provider.py",
    "xp_amount = secrets.randbelow(settings.message_xp_max - settings.message_xp_min + 1) + settings.message_xp_min",
    "xp_amount = secrets.randbelow(\n            settings.message_xp_max - settings.message_xp_min + 1\n        ) + settings.message_xp_min")
