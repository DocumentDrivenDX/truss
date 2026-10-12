"""Bounded exact owner-evidence JSON; never a Truss semantic wire codec.

Original bytes remain authoritative. Numbers are inspected without conversion
through binary floating point; this does not issue catalog support or authority.
"""
import json
from decimal import Decimal, DecimalException, InvalidOperation, localcontext


def decode_owner_evidence_json(original):
    if type(original) is not bytes or not 1 <= len(original) <= 8_388_608:
        raise ValueError('Bounded original owner evidence required')

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('Duplicate owner evidence member')
            result[key] = value
        return result

    def number(token, convert):
        if len(token) > 512:
            raise ValueError('Owner evidence number token capacity exceeded')
        try:
            with localcontext() as context:
                context.traps[InvalidOperation] = True
                return convert(token)
        except DecimalException as error:
            raise ValueError('Owner evidence number representation unavailable') from error

    def nonfinite(token):
        raise ValueError('Finite JSON owner evidence required')

    try:
        value = json.loads(original.decode('utf-8'), object_pairs_hook=pairs,
                           parse_int=lambda token: number(token, int),
                           parse_float=lambda token: number(token, Decimal),
                           parse_constant=nonfinite)
    except (UnicodeError, RecursionError) as error:
        raise ValueError('Invalid owner evidence encoding or nesting') from error
    pending = [(value, 0)]; nodes = 0
    while pending:
        item, depth = pending.pop(); nodes += 1
        if nodes > 1_000_000 or depth > 128:
            raise ValueError('Owner evidence tree capacity exceeded')
        if type(item) is dict:
            if len(item) > 4096:
                raise ValueError('Owner evidence object capacity exceeded')
            pending.extend((key, depth + 1) for key in item)
            pending.extend((child, depth + 1) for child in item.values())
        elif type(item) is list:
            if len(item) > 4096:
                raise ValueError('Owner evidence array capacity exceeded')
            pending.extend((child, depth + 1) for child in item)
        elif type(item) is str:
            if any(0xD800 <= ord(char) <= 0xDFFF for char in item):
                raise ValueError('Unicode scalar owner evidence required')
        elif type(item) is Decimal and not item.is_finite():
            raise ValueError('Finite owner evidence required')
    return value


def same_owner_evidence(left, right):
    """Compare parsed source meaning without Python bool/int coercion."""
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        return left.keys() == right.keys() and all(
            same_owner_evidence(left[key], right[key]) for key in left)
    if type(left) is list:
        return len(left) == len(right) and all(
            same_owner_evidence(a, b) for a, b in zip(left, right))
    if type(left) is Decimal:
        return left.as_tuple() == right.as_tuple()
    return left == right
