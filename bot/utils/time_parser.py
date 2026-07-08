"""Time parser — converts human-readable duration strings to timedelta.

Supports duration strings like:
    "2h30m"    → timedelta(hours=2, minutes=30)
    "1d12h"    → timedelta(days=1, hours=12)
    "30s"      → timedelta(seconds=30)
    "1w2d"     → timedelta(weeks=1, days=2)
    "7d"       → timedelta(days=7)

Also provides formatting functions to convert timedelta back to
human-readable strings.

Usage:
    from bot.utils.time_parser import parse_duration, format_duration

    delta = parse_duration("2h30m")  # timedelta(hours=2, minutes=30)
    text = format_duration(delta)    # "2 hours 30 minutes"
"""

from __future__ import annotations

import re
from datetime import timedelta

# Regex pattern matching duration units
# Matches sequences like: 1w 2d 3h 30m 45s
_DURATION_PATTERN = re.compile(
    r"(?:(\d+)\s*w(?:eeks?)?)?\s*"
    r"(?:(\d+)\s*d(?:ays?)?)?\s*"
    r"(?:(\d+)\s*h(?:(?:ou)?rs?)?)?\s*"
    r"(?:(\d+)\s*m(?:in(?:ute)?s?)?)?\s*"
    r"(?:(\d+)\s*s(?:ec(?:ond)?s?)?)?\s*$",
    re.IGNORECASE,
)

# Individual unit pattern for strict validation
_UNIT_PATTERN = re.compile(
    r"(\d+)\s*(w(?:eeks?)?|d(?:ays?)?|h(?:(?:ou)?rs?)?|m(?:in(?:ute)?s?)?|s(?:ec(?:ond)?s?)?)",
    re.IGNORECASE,
)


class DurationParseError(ValueError):
    """Raised when a duration string cannot be parsed."""

    def __init__(self, input_string: str) -> None:
        self.input_string = input_string
        super().__init__(
            f"Could not parse duration: '{input_string}'. "
            f"Expected format: 1w2d3h30m45s (e.g., '2h30m', '1d', '30s')"
        )


def parse_duration(duration_string: str) -> timedelta:
    """Parse a human-readable duration string into a timedelta.

    Supported units:
    - w / week / weeks
    - d / day / days
    - h / hr / hrs / hour / hours
    - m / min / mins / minute / minutes
    - s / sec / secs / second / seconds

    Args:
        duration_string: Human-readable duration (e.g., "2h30m", "1d12h").

    Returns:
        A timedelta representing the parsed duration.

    Raises:
        DurationParseError: If the string cannot be parsed.
    """
    cleaned = duration_string.strip()
    if not cleaned:
        raise DurationParseError(duration_string)

    # Try to match the full pattern
    match = _DURATION_PATTERN.match(cleaned)
    if not match or not any(match.groups()):
        raise DurationParseError(duration_string)

    weeks = int(match.group(1) or 0)
    days = int(match.group(2) or 0)
    hours = int(match.group(3) or 0)
    minutes = int(match.group(4) or 0)
    seconds = int(match.group(5) or 0)

    total = timedelta(
        weeks=weeks,
        days=days,
        hours=hours,
        minutes=minutes,
        seconds=seconds,
    )

    if total.total_seconds() <= 0:
        raise DurationParseError(duration_string)

    return total


def parse_duration_seconds(duration_string: str) -> int:
    """Parse a duration string and return total seconds.

    Convenience wrapper around parse_duration().

    Args:
        duration_string: Human-readable duration string.

    Returns:
        Total seconds as an integer.

    Raises:
        DurationParseError: If the string cannot be parsed.
    """
    return int(parse_duration(duration_string).total_seconds())


def format_duration(delta: timedelta) -> str:
    """Format a timedelta into a human-readable string.

    Examples:
        timedelta(hours=2, minutes=30) → "2 hours 30 minutes"
        timedelta(days=1) → "1 day"
        timedelta(seconds=45) → "45 seconds"
        timedelta(days=7) → "1 week"

    Args:
        delta: The timedelta to format.

    Returns:
        A human-readable duration string.
    """
    total_seconds = int(delta.total_seconds())

    if total_seconds <= 0:
        return "0 seconds"

    weeks, remainder = divmod(total_seconds, 604800)
    days, remainder = divmod(remainder, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts: list[str] = []

    if weeks:
        parts.append(f"{weeks} week{'s' if weeks != 1 else ''}")
    if days:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if seconds:
        parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")

    return " ".join(parts)


def format_duration_short(delta: timedelta) -> str:
    """Format a timedelta into a compact string.

    Examples:
        timedelta(hours=2, minutes=30) → "2h 30m"
        timedelta(days=1) → "1d"
        timedelta(seconds=45) → "45s"

    Args:
        delta: The timedelta to format.

    Returns:
        A compact duration string.
    """
    total_seconds = int(delta.total_seconds())

    if total_seconds <= 0:
        return "0s"

    weeks, remainder = divmod(total_seconds, 604800)
    days, remainder = divmod(remainder, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts: list[str] = []

    if weeks:
        parts.append(f"{weeks}w")
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if seconds:
        parts.append(f"{seconds}s")

    return " ".join(parts)


def format_seconds(seconds: int) -> str:
    """Format raw seconds into a human-readable string.

    Convenience wrapper around format_duration().

    Args:
        seconds: Number of seconds.

    Returns:
        Human-readable duration string.
    """
    return format_duration(timedelta(seconds=seconds))
