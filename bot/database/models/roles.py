"""Database models for Reaction Roles (Module 11)."""

from sqlalchemy import BigInteger, String, JSON, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from bot.database.models.base import Base


class ReactionRolePanel(Base):
    """A deployed message with buttons/dropdowns."""
    __tablename__ = "reaction_role_panels"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    channel_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    
    group_id: Mapped[int] = mapped_column(ForeignKey("reaction_role_groups.id", ondelete="CASCADE"), nullable=False)


class ReactionRoleGroup(Base):
    """Defines limits and exclusivity for a set of roles."""
    __tablename__ = "reaction_role_groups"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Validation logic
    min_roles: Mapped[int] = mapped_column(Integer, default=0)
    max_roles: Mapped[int] = mapped_column(Integer, default=0) # 0 means unlimited
    required_roles: Mapped[list[int]] = mapped_column(JSON, default=list) # User must have these to use
    blacklisted_roles: Mapped[list[int]] = mapped_column(JSON, default=list) # User must NOT have these


class ReactionRoleItem(Base):
    """Maps a specific emoji/custom_id to a Discord role."""
    __tablename__ = "reaction_role_items"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("reaction_role_groups.id", ondelete="CASCADE"), nullable=False)
    
    role_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    emoji: Mapped[str | None] = mapped_column(String(50), nullable=True)
    label: Mapped[str | None] = mapped_column(String(100), nullable=True)
