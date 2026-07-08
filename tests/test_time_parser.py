"""Tests for the time_parser utility module."""

from __future__ import annotations

from datetime import timedelta

import pytest

from bot.utils.time_parser import (
    DurationParseError,
    format_duration,
    format_duration_short,
    format_seconds,
    parse_duration,
    parse_duration_seconds,
)

# ======================================================================
# parse_duration tests
# ======================================================================


class TestParseDuration:
    """Tests for the parse_duration function."""

    def test_parse_seconds(self) -> None:
        """Parse seconds only."""
        assert parse_duration("30s") == timedelta(seconds=30)
        assert parse_duration("45sec") == timedelta(seconds=45)
        assert parse_duration("60seconds") == timedelta(seconds=60)

    def test_parse_minutes(self) -> None:
        """Parse minutes only."""
        assert parse_duration("5m") == timedelta(minutes=5)
        assert parse_duration("30min") == timedelta(minutes=30)
        assert parse_duration("15minutes") == timedelta(minutes=15)

    def test_parse_hours(self) -> None:
        """Parse hours only."""
        assert parse_duration("2h") == timedelta(hours=2)
        assert parse_duration("12hr") == timedelta(hours=12)
        assert parse_duration("1hour") == timedelta(hours=1)
        assert parse_duration("24hours") == timedelta(hours=24)

    def test_parse_days(self) -> None:
        """Parse days only."""
        assert parse_duration("1d") == timedelta(days=1)
        assert parse_duration("7days") == timedelta(days=7)
        assert parse_duration("30day") == timedelta(days=30)

    def test_parse_weeks(self) -> None:
        """Parse weeks only."""
        assert parse_duration("1w") == timedelta(weeks=1)
        assert parse_duration("2weeks") == timedelta(weeks=2)
        assert parse_duration("4week") == timedelta(weeks=4)

    def test_parse_combined(self) -> None:
        """Parse combined duration strings."""
        assert parse_duration("2h30m") == timedelta(hours=2, minutes=30)
        assert parse_duration("1d12h") == timedelta(days=1, hours=12)
        assert parse_duration("1w2d3h") == timedelta(weeks=1, days=2, hours=3)
        assert parse_duration("1d2h30m45s") == timedelta(days=1, hours=2, minutes=30, seconds=45)

    def test_parse_with_spaces(self) -> None:
        """Parse durations with spaces between units."""
        assert parse_duration("2h 30m") == timedelta(hours=2, minutes=30)
        assert parse_duration("1d 12h") == timedelta(days=1, hours=12)

    def test_parse_case_insensitive(self) -> None:
        """Parse durations regardless of case."""
        assert parse_duration("2H30M") == timedelta(hours=2, minutes=30)
        assert parse_duration("1D") == timedelta(days=1)

    def test_parse_empty_string_raises(self) -> None:
        """Empty string should raise DurationParseError."""
        with pytest.raises(DurationParseError):
            parse_duration("")

    def test_parse_whitespace_only_raises(self) -> None:
        """Whitespace-only string should raise DurationParseError."""
        with pytest.raises(DurationParseError):
            parse_duration("   ")

    def test_parse_invalid_format_raises(self) -> None:
        """Invalid format should raise DurationParseError."""
        with pytest.raises(DurationParseError):
            parse_duration("abc")

    def test_parse_zero_duration_raises(self) -> None:
        """Zero duration should raise DurationParseError."""
        with pytest.raises(DurationParseError):
            parse_duration("0s")

    def test_parse_negative_not_supported(self) -> None:
        """Negative durations should raise DurationParseError."""
        with pytest.raises(DurationParseError):
            parse_duration("-5m")


class TestParseDurationSeconds:
    """Tests for the parse_duration_seconds convenience function."""

    def test_returns_integer_seconds(self) -> None:
        """Should return total seconds as an integer."""
        assert parse_duration_seconds("2h") == 7200
        assert parse_duration_seconds("30m") == 1800
        assert parse_duration_seconds("1d") == 86400

    def test_combined_duration(self) -> None:
        """Should handle combined durations."""
        assert parse_duration_seconds("1h30m") == 5400


# ======================================================================
# format_duration tests
# ======================================================================


class TestFormatDuration:
    """Tests for the format_duration function."""

    def test_format_seconds(self) -> None:
        """Format seconds only."""
        assert format_duration(timedelta(seconds=45)) == "45 seconds"

    def test_format_minutes(self) -> None:
        """Format minutes only."""
        assert format_duration(timedelta(minutes=30)) == "30 minutes"

    def test_format_hours(self) -> None:
        """Format hours only."""
        assert format_duration(timedelta(hours=2)) == "2 hours"

    def test_format_days(self) -> None:
        """Format days only."""
        assert format_duration(timedelta(days=1)) == "1 day"

    def test_format_weeks(self) -> None:
        """Format weeks."""
        assert format_duration(timedelta(weeks=1)) == "1 week"

    def test_format_combined(self) -> None:
        """Format combined durations."""
        result = format_duration(timedelta(hours=2, minutes=30))
        assert result == "2 hours 30 minutes"

    def test_format_singular_units(self) -> None:
        """Singular units should not have 's' suffix."""
        assert "1 day" in format_duration(timedelta(days=1))
        assert "1 hour" in format_duration(timedelta(hours=1))
        assert "1 minute" in format_duration(timedelta(minutes=1))
        assert "1 second" in format_duration(timedelta(seconds=1))

    def test_format_zero(self) -> None:
        """Zero duration should return '0 seconds'."""
        assert format_duration(timedelta(seconds=0)) == "0 seconds"


class TestFormatDurationShort:
    """Tests for the format_duration_short function."""

    def test_short_format(self) -> None:
        """Should produce compact output."""
        assert format_duration_short(timedelta(hours=2, minutes=30)) == "2h 30m"
        assert format_duration_short(timedelta(days=1)) == "1d"
        assert format_duration_short(timedelta(seconds=45)) == "45s"
        assert format_duration_short(timedelta(weeks=1, days=2)) == "1w 2d"

    def test_short_format_zero(self) -> None:
        """Zero duration should return '0s'."""
        assert format_duration_short(timedelta(seconds=0)) == "0s"


class TestFormatSeconds:
    """Tests for the format_seconds convenience function."""

    def test_format_from_int(self) -> None:
        """Should format raw seconds into human-readable string."""
        assert format_seconds(3600) == "1 hour"
        assert format_seconds(90) == "1 minute 30 seconds"
        assert format_seconds(86400) == "1 day"
