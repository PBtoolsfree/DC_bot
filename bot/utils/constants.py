"""Application-wide constants.

Centralized colors, emojis, limits, and other magic values.
All constants are typed and documented.
"""

from __future__ import annotations

import discord

# ======================================================================
# Embed Colors (Discord color values)
# ======================================================================


class Colors:
    """Curated color palette for bot embeds."""

    # Primary actions
    SUCCESS = discord.Color.from_rgb(87, 242, 135)  # Green
    ERROR = discord.Color.from_rgb(237, 66, 69)  # Red
    WARNING = discord.Color.from_rgb(254, 231, 92)  # Yellow
    INFO = discord.Color.from_rgb(88, 101, 242)  # Blurple
    NEUTRAL = discord.Color.from_rgb(153, 170, 181)  # Gray

    # Module-specific
    MODERATION = discord.Color.from_rgb(237, 66, 69)  # Red
    AUTOMOD = discord.Color.from_rgb(235, 69, 158)  # Pink
    SECURITY = discord.Color.from_rgb(194, 124, 14)  # Amber
    LOGS = discord.Color.from_rgb(88, 101, 242)  # Blurple
    WELCOME = discord.Color.from_rgb(87, 242, 135)  # Green
    TICKETS = discord.Color.from_rgb(69, 79, 191)  # Indigo
    GIVEAWAY = discord.Color.from_rgb(163, 99, 247)  # Purple
    ANALYTICS = discord.Color.from_rgb(32, 178, 170)  # Teal
    PREMIUM = discord.Color.from_rgb(255, 215, 0)  # Gold

    # Severity levels
    LOW = discord.Color.from_rgb(87, 242, 135)  # Green
    MEDIUM = discord.Color.from_rgb(254, 231, 92)  # Yellow
    HIGH = discord.Color.from_rgb(245, 165, 36)  # Orange
    CRITICAL = discord.Color.from_rgb(237, 66, 69)  # Red


# ======================================================================
# Emojis (Unicode)
# ======================================================================


class Emojis:
    """Unicode emojis used in bot messages."""

    # Status
    SUCCESS = "✅"
    ERROR = "❌"
    WARNING = "⚠️"
    INFO = "ℹ️"
    LOADING = "⏳"
    CLOCK = "🕐"

    # Moderation
    HAMMER = "🔨"
    BOOT = "🥾"
    SHIELD = "🛡️"
    LOCK = "🔒"
    UNLOCK = "🔓"
    MUTE = "🔇"
    UNMUTE = "🔊"
    TRASH = "🗑️"

    # Features
    WAVE = "👋"
    TICKET = "🎫"
    GIFT = "🎉"
    STAR = "⭐"
    CHART = "📊"
    BELL = "🔔"
    ROBOT = "🤖"
    CROWN = "👑"
    GEAR = "⚙️"
    PENCIL = "✏️"
    LINK = "🔗"
    BOOKMARK = "🔖"

    # Pagination
    FIRST = "⏪"
    PREVIOUS = "◀️"
    NEXT = "▶️"
    LAST = "⏩"
    STOP = "⏹️"

    # Voting
    UPVOTE = "👍"
    DOWNVOTE = "👎"

    # Numbers
    NUMBERS = ["0️⃣", "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]


# ======================================================================
# Limits
# ======================================================================


class Limits:
    """Discord API and application limits."""

    # Discord limits
    EMBED_TITLE_LENGTH = 256
    EMBED_DESCRIPTION_LENGTH = 4096
    EMBED_FIELD_NAME_LENGTH = 256
    EMBED_FIELD_VALUE_LENGTH = 1024
    EMBED_FOOTER_LENGTH = 2048
    EMBED_AUTHOR_NAME_LENGTH = 256
    EMBED_TOTAL_LENGTH = 6000
    EMBED_FIELD_COUNT = 25
    MESSAGE_LENGTH = 2000
    BULK_DELETE_LIMIT = 100
    BULK_DELETE_AGE_DAYS = 14

    # Application limits
    MAX_WARNINGS_PER_PAGE = 10
    MAX_ACTIONS_PER_PAGE = 10
    MAX_PURGE_MESSAGES = 500
    MAX_GIVEAWAY_WINNERS = 20
    MAX_REACTION_ROLES = 25
    DEFAULT_TIMEOUT_SECONDS = 60 * 60  # 1 hour
    MAX_TIMEOUT_SECONDS = 60 * 60 * 24 * 28  # 28 days (Discord max)

    # Automod thresholds (defaults, configurable per guild)
    DEFAULT_SPAM_THRESHOLD = 5  # messages per window
    DEFAULT_SPAM_WINDOW = 5  # seconds
    DEFAULT_MENTION_LIMIT = 5  # unique mentions per message
    DEFAULT_CAPS_PERCENTAGE = 70  # max percentage of caps
    DEFAULT_CAPS_MIN_LENGTH = 10  # min message length for caps check
    DEFAULT_EMOJI_LIMIT = 10  # max emojis per message
    DEFAULT_RAID_JOIN_THRESHOLD = 10  # joins per window
    DEFAULT_RAID_JOIN_WINDOW = 10  # seconds


# ======================================================================
# Module Names
# ======================================================================


class Modules:
    """Module identifiers used in GuildModuleSettings."""

    MODERATION = "moderation"
    AUTOMOD = "automod"
    SECURITY = "security"
    LOGS = "logs"
    WELCOME = "welcome"
    VERIFICATION = "verification"
    TICKETS = "tickets"
    REACTION_ROLES = "reaction_roles"
    GIVEAWAYS = "giveaways"
    SCHEDULER = "scheduler"
    NOTIFICATIONS = "notifications"
    ANALYTICS = "analytics"
    AI = "ai"
    TEMP_CHANNELS = "temp_channels"
    SUGGESTIONS = "suggestions"
    BACKUP = "backup"

    ALL: list[str] = [
        MODERATION,
        AUTOMOD,
        SECURITY,
        LOGS,
        WELCOME,
        VERIFICATION,
        TICKETS,
        REACTION_ROLES,
        GIVEAWAYS,
        SCHEDULER,
        NOTIFICATIONS,
        ANALYTICS,
        AI,
        TEMP_CHANNELS,
        SUGGESTIONS,
        BACKUP,
    ]
