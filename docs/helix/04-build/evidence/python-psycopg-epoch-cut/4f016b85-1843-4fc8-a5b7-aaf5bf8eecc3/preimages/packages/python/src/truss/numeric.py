"""Python conveniences for already admitted finite numeric tokens.

This module converts already admitted tokens; it does not admit UMF grammar,
facets or a native storage domain.
The caller supplies its selected finite byte bound; original spelling is retained.
No arithmetic, key normalization or native-domain qualification is performed.
"""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


@dataclass(frozen=True)
class ExactInteger:
    original_text: str
    value: int


@dataclass(frozen=True)
class ExactDecimal:
    original_text: str
    value: Decimal


def _bounded_text(token: str, maximum_bytes: int) -> str:
    if type(token) is not str or type(maximum_bytes) is not int or maximum_bytes <= 0:
        raise ValueError("Original text and a selected positive byte bound required")
    if len(token) > maximum_bytes:
        raise ValueError("Exact token exceeds selected bound")
    try:
        size = len(token.encode("utf-8", errors="strict"))
    except UnicodeError as error:
        raise ValueError("Original token is not UTF-8") from error
    if size > maximum_bytes:
        raise ValueError("Exact token exceeds selected bound")
    return token


def integer_from_admitted_text(token: str, maximum_bytes: int) -> ExactInteger:
    original = _bounded_text(token, maximum_bytes)
    # Host conversion only: source grammar/range/facets are admitted upstream.
    try:
        value = int(original, 10)
    except ValueError as error:
        raise ValueError("Exact integer conversion unavailable") from error
    return ExactInteger(original, value)


def decimal_from_admitted_text(token: str, maximum_bytes: int) -> ExactDecimal:
    original = _bounded_text(token, maximum_bytes)
    try:
        # Constructing from text preserves digits without ambient-context rounding.
        value = Decimal(original)
    except InvalidOperation as error:
        raise ValueError("Exact decimal conversion unavailable") from error
    if not value.is_finite():
        raise ValueError("Finite admitted decimal required")
    return ExactDecimal(original, value)


def integral_host_value(value: int) -> int:
    # bool is an int subclass in Python; it cannot enter an integral domain.
    if type(value) is not int:
        raise ValueError("An exact Python int is required")
    return value
