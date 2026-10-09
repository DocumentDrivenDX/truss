"""Private convenience view of already admitted offset timestamp text.

Original source semantics remain upstream. Unavailable datetime conversion never
rewrites the token, normalizes its offset or claims the source token is invalid.
"""
from dataclasses import dataclass
from datetime import datetime
import re

from python_exact_numeric_candidate import _bounded_text


@dataclass(frozen=True)
class ExactTimestamp:
    original_text: str
    datetime_view: datetime | None


_VIEW_SUBSET = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(?:\.([0-9]{1,9}))?(Z|[+-][0-9]{2}:[0-9]{2})"
)


def timestamp_from_admitted_text(token: str, maximum_bytes: int) -> ExactTimestamp:
    original = _bounded_text(token, maximum_bytes)
    match = _VIEW_SUBSET.fullmatch(original)
    if not match:
        return ExactTimestamp(original, None)
    fraction, offset = match.groups()
    # Unknown local offset cannot be changed to an asserted UTC offset.
    if offset == "-00:00" or (fraction and any(digit != "0" for digit in fraction[6:])):
        return ExactTimestamp(original, None)
    # Python normalizes minute overflow such as +00:60 into another offset.
    # Conversion availability must not silently assign meaning to such a token.
    if offset != "Z" and (int(offset[1:3]) > 23 or int(offset[4:6]) > 59):
        return ExactTimestamp(original, None)
    try:
        view = datetime.fromisoformat(original)
    except ValueError:
        # Includes leap seconds and dates outside Python's realizable domain.
        return ExactTimestamp(original, None)
    if view.tzinfo is None or view.utcoffset() is None:
        return ExactTimestamp(original, None)
    return ExactTimestamp(original, view)
