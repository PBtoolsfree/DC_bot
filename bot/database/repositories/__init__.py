"""Repository package — data access layer.

Repositories encapsulate all database queries, keeping SQL logic
separate from business logic (services) and Discord logic (cogs).
"""

from __future__ import annotations

from bot.database.repositories.guild_repo import GuildRepository
from bot.database.repositories.member_repo import MemberRepository

__all__ = ["GuildRepository", "MemberRepository"]
