"""exceptions for dewata calendar engine."""

from __future__ import annotations


class CalendarError(Exception):
    """base exception for dewata calendar engine."""


class InvalidDateError(CalendarError):
    """date is outside the engine's supported range."""


class RulesetMismatchError(CalendarError):
    """the requested operation conflicts with the active ruleset version."""
