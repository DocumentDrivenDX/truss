"""Foreign catalog descriptors must refuse before row decoding or callback.
@covers US-056-AC10
"""
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from truss._psycopg_fact_cut import (
    _FactRelationComparison, _FactColumnComparison, _run_fenced_fact_operation,
)


class FactCutDescriptorBoundaryTests(unittest.TestCase):
    def test_each_catalog_stage_refuses_foreign_oid_before_fetch(self):
        for stage in (1, 2, 3):
            with self.subTest(stage=stage):
                cursor = CatalogCursor(stage)
                callbacks = []
                relation = _FactRelationComparison('truss', 'fact', 10, 20, 'body',
                    (_FactColumnComparison('id', 1, 25, -1, True, 0),))
                def epoch_scope(host, transaction, comparison, acquire):
                    return acquire(cursor)
                with patch('truss._psycopg_fact_cut._run_fenced_epoch_operation', epoch_scope):
                    with self.assertRaisesRegex(ValueError, 'TEXT .* descriptors'):
                        _run_fenced_fact_operation(None, None, None, (relation,),
                            lambda c: callbacks.append(c))
                self.assertEqual(cursor.foreign_fetches, 0)
                self.assertEqual(callbacks, [])
                self.assertEqual(cursor.stage, stage)


class CatalogCursor:
    def __init__(self, bad_stage):
        self.bad_stage = bad_stage
        self.stage = 0
        self.foreign_fetches = 0
        self.description = None

    def execute(self, statement, *args, **kwargs):
        if str(statement).startswith('SELECT'):
            self.stage += 1
            width = (7, 12, 9)[self.stage - 1]
            self.description = [SimpleNamespace(type_code=25) for _ in range(width)]
            if self.stage == self.bad_stage:
                self.description[0].type_code = 19  # native NAME, not TEXT

    def fetchmany(self, count):
        if self.stage == self.bad_stage:
            self.foreign_fetches += 1
            raise AssertionError('foreign row decoder entered')
        if self.stage == 1:
            return [('10', '20', 'r', 'p', 'false', 'false', 'false')]
        return [('A', '62', '0', '', 'false', 'true', '20', 'false', 'v',
                 '["search_path=pg_catalog, pg_temp"]', 'body', 'false')]
