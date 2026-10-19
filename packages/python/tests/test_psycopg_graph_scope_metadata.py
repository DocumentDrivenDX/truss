# SPDX-License-Identifier: MIT OR Apache-2.0
"""Wrong graph metadata must refuse before invoking row decoders."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from truss._psycopg_graph_scope import _GraphScopeComparison, _run_graph_scope_operation


class GraphScopeMetadataTests(unittest.TestCase):
    def test_every_metadata_boundary_refuses_before_fetch(self):
        for phase in ('identity', 'before', 'registration', 'after'):
            for defect in ('absent', 'arity', 'oid', 'name'):
                if defect == 'name' and phase != 'registration':
                    continue
                with self.subTest(phase=phase, defect=defect):
                    class Cursor:
                        adapters = SimpleNamespace(register_dumper=lambda *args: None)
                        scope_reads = 0
                        def execute(self, sql, *args, **kwargs):
                            if sql.startswith('LOCK'):
                                return
                            if 'AS registered_types' in sql:
                                self.phase, count = 'registration', 1
                            elif 'authorization_graph_fact_scope' in sql:
                                self.scope_reads += 1
                                self.phase, count = ('before' if self.scope_reads == 1 else 'after'), 3
                            else:
                                self.phase, count = 'identity', 7
                            self.description = [SimpleNamespace(type_code=25, name='registered_types') for _ in range(count)]
                            if self.phase == phase:
                                if defect == 'absent': self.description = None
                                elif defect == 'arity': self.description = []
                                elif defect == 'oid': self.description[0].type_code = 23
                                else: self.description[0].name = 'substituted'
                        def fetchmany(self, count):
                            if self.phase == phase:
                                raise AssertionError('Unvalidated result reached row decoding')
                            if self.phase == 'identity': return [('1', '2', '3', 's', 'a', '4', '5')]
                            if self.phase == 'registration': return [('1',)]
                            return []
                    cursor = Cursor()
                    called = []
                    with patch('truss._psycopg_graph_scope._run_fenced_epoch_operation', side_effect=lambda h,t,e,callback: callback(cursor)):
                        with self.assertRaises(ValueError):
                            _run_graph_scope_operation(None, None, None, _GraphScopeComparison((100,), b'original'), lambda c: called.append(True))
                    self.assertEqual(cursor.phase, phase)
                    self.assertEqual(called, [])
