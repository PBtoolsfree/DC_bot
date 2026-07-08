"""Database models package.

Import all models here so that:
1. Alembic can auto-detect them for migrations
2. SQLAlchemy metadata.create_all() can find them
3. Other modules can import from a single location
"""

from __future__ import annotations

from bot.database.models.base import Base
from bot.database.models.guild import (
    GuildConfig,
    GuildModuleSettings,
    GuildPremium,
)
from bot.database.models.member import (
    MemberData,
    ModAction,
    Warning,
)
from bot.database.models.security import (
    IncidentReport,
    SecuritySnapshot,
)
from bot.database.models.logging import ActionLog
from bot.database.models.dashboard import DashboardMember
from bot.database.models.dashboard_audit import DashboardAuditLog
from bot.database.models.verification import (
    VerificationSettings,
    VerificationSession,
    VerificationHistory,
)
from bot.database.models.tickets import (
    Ticket,
    TicketCategory,
    TicketPanel,
    TicketMessage,
    TicketTranscript,
    TicketParticipant
)
from bot.database.models.backup import ServerBackup
from bot.database.models.welcome import WelcomeSettings, AutoRoleSettings
from bot.database.models.roles import ReactionRolePanel, ReactionRoleGroup, ReactionRoleItem
from bot.database.models.xp import XPSettings, UserXP, XPReward

__all__ = [
    "Base",
    "GuildConfig",
    "GuildModuleSettings",
    "GuildPremium",
    "MemberData",
    "ModAction",
    "Warning",
    "IncidentReport",
    "SecuritySnapshot",
    "ActionLog",
    "DashboardMember",
    "DashboardAuditLog",
    "VerificationSettings",
    "VerificationSession",
    "VerificationHistory",
    "Ticket",
    "TicketCategory",
    "TicketPanel",
    "TicketMessage",
    "TicketTranscript",
    "TicketParticipant",
    "ServerBackup",
    "WelcomeSettings",
    "AutoRoleSettings",
    "ReactionRolePanel",
    "ReactionRoleGroup",
    "ReactionRoleItem",
    "XPSettings",
    "UserXP",
    "XPReward",
]
