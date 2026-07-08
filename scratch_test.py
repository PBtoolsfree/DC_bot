import discord
from unittest.mock import MagicMock

print(isinstance(MagicMock(spec=discord.Member), discord.Member))
