# SPDX-License-Identifier: MIT OR Apache-2.0
"""Prepared group admission verifies exact document sources without cross-call reuse."""
import json

import psycopg

from truss import CatalogRuntimeConfiguration, ModuleAccessGrant, Ok, adopt_psycopg_host, create_reference_assembly
from truss.contracts import MapValue
import test_group_create_native as base


class GroupSourceAdmissionTests(base.PublicCreateGroupTests):
    for name in tuple(n for n in dir(base.PublicCreateGroupTests) if n.startswith('test_')):
        locals()[name] = None

    def enable_second_document(self):
        self.admin.execute('BEGIN')
        admin_host = adopt_psycopg_host(self.admin)
        admin_tx = admin_host.adopt_transaction().value
        admin_assembly = create_reference_assembly(CatalogRuntimeConfiguration(), admin_host).value
        configured = admin_assembly.configure_module_access_in_transaction(
            admin_tx, (ModuleAccessGrant('zdoc', 'm', 'group_reader', 'group_writer'),))
        self.assertIsInstance(configured, Ok, repr(configured))
        admin_host.detach()
        self.admin.commit()

    def raw_apply(self, connection, assembly, tx, operations, documents):
        from truss._group_runtime import _bytes, _wire
        from truss.catalog_runtime import _release

        context = assembly.group_context_in_transaction(tx)
        self.assertIsInstance(context, Ok, repr(context))
        original_input = _bytes(_wire(context.value.input(operations, MapValue(entries=()))))
        original_documents = _bytes(documents)
        release, digest, _ = _release()
        payload = connection.execute(
            'SELECT truss.apply_group(%s,%s,%s,%s,%s)',
            (original_input, original_documents, b'{"state":"none"}', release['releaseId'], digest),
        ).fetchone()[0]
        return json.loads(bytes(payload))

    def original_documents(self):
        return [{'documentId': document.document_id, 'sourceText': document.content.decode('utf-8')}
                for document in self.documents]

    def assert_no_group_effects(self, connection):
        for table in ('object', 'edge', 'journal', 'object_key_bucket', 'request_receipt'):
            count = connection.execute(psycopg.sql.SQL('SELECT count(*) FROM truss.{}').format(
                psycopg.sql.Identifier(table))).fetchone()[0]
            self.assertEqual(count, 0, table)

    def test_repeated_owners_of_one_exact_document_succeed(self):
        connection, host, assembly, tx = self.ready(document_ids=('adoc',))
        operations = (self.create('one', alias='one', record='A'), self.create('two', alias='two', record='B'),
                      self.create('three', alias='three', record='A'))
        result = self.raw_apply(connection, assembly, tx, operations, self.original_documents())
        self.assertEqual(result['outcome'], 'success', result)
        self.assertEqual(len(result['semantic']['results']), 3)
        self.assertEqual(tuple(item['alias'] for item in result['semantic']['results']), ('one', 'two', 'three'))
        host.detach()
        connection.commit()
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(), (3,))

    def test_each_authorized_document_source_is_verified(self):
        connection, host, assembly, tx = self.ready(document_ids=('zdoc', 'adoc'))
        self.enable_second_document()
        operations = (self.create('adoc', alias='adoc', document='adoc'),
                      self.create('zdoc', alias='zdoc', document='zdoc'))
        documents = self.original_documents()

        valid = self.raw_apply(connection, assembly, tx, operations, documents)
        self.assertEqual(valid['outcome'], 'success', valid)
        self.assertEqual(len(valid['semantic']['results']), 2)
        host.detach()
        connection.commit()

        connection, host, assembly, tx = self.consumer()
        altered = [dict(document) for document in documents]
        target = next(document for document in altered if document['documentId'] == 'zdoc')
        target['sourceText'] += '\n'
        refused = self.raw_apply(connection, assembly, tx,
                                 (self.create('later-a', alias='later-a', document='adoc'),
                                  self.create('later-z', alias='later-z', document='zdoc')),
                                 altered)
        self.assertEqual(refused['outcome'], 'failed', refused)
        host.detach()
        connection.commit()
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(), (2,))

    def test_missing_duplicate_and_mismatched_sources_refuse_without_effects(self):
        connection, host, _, _ = self.ready(document_ids=('zdoc', 'adoc'))
        host.detach()
        connection.rollback()
        self.enable_second_document()
        operations = (self.create('first', alias='first', document='adoc'),
                      self.create('second', alias='second', document='zdoc'))
        documents = self.original_documents()
        cases = (
            ('missing', [document for document in documents if document['documentId'] != 'zdoc'],
             psycopg.errors.NoDataFound),
            ('duplicate', documents + [dict(next(document for document in documents
                                                  if document['documentId'] == 'adoc'))],
             psycopg.errors.TooManyRows),
            ('mismatch', [dict(document, sourceText=document['sourceText'] + '\n')
                          if document['documentId'] == 'zdoc' else dict(document)
                          for document in documents], None),
        )
        for label, candidate, expected_error in cases:
            with self.subTest(label=label):
                connection, host, assembly, tx = self.consumer()
                connection.execute('CREATE TEMP TABLE caller_work(value text); INSERT INTO caller_work VALUES (\'kept\')')
                connection.execute('SAVEPOINT source_case')
                try:
                    if expected_error is None:
                        result = self.raw_apply(connection, assembly, tx, operations, candidate)
                        self.assertEqual(result['outcome'], 'failed', result)
                    else:
                        with self.assertRaises(expected_error):
                            self.raw_apply(connection, assembly, tx, operations, candidate)
                finally:
                    connection.execute('ROLLBACK TO SAVEPOINT source_case')
                    connection.execute('RELEASE SAVEPOINT source_case')
                self.assertEqual(connection.execute('TABLE caller_work').fetchall(), [('kept',)])
                host.detach()
                connection.commit()
                self.assert_no_group_effects(self.admin)

    def test_source_verification_memo_does_not_cross_apply_calls(self):
        connection, host, assembly, tx = self.ready(document_ids=('adoc',))
        connection.execute('CREATE TEMP TABLE caller_work(value text); INSERT INTO caller_work VALUES (\'kept\')')
        original = self.original_documents()
        first = self.raw_apply(connection, assembly, tx, (self.create('first', alias='first'),), original)
        self.assertEqual(first['outcome'], 'success', first)

        wrong = [dict(document, sourceText=document['sourceText'] + '\n') for document in original]
        second = self.raw_apply(connection, assembly, tx, (self.create('second', alias='second'),), wrong)
        self.assertEqual(second['outcome'], 'failed', second)
        self.assertEqual(connection.execute('TABLE caller_work').fetchall(), [('kept',)])
        host.detach()
        connection.commit()
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(), (1,))
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.journal').fetchone(), (1,))
