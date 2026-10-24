# SPDX-License-Identifier: MIT OR Apache-2.0
"""Pure controls for exact installation privilege facts and routine lookup."""

import unittest

from truss._installation_privileges import _exact_boolean_facts, _resolve_signatures
from truss._installation_sql_batch import execute_ordered_ddl


class FakeCursor:
    def __init__(self, rows):
        self.rows = list(rows)
        self.executions = []

    def execute(self, query, params=(), **kwargs):
        self.executions.append((query, params, kwargs))
        return self

    def fetchmany(self, size):
        rows, self.rows = self.rows[:size], self.rows[size:]
        return rows


class FailingNextsetCursor:
    def __init__(self, error):
        self.error = error
        self.executions = []
        self.description = None
        self.nextset_calls = 0

    def execute(self, query, **kwargs):
        self.executions.append(query)

    def nextset(self):
        self.nextset_calls += 1
        if self.nextset_calls == 1:
            return True
        raise self.error


class InstallationSetFactTests(unittest.TestCase):
    def test_exact_boolean_facts_accept_complete_false_inventory(self):
        cursor = FakeCursor([(10, False), (20, False)])
        self.assertIsNone(_exact_boolean_facts(
            cursor, "facts", (), (20, 10), "unexpected privilege"))

    def test_exact_boolean_facts_reject_missing_duplicate_and_extra_oids(self):
        cases = (
            [(10, False)],
            [(10, False), (10, False)],
            [(10, False), (20, False), (30, False)],
        )
        for rows in cases:
            with self.subTest(rows=rows), self.assertRaisesRegex(
                    ValueError, "observations are incomplete"):
                _exact_boolean_facts(
                    FakeCursor(rows), "facts", (), (10, 20), "unexpected privilege")

    def test_exact_boolean_facts_rejects_null_and_bool_as_oid(self):
        for rows in ([(10, None)], [(True, False)]):
            with self.subTest(rows=rows), self.assertRaisesRegex(
                    ValueError, "observations are incomplete"):
                _exact_boolean_facts(
                    FakeCursor(rows), "facts", (), (10,), "unexpected privilege")

    def test_exact_boolean_facts_reports_a_true_privilege(self):
        with self.assertRaisesRegex(ValueError, "unexpected privilege"):
            _exact_boolean_facts(
                FakeCursor([(10, True)]), "facts", (), (10,), "unexpected privilege")

    def test_resolve_signatures_preserves_order_and_optional_null(self):
        signatures = ("present()", "optional()")
        cursor = FakeCursor([(1, signatures[0], 101), (2, signatures[1], None)])
        self.assertEqual(_resolve_signatures(cursor, signatures), (101, None))
        query, params, kwargs = cursor.executions[0]
        self.assertIn("WITH ORDINALITY", query)
        self.assertEqual(params, (list(signatures),))
        self.assertEqual(kwargs, {"prepare": False})

    def test_resolve_signatures_rejects_wrong_ordinal_or_name(self):
        signatures = ("first()", "second()")
        cases = (
            [(2, "first()", 101), (1, "second()", 102)],
            [(1, "wrong()", 101), (2, "second()", 102)],
        )
        for rows in cases:
            with self.subTest(rows=rows), self.assertRaisesRegex(
                    ValueError, "signature resolution is incomplete"):
                _resolve_signatures(FakeCursor(rows), signatures)

    def test_resolve_signatures_rejects_missing_or_ill_typed_rows(self):
        signatures = ("one()", "two()")
        cases = (
            [(1, "one()", 101)],
            [(1, "one()", True), (2, "two()", 102)],
            [(1, "one()", 101), (2, "two()", None), (3, "three()", 103)],
        )
        for rows in cases:
            with self.subTest(rows=rows), self.assertRaisesRegex(
                    ValueError, "signature resolution is incomplete"):
                _resolve_signatures(FakeCursor(rows), signatures)

    def test_later_nextset_exception_is_preserved_without_next_batch(self):
        error = RuntimeError("nextset sentinel")
        cursor = FailingNextsetCursor(error)

        with self.assertRaises(RuntimeError) as raised:
            execute_ordered_ddl(cursor, tuple(f"SELECT {i}" for i in range(33)))

        self.assertIs(raised.exception, error)
        self.assertEqual(len(cursor.executions), 1)
        self.assertEqual(cursor.nextset_calls, 2)


if __name__ == "__main__":
    unittest.main()
