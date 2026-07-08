import re

def fix_file(path, replacements):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    for old, new in replacements:
        content = content.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

# 1. bot/ui/verification_views.py
fix_file("bot/ui/verification_views.py", [
    ("button: Button", "_button: Button")
])

# 2. bot/utils/paginator.py
fix_file("bot/utils/paginator.py", [
    ("button: discord.ui.Button[PaginatorView]", "_button: discord.ui.Button[PaginatorView]")
])

# 3. bot/utils/constants.py
fix_file("bot/utils/constants.py", [
    ('INFO = "ℹ️"', 'INFO = "💡"'),
    ('NUMBERS = ["0️⃣"', 'NUMBERS: typing.ClassVar[list[str]] = ["0️⃣"'),
    ('ALL: list[str] = [', 'ALL: typing.ClassVar[list[str]] = [')
])
# Need to ensure typing is imported in constants.py
with open("bot/utils/constants.py", 'r', encoding='utf-8') as f:
    if "import typing" not in f.read():
        with open("bot/utils/constants.py", 'r', encoding='utf-8') as f2:
            content = f2.read()
        content = "import typing\n" + content
        with open("bot/utils/constants.py", 'w', encoding='utf-8') as f3:
            f3.write(content)

# 4. bot/utils/embed_builder.py
fix_file("bot/utils/embed_builder.py", [
    ('title: Embed title (auto-prefixed with ℹ️).', 'title: Embed title (auto-prefixed).')
])

# 5. dashboard/backend/api/v1/members.py
fix_file("dashboard/backend/api/v1/members.py", [
    ('raise HTTPException(status_code=400, detail="Invalid discord_user_id")', 'raise HTTPException(status_code=400, detail="Invalid discord_user_id") from None')
])

# 6. dashboard/backend/api/v1/verification.py
fix_file("dashboard/backend/api/v1/verification.py", [
    ('raise HTTPException(status_code=400, detail=f"Invalid ID for {key}")', 'raise HTTPException(status_code=400, detail=f"Invalid ID for {key}") from None')
])

# 7. dashboard/backend/core/security.py
fix_file("dashboard/backend/core/security.py", [
    ('raise credentials_exception', 'raise credentials_exception from None')
])

# 8. dashboard/backend/core/websocket.py
ws_code = """                try:
                    await connection.send_json(message)
                except Exception:
                    pass  # Handle stale connections"""
ws_new = """                import contextlib
                with contextlib.suppress(Exception):
                    await connection.send_json(message)"""
fix_file("dashboard/backend/core/websocket.py", [
    (ws_code, ws_new)
])

# 9. tests/test_cogs_automod.py (Line too long)
fix_file("tests/test_cogs_automod.py", [
    ('await cog.toggle.callback.__wrapped__(cog, mock_interaction, app_commands.Choice(name="Enable", value="enable"))  # type: ignore', 
     'await cog.toggle.callback.__wrapped__(cog, mock_interaction, app_commands.Choice(name="Enable", value="enable"))')
])

# 10. tests/test_embed_builder.py (Unused lambda argument self)
fix_file("tests/test_embed_builder.py", [
    ('lambda self: "TestUser"', 'lambda _self: "TestUser"')
])
