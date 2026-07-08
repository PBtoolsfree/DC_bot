"""Database models package.

Import all models here so that:
1. Alembic can auto-detect them for migrations
2. SQLAlchemy metadata.create_all() can find them
3. Other modules can import from a single location
"""

from __future__ import annotations

from bot.database.models.backup import ServerBackup
from bot.database.models.base import Base
from bot.database.models.dashboard import DashboardMember
from bot.database.models.dashboard_audit import DashboardAuditLog
from bot.database.models.guild import (
    GuildConfig,
    GuildModuleSettings,
    GuildPremium,
)
from bot.database.models.logging import ActionLog
from bot.database.models.member import (
    MemberData,
    ModAction,
    Warning,
)
from bot.database.models.roles import ReactionRoleGroup, ReactionRoleItem, ReactionRolePanel
from bot.database.models.security import (
    IncidentReport,
    SecuritySnapshot,
)
from bot.database.models.tickets import (
    Ticket,
    TicketCategory,
    TicketMessage,
    TicketPanel,
    TicketParticipant,
    TicketTranscript,
)
from bot.database.models.verification import (
    VerificationHistory,
    VerificationSession,
    VerificationSettings,
)
from bot.database.models.welcome import AutoRoleSettings, WelcomeSettings
from bot.database.models.xp import UserXP, XPReward, XPSettings

__all__ = [
    "ActionLog",
    "AutoRoleSettings",
    "Base",
    "DashboardAuditLog",
    "DashboardMember",
    "GuildConfig",
    "GuildModuleSettings",
    "GuildPremium",
    "IncidentReport",
    "MemberData",
    "ModAction",
    "ReactionRoleGroup",
    "ReactionRoleItem",
    "ReactionRolePanel",
    "SecuritySnapshot",
    "ServerBackup",
    "Ticket",
    "TicketCategory",
    "TicketMessage",
    "TicketPanel",
    "TicketParticipant",
    "TicketTranscript",
    "UserXP",
    "VerificationHistory",
    "VerificationSession",
    "VerificationSettings",
    "Warning",
    "WelcomeSettings",
    "XPReward",
    "XPSettings",
]
