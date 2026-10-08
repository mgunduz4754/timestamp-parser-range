import re
from datetime import datetime, timezone, timedelta
from typing import Tuple, Optional


# Compiled once at import. All parsing routes share this, so a malformed
# string is rejected before any timedelta arithmetic is attempted.
_TS_RE = re.compile(
    r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})"
    r"(?:\.(\d+))?"
    r"(Z|[+-]\d{2}:\d{2})$"
)


def _parse_offset(token: str) -> timezone:
    """Convert a ``Z`` or ``+HH:MM`` / ``-HH:MM`` token into a tzinfo.

    The grammar above already guarantees the shape, so the only branches
    here are the semantic ones. Returns a fixed-offset ``timezone``.
    """
    if token == "Z":
        return timezone.utc
    sign = 1 if token[0] == "+" else -1
    hours = int(token[1:3])
    minutes = int(token[4:6])
    if hours > 23 or minutes > 59:
        raise ValueError(f"offset out of range: {token}")
    return timezone(sign * timedelta(hours=hours, minutes=minutes))


def parse_timestamp(value: str) -> datetime:
    """Parse a single ISO 8601 timestamp into a timezone-aware ``datetime``.

    Accepted shape (subset of ISO 8601)::

        YYYY-MM-DDTHH:MM:SS[.ffffff](Z|+HH:MM|-HH:MM)

    Fractional seconds are accepted with 1 to 6 digits and are truncated
    (not rounded) to microseconds, matching how ``datetime`` stores them.
    The offset is mandatory; naive timestamps are rejected so that every
    returned value is unambiguous about its instant in time.

    Raises ``ValueError`` for strings that are not structurally a match or
    that contain out-of-range calendar/time fields.
    """
    if not isinstance(value, str):
        raise ValueError(f"expected str, got {type(value).__name__}")
    m = _TS_RE.match(value)
    if m is None:
        raise ValueError(f"not a compliant timestamp: {value!r}")

    year, month, day, hour, minute, second = (int(g) for g in m.group(1, 2, 3, 4, 5, 6))
    frac, off = m.group(7), m.group(8)

    micros = 0
    if frac is not None:
        # Right-pad to 6 digits so e.g. ".5" means 500000us and ".123456"
        # stays as-is. Extra digits beyond 6 are truncated, never rounded,
        # to avoid silently pushing a value across a second boundary.
        micros = int(frac.ljust(6, "0")[:6])

    tz = _parse_offset(off)
    return datetime(year, month, day, hour, minute, second, micros, tz)


def split_range(value: str) -> Tuple[str, str]:
    """Split an ISO 8601 interval into its two endpoint strings.

    This library recognises only the solidus form::

        <timestamp>/<timestamp>

    The double-solidus form (``<start>//<duration>``) is intentionally not
    supported; if it were, a string like ``2020-01-01T00:00:00Z//P1D`` would
    be ambiguous between "start//duration" and "start/end" where the end
    happened to begin with ``/P". Supporting one form removes that ambiguity.
    """
    if not isinstance(value, str):
        raise ValueError(f"expected str, got {type(value).__name__}")
    if "/" not in value:
        raise ValueError(f"not a range (missing '/'): {value!r}")
    left, sep, right = value.partition("/")
    if "/" in right:
        raise ValueError(f"range has more than two segments: {value!r}")
    if not left or not right:
        raise ValueError(f"range has an empty segment: {value!r}")
    return left, right


def parse_range(value: str) -> Tuple[datetime, datetime]:
    """Parse an ISO 8601 interval into a ``(start, end)`` pair of datetimes.

    Only ``<start>/<end>`` is supported (see :func:`split_range`). Both
    endpoints must independently satisfy :func:`parse_timestamp`. The
    function does not require ``start <= end``; callers that need that
    invariant should check it themselves.
    """
    left, right = split_range(value)
    return parse_timestamp(left), parse_timestamp(right)
