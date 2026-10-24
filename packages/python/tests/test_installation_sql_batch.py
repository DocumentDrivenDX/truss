# SPDX-License-Identifier: MIT OR Apache-2.0
"""Offline controls for bounded, ordered installer DDL submissions."""

import unittest

from psycopg import sql
from truss._installation_sql_batch import execute_ordered_ddl


class FakeCursor:
    def __init__(self, *, nextsets=0, description=None, error=None):
        self.connection = None
        self.nextsets_per_execute = nextsets
        self.description_after_execute = description
        self.error = error
        self.executions = []
        self.nextset_calls = 0
        self.remaining_nextsets = 0
        self.description = None

    def execute(self, query, *args, **kwargs):
        if self.error is not None:
            raise self.error
        self.executions.append((query, args, kwargs))
        self.remaining_nextsets = self.nextsets_per_execute
        self.description = self.description_after_execute
        return self

    def nextset(self):
        self.nextset_calls += 1
        if self.remaining_nextsets:
            self.remaining_nextsets -= 1
            self.description = None
            return True
        return None


class InstallationSqlBatchTests(unittest.TestCase):
    def test_preserves_ordered_source_and_drains_every_result_set(self):
        units = [f"-- source {index}\nSELECT {index};" for index in range(37)]
        cursor = FakeCursor(nextsets=2)

        execute_ordered_ddl(cursor, units)

        self.assertEqual(len(cursor.executions), 2)
        self.assertEqual(
            [query for query, _, _ in cursor.executions],
            ["\n;\n".join(units[:32]), "\n;\n".join(units[32:])],
        )
        self.assertEqual(cursor.nextset_calls, 6)
        for _, args, kwargs in cursor.executions:
            self.assertEqual(args, ())
            self.assertEqual(kwargs, {"prepare": False, "binary": False})

    def test_utf8_limit_includes_batch_separator(self):
        first = "a" * 65_534
        second = "é" * 32_767 + "b"  # exactly 65,535 UTF-8 bytes
        third = "SELECT 3;"
        self.assertEqual(
            len(first.encode("utf-8")) + len(second.encode("utf-8")) + 3, 128 * 1024
        )
        cursor = FakeCursor()

        execute_ordered_ddl(cursor, (first, second, third))

        self.assertEqual(
            [call[0] for call in cursor.executions], [first + "\n;\n" + second, third]
        )

    def test_original_oversize_unit_is_submitted_alone_unchanged(self):
        large = "-- retain unicode and punctuation: é;\n" + ("x" * (128 * 1024))
        following = "/* following */ SELECT 7;"
        cursor = FakeCursor()

        execute_ordered_ddl(cursor, (following, large, following))

        self.assertEqual(
            [call[0] for call in cursor.executions], [following, large, following]
        )

    def test_composable_is_rendered_using_the_cursor_connection(self):
        cursor = FakeCursor()
        unit = sql.SQL("CREATE SCHEMA {}").format(sql.Identifier("kept_name"))

        execute_ordered_ddl(cursor, (unit,))

        self.assertEqual(cursor.executions[0][0], 'CREATE SCHEMA "kept_name"')

    def test_row_result_is_rejected(self):
        cursor = FakeCursor(nextsets=2, description=(("value",),))

        with self.assertRaisesRegex(ValueError, "DDL returned rows"):
            execute_ordered_ddl(cursor, ("SELECT 1",))
        self.assertEqual(cursor.nextset_calls, 3)

    def test_empty_and_unsupported_units_fail_before_execution(self):
        for unit in ("", "  \n ", object()):
            with self.subTest(unit_type=type(unit).__name__):
                cursor = FakeCursor()
                with self.assertRaises((TypeError, ValueError)):
                    execute_ordered_ddl(cursor, (unit,))
                self.assertEqual(cursor.executions, [])

    def test_driver_exception_is_propagated_without_wrapping(self):
        error = RuntimeError("driver sentinel")
        cursor = FakeCursor(error=error)

        with self.assertRaises(RuntimeError) as raised:
            execute_ordered_ddl(cursor, ("CREATE SCHEMA one",))

        self.assertIs(raised.exception, error)


if __name__ == "__main__":
    unittest.main()
