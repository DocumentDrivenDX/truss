# SPDX-License-Identifier: MIT OR Apache-2.0
"""Ordered cascade simulation; no public owned-write support claim."""
import json
from pathlib import Path
import psycopg
import test_numeric_facets_native as numeric


class OwnedDeleteSimulationTests(numeric.NumericFacetTests):
    for name in tuple(n for n in dir(numeric.NumericFacetTests) if n.startswith('test_')):
        locals()[name] = None

    def test_subtree_parallel_edges_and_prior_unlink(self):
        connection, host, assembly, tx = self.ready(self.fields)
        host.detach()
        connection.rollback()
        for source in ('delete.sql',):
            self.admin.execute(Path(__file__).with_name(source).read_text())
        # Nodes: root, child, grandchild, outside boundary witness.
        owned = [{'edge': 3, 'source': 0, 'target': 1},
                 {'edge': 4, 'source': 0, 'target': 1},
                 {'edge': 9, 'source': 1, 'target': 2}]
        def project(independent):
            return self.admin.execute(
                'SELECT truss.owned_delete_projection(3,%s::jsonb,%s::jsonb,1)',
                (json.dumps(owned), json.dumps(independent))).fetchone()[0]
        inventory_sql = ('SELECT (SELECT count(*) FROM truss.object),'
                         '(SELECT count(*) FROM truss.edge),'
                         '(SELECT count(*) FROM truss.journal),'
                         '(SELECT count(*) FROM truss.request_receipt)')
        before = self.admin.execute(inventory_sql).fetchone()
        self.assertEqual(project([]), {'deletedNodes': [1, 2], 'deletedEdges': [3, 4, 9]})
        for edge in ({'edge': 10, 'source': 2, 'target': 3},
                     {'edge': 10, 'source': 1, 'target': 2}):
            with self.assertRaises(psycopg.Error) as refused:
                project([edge])
            self.assertEqual(refused.exception.sqlstate, '22023')
        # A prior unlink removes the edge from this ordered simulation.
        self.assertEqual(project([])['deletedNodes'], [1, 2])
        # Intermediate cycles are traversed once, not prematurely rejected.
        owned.append({'edge': 11, 'source': 2, 'target': 1})
        self.assertEqual(project([]), {'deletedNodes': [1, 2], 'deletedEdges': [3, 4, 9, 11]})
        self.assertEqual(self.admin.execute(inventory_sql).fetchone(), before)
