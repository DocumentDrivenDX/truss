# SPDX-License-Identifier: MIT OR Apache-2.0
"""Bounded, ordered DDL submissions on the caller's guarded cursor.

Units are captured source files or already quoted commands, not parsed SQL
statements. An original unit larger than the normal carrier limit is submitted
alone, unchanged. Transaction custody and the operation deadline remain owned
by the host.
"""

from collections.abc import Iterable

from psycopg import sql

_MAX_UNITS = 32
_MAX_BYTES = 128 * 1024
_SEPARATOR = "\n;\n"


def execute_ordered_ddl(cursor, units: Iterable[str | sql.Composable]) -> None:
    """Execute original units in order, retaining every driver error unchanged."""
    pending: list[str] = []
    pending_bytes = 0

    def submit() -> None:
        if not pending:
            return
        cursor.execute(_SEPARATOR.join(pending), prepare=False, binary=False)
        saw_rows = False
        while True:
            if cursor.description is not None:
                saw_rows = True
            if not cursor.nextset():
                break
        if saw_rows:
            raise ValueError('Installation DDL returned rows')

    for unit in units:
        if isinstance(unit, sql.Composable):
            rendered = unit.as_string(cursor.connection)
        elif isinstance(unit, str):
            rendered = unit
        else:
            raise TypeError('Installation DDL requires text or a composed command')
        if not rendered.strip():
            raise ValueError('Installation DDL requires a nonempty source unit')
        size = len(rendered.encode('utf-8'))
        combined = pending_bytes + (len(_SEPARATOR) if pending else 0) + size
        if pending and (len(pending) == _MAX_UNITS or combined > _MAX_BYTES):
            submit()
            pending.clear()
            pending_bytes = 0
        pending.append(rendered)
        pending_bytes += (len(_SEPARATOR) if len(pending) > 1 else 0) + size
        if size > _MAX_BYTES:
            submit()
            pending.clear()
            pending_bytes = 0
    submit()
