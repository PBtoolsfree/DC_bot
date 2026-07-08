"""Dashboard permission enumerations."""

from enum import Enum


class DashboardRole(str, Enum):
    """Pre-defined dashboard roles."""

    OWNER = "owner"
    ADMIN = "admin"
    MODERATOR = "moderator"
    VIEWER = "viewer"
    CUSTOM = "custom"


class GranularPermission(str, Enum):
    """Granular permissions for custom dashboard roles."""

    MANAGE_MODERATION = "manage_moderation"
    MANAGE_AUTOMOD = "manage_automod"
    MANAGE_SECURITY = "manage_security"
    MANAGE_LOGS = "manage_logs"
    MANAGE_TICKETS = "manage_tickets"
    MANAGE_VERIFICATION = "manage_verification"
    MANAGE_WELCOME = "manage_welcome"
    MANAGE_NOTIFICATIONS = "manage_notifications"
    MANAGE_PREMIUM = "manage_premium"
    VIEW_ANALYTICS = "view_analytics"
