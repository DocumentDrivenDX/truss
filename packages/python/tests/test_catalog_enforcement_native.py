# SPDX-License-Identifier: MIT OR Apache-2.0
"""The registration report names who enforces each stored rule."""
import hashlib
import json
import os
from pathlib import Path

from psycopg import errors
from truss import CatalogDocument, CatalogRegistration, Ok, prepare_catalog

import test_group_create_native as base


class CatalogEnforcementTests(base.PublicCreateGroupTests):
    for _name in tuple(n for n in dir(base.PublicCreateGroupTests) if n.startswith('test_')):
        locals()[_name] = None

    def test_report_separates_database_constraints_from_engine_checks(self):
        raw = (Path(__file__).parent / 'fixtures/commerce-original-umf08.json').read_bytes()
        source = json.loads(raw)
        document = CatalogDocument(source['id'], hashlib.sha256(raw).hexdigest(), raw)
        prepared = prepare_catalog((document,), source_version='0.8.0', bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE', 'bun'))
        self.install()
        connection, host, assembly, transaction = self.consumer()
        accepted = assembly.accept_in_transaction(transaction, prepared, request_key='enforcement-report')
        self.assertIsInstance(accepted, Ok, repr(accepted) + ' ' + str(host._custody.last_attempt.error))
        self.assertIsInstance(accepted.value, CatalogRegistration)
        report = json.loads(accepted.value.report_bytes)
        rules = report['enforcement']

        def find(**wanted):
            return [rule for rule in rules if all(rule.get(key) == value for key, value in wanted.items())]

        self.assertTrue(find(rule='key.unique', enforcement='database', elementId='customers', keyId='identity'))
        self.assertTrue(find(rule='relationship.endpoint_types', enforcement='database', elementId='products.supplier_id'))
        self.assertTrue(find(rule='relationship.multiplicity', enforcement='engine', elementId='products.supplier_id'))
        self.assertTrue(find(rule='property.facets', enforcement='engine', elementId='refunds.amount'))
        host.detach()
        connection.commit()

        digest = bytes.fromhex('ab' * 32)
        key = bytes.fromhex('cd' * 32)
        self.admin.execute(
            'INSERT INTO truss.key_bucket_guard (namespace_sha256, key_sha256) VALUES (%s, %s)',
            (digest, key))
        with self.assertRaises(errors.UniqueViolation):
            self.admin.execute(
                'INSERT INTO truss.key_bucket_guard (namespace_sha256, key_sha256) VALUES (%s, %s)',
                (digest, key))

        relation = self.admin.execute(
            """SELECT r.rel_type_id, e.source_type, e.target_type, r.since_rev
               FROM truss.rel_def r
               JOIN truss.rel_endpoint e ON e.rel_type_id = r.rel_type_id
               WHERE r.rel_id = 'products.supplier_id' AND r.retired_rev IS NULL"""
        ).fetchone()
        other = self.admin.execute(
            "SELECT type_id FROM truss.type_def WHERE element = 'customers' AND retired_rev IS NULL"
        ).fetchone()[0]
        source_id = self.admin.execute(
            'INSERT INTO truss.object (type_id, rev) VALUES (%s, %s) RETURNING id',
            (relation[1], relation[3])).fetchone()[0]
        target_id = self.admin.execute(
            'INSERT INTO truss.object (type_id, rev) VALUES (%s, %s) RETURNING id',
            (relation[2], relation[3])).fetchone()[0]
        wrong_id = self.admin.execute(
            'INSERT INTO truss.object (type_id, rev) VALUES (%s, %s) RETURNING id',
            (other, relation[3])).fetchone()[0]
        with self.assertRaises(errors.ForeignKeyViolation):
            self.admin.execute(
                """INSERT INTO truss.edge (rel_type_id, source_id, source_type, target_id, target_type, rev)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (relation[0], source_id, relation[1], wrong_id, other, relation[3]))
        for _ in range(2):
            self.admin.execute(
                """INSERT INTO truss.edge (rel_type_id, source_id, source_type, target_id, target_type, rev)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (relation[0], source_id, relation[1], target_id, relation[2], relation[3]))
        self.assertEqual(
            self.admin.execute('SELECT count(*) FROM truss.edge WHERE rel_type_id = %s', (relation[0],)).fetchone()[0],
            2)
