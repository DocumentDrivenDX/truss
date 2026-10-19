# SPDX-License-Identifier: MIT OR Apache-2.0
"""Registration reports distinguish physical constraints from engine checks."""
import hashlib
import json
import os
from pathlib import Path

from psycopg import errors
from truss import CatalogDocument, CatalogRegistration, Ok, prepare_catalog
from truss.groups import GroupFailed, GroupSuccess, RequestNone

import test_group_create_native as base


class CatalogEnforcementTests(base.PublicCreateGroupTests):
    for _name in tuple(n for n in dir(base.PublicCreateGroupTests) if n.startswith('test_')):
        locals()[_name] = None

    def test_report_separates_database_constraints_from_engine_checks(self):
        raw = (Path(__file__).parent / 'fixtures/commerce-current-umf10.json').read_bytes()
        source = json.loads(raw)
        self.assertEqual(source['umf'], '0.10.0')
        document = CatalogDocument(source['id'], hashlib.sha256(raw).hexdigest(), raw)
        prepared = prepare_catalog((document,), source_version='0.10.0',
            bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE', 'bun'))
        self.install()
        connection, host, assembly, transaction = self.consumer()
        accepted = assembly.accept_in_transaction(transaction, prepared, request_key='enforcement-report')
        self.assertIsInstance(accepted, Ok, repr(accepted) + ' ' + str(host._custody.last_attempt.error))
        self.assertIsInstance(accepted.value, CatalogRegistration)
        rules = json.loads(accepted.value.report_bytes)['enforcement']

        def find(**wanted):
            return [rule for rule in rules if all(rule.get(key) == value for key, value in wanted.items())]

        self.assertTrue(find(rule='key.unique', enforcement='engine', elementId='customers', keyId='identity'))
        self.assertTrue(find(rule='relationship.endpoint_types', enforcement='database', elementId='products.supplier_id'))
        self.assertTrue(find(rule='relationship.multiplicity', enforcement='engine', elementId='products.supplier_id'))
        self.assertTrue(find(rule='property.facets', enforcement='engine', elementId='refunds.amount'))
        host.detach()
        connection.commit()

        relation = self.admin.execute(
            """SELECT r.rel_type_id, e.source_type, e.target_type, r.since_rev
               FROM truss.rel_def r JOIN truss.rel_endpoint e USING(rel_type_id)
               WHERE r.rel_id = 'products.supplier_id' AND r.retired_rev IS NULL""").fetchone()
        other = self.admin.execute("SELECT type_id FROM truss.type_def WHERE element = 'customers' AND retired_rev IS NULL").fetchone()[0]
        # These rolled-back writes isolate table constraints; they do not invoke
        # or qualify a privileged alternative to the supported engine write API.
        with self.admin.transaction(force_rollback=True):
            source_id = self.admin.execute('INSERT INTO truss.object(type_id,rev) VALUES(%s,%s) RETURNING id', (relation[1], relation[3])).fetchone()[0]
            target_id = self.admin.execute('INSERT INTO truss.object(type_id,rev) VALUES(%s,%s) RETURNING id', (relation[2], relation[3])).fetchone()[0]
            wrong_id = self.admin.execute('INSERT INTO truss.object(type_id,rev) VALUES(%s,%s) RETURNING id', (other, relation[3])).fetchone()[0]
            with self.assertRaises(errors.ForeignKeyViolation), self.admin.transaction():
                self.admin.execute('INSERT INTO truss.edge(rel_type_id,source_id,source_type,target_id,target_type,rev) VALUES(%s,%s,%s,%s,%s,%s)',
                    (relation[0], source_id, relation[1], wrong_id, other, relation[3]))
            for _ in range(2):
                self.admin.execute('INSERT INTO truss.edge(rel_type_id,source_id,source_type,target_id,target_type,rev) VALUES(%s,%s,%s,%s,%s,%s)',
                    (relation[0], source_id, relation[1], target_id, relation[2], relation[3]))
            self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.edge WHERE rel_type_id=%s', (relation[0],)).fetchone()[0], 2)

    def test_business_key_uniqueness_is_engine_enforced_across_objects(self):
        connection, host, assembly, transaction = self.ready(document_ids=('adoc',))
        created = self.apply(assembly, transaction, *self.input(assembly, transaction))
        self.assertIsInstance(created, GroupSuccess)
        identity = created.response.semantic.results[0].identity
        host.detach()
        connection.commit()
        connection, host, assembly, transaction = self.consumer()
        semantic, _ = self.input(assembly, transaction, (self.create(label='one', value='another', alias='duplicate'),))
        duplicate = self.apply(assembly, transaction, semantic, RequestNone())
        self.assertIsInstance(duplicate, GroupFailed)
        host.detach()
        connection.rollback()
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone()[0], 1)

        with self.admin.transaction(force_rollback=True):
            second_id = self.admin.execute(
                """INSERT INTO truss.object(type_id,props,retained,root_id,root_type,rev,ver,created_at,updated_at)
                   SELECT type_id,props,retained,root_id,root_type,rev,ver,created_at,updated_at
                   FROM truss.object WHERE id=%s AND type_id=%s RETURNING id""",
                (int(identity.id), int(identity.type_id))).fetchone()[0]
            route = self.admin.execute(
                """INSERT INTO truss.object_key_bucket(type_id,key_num,object_id,namespace_bytes,key_bytes,original_context_bytes)
                   SELECT type_id,key_num,%s,namespace_bytes,key_bytes,original_context_bytes
                   FROM truss.object_key_bucket WHERE object_id=%s AND type_id=%s ORDER BY key_num LIMIT 1
                   RETURNING namespace_bytes,key_bytes""",
                (second_id, int(identity.id), int(identity.type_id))).fetchone()
            self.assertEqual(self.admin.execute(
                'SELECT count(*) FROM truss.key_bucket_guard WHERE namespace_sha256=sha256(%s) AND key_sha256=sha256(%s)', route).fetchone()[0], 1)
            self.assertEqual(self.admin.execute(
                'SELECT count(DISTINCT object_id) FROM truss.object_key_bucket WHERE namespace_bytes=%s AND key_bytes=%s', route).fetchone()[0], 2)
