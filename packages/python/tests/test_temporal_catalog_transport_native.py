# SPDX-License-Identifier: MIT OR Apache-2.0
"""Native acceptance transport and immutable temporal-family regressions."""
from dataclasses import replace
from hashlib import sha256
import base64
import json
import os
import psycopg
from truss import CatalogDocument, ObjectFound, Ok
from truss.contracts import TextValue, MapValue, LocalTimestampValue
from truss.groups import AuthoredValue, GroupSuccess, RequestNone
from truss._catalog_source_reference import DATE10_PROFILE, TEMPORAL_PROFILE
from truss._catalog_report_semantics import canonical_numeric_free, compose_original_catalog_report_semantics
from truss._catalog_support import evaluate_catalog_support
import test_local_timestamp_query_native as carrier_tests


class TemporalCatalogTransportTests(carrier_tests.LocalTimestampQueryTests):
    # Reuse the public native fixture and preparation helpers, without rerunning
    # the carrier/parser cases as part of this narrowly selected module.
    for _name in tuple(n for n in dir(carrier_tests.LocalTimestampQueryTests) if n.startswith('test_')):
        locals()[_name] = None

    def _grant_registrar(self):
        self.admin.execute(psycopg.sql.SQL('GRANT {} TO consumer WITH SET FALSE').format(
            psycopg.sql.Identifier(self.installation.registrar_role)))

    @staticmethod
    def _property_id(view, authored_identity):
        matches = [entry.reference.property_id for entry in view.definitions
            if entry.reference.kind == 'property'
            and entry.reference.owner.document_id == 'adoc'
            and entry.reference.owner.module_id == 'm'
            and entry.reference.authored_identity == authored_identity]
        if len(matches) != 1:
            raise AssertionError('Unique public catalog property identity required')
        return matches[0]

    def test_temporal_replay_preserves_original_preparation_and_report_bytes(self):
        c, host, assembly, tx = self.ready()
        accepted = self.registered
        original = (self.prepared.input_bytes, self.prepared.declarations_bytes,
                    self.prepared.archive_documents_bytes)
        support = evaluate_catalog_support(self.prepared)
        semantic = compose_original_catalog_report_semantics(self.prepared, support)
        retained_source = {key: semantic[key] for key in ('sourceFormat', 'umf', 'documentValidations', 'ownerAccessProfile')}
        expected_source = json.dumps(retained_source, ensure_ascii=True, separators=(',', ':'), allow_nan=False).encode('utf8')
        retained = self.admin.execute("""SELECT r.input_bytes,r.document_bytes,r.declaration_bytes,r.source_bytes,
            r.revision,ar.report_bytes,r.report_sha256
            FROM truss.catalog_registration_request r
            JOIN truss.catalog_acceptance_report ar ON ar.rev=r.revision
            WHERE r.request_key='temporal-model'""").fetchone()
        self.assertIsNotNone(retained)
        self.assertEqual(retained[:4], (self.prepared.input_bytes, self.prepared.archive_documents_bytes,
                                        self.prepared.declarations_bytes, expected_source))
        self.assertEqual(json.loads(retained[3]), retained_source)
        self.assertEqual(retained[5], accepted.report_bytes)
        self.assertEqual(bytes(retained[6]), sha256(accepted.report_bytes).digest())
        self._grant_registrar()
        replay = assembly.accept_in_transaction(tx, self.prepared, request_key='temporal-model')
        self.assertIsInstance(replay, Ok, repr(replay) + ' ' + str(host._custody.last_attempt.error))
        self.assertTrue(replay.value.replayed)
        self.assertEqual(replay.value.report_bytes, accepted.report_bytes)
        self.assertEqual((self.prepared.input_bytes, self.prepared.declarations_bytes,
                          self.prepared.archive_documents_bytes), original)
        host.detach(); c.commit()
        retained_after = self.admin.execute("""SELECT r.input_bytes,r.document_bytes,r.declaration_bytes,r.source_bytes,
            r.revision,ar.report_bytes,r.report_sha256
            FROM truss.catalog_registration_request r
            JOIN truss.catalog_acceptance_report ar ON ar.rev=r.revision
            WHERE r.request_key='temporal-model'""").fetchone()
        self.assertEqual(retained_after, retained)
        self.assertEqual(self.admin.execute('SELECT rev FROM truss.schema_head').fetchone(), (1,))

    def test_legacy_timestamp_family_refuses_temporal_reinterpretation_atomically(self):
        c, host, assembly, tx = self.ready(support_profile=DATE10_PROFILE)
        self._grant_registrar()
        baseline_view = assembly.catalog_view_in_transaction(tx, assembly.catalog_view_request())
        self.assertIsInstance(baseline_view, Ok, repr(baseline_view))
        baseline_view = baseline_view.value.view
        context = assembly.group_context_in_transaction(tx).value
        original = '2024-01-04T12:00:00.1234567-00:00'
        operation = self.create(label='legacy-timestamp', alias='legacy-timestamp')
        operation = replace(operation, values=operation.values + (
            AuthoredValue(name='A-at', value=TextValue(kind='timestamp', text='2024-01-04T12:00:00.123456Z')),
            AuthoredValue(name='A-local', value=TextValue(kind='timestamp', text=original))))
        applied = assembly.apply_in_transaction(tx, context.input((operation,), MapValue(entries=())),
            RequestNone(), documents=self.documents, bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE', 'bun'))
        self.assertIsInstance(applied, Ok, repr(applied))
        self.assertIsInstance(applied.value, GroupSuccess, repr(applied) + ' ' + str(host._custody.last_attempt.error))
        object_id = int(applied.value.response.semantic.results[0].identity.id)
        host.detach(); c.commit()
        c, host, assembly, tx = self.consumer()
        before_read = assembly.get_object_in_transaction(tx, document_id='adoc', module_id='m', record_id='A', object_id=object_id)
        self.assertIsInstance(before_read.value, ObjectFound, repr(before_read))
        self.assertEqual(dict(before_read.value.object.values)['A-local'], TextValue(kind='timestamp', text=original))
        local_property_id = self._property_id(baseline_view, 'A-local')
        stored_before = self.admin.execute("SELECT props->%s FROM truss.object WHERE id=%s", (local_property_id, object_id)).fetchone()[0]
        self.assertEqual(stored_before, {'kind': 'timestamp', 'text': original})
        source = json.loads(self.documents[0].content)
        candidate = CatalogDocument('adoc', 'r2', json.dumps(source, ensure_ascii=False).encode())
        temporal = assembly.prepare_catalog((candidate,), source_version='0.10.0',
            support_profile=TEMPORAL_PROFILE, bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE', 'bun'))
        denied = assembly.accept_in_transaction(tx, temporal, request_key='temporal-reinterpret')
        self.assertNotIsInstance(denied, Ok, repr(denied))
        error = host._custody.last_attempt.error
        self.assertEqual(getattr(error, 'sql_state', getattr(error, 'sqlstate', None)), '0A000', repr(error))
        after_view = assembly.catalog_view_in_transaction(tx, assembly.catalog_view_request())
        self.assertIsInstance(after_view, Ok, repr(after_view))
        self.assertEqual(after_view.value.view.original_bytes, baseline_view.original_bytes)
        after_value = self.admin.execute("SELECT props->%s FROM truss.object WHERE id=%s", (local_property_id, object_id)).fetchone()[0]
        self.assertEqual(after_value, stored_before)
        self.assertEqual(c.execute('SELECT 42').fetchone(), (42,))
        after_read = assembly.get_object_in_transaction(tx, document_id='adoc', module_id='m', record_id='A', object_id=object_id)
        self.assertIsInstance(after_read.value, ObjectFound, repr(after_read))
        self.assertEqual(dict(after_read.value.object.values)['A-local'], TextValue(kind='timestamp', text=original))
        renamed_source = json.loads(self.documents[0].content)
        next(e for e in renamed_source['modules'][0]['elements'] if e.get('id') == 'A-local')['name'] = 'A-local-renamed'
        renamed = assembly.prepare_catalog((CatalogDocument('adoc', 'r2', json.dumps(renamed_source, ensure_ascii=False).encode()),),
            source_version='0.10.0', support_profile=TEMPORAL_PROFILE,
            bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE', 'bun'))
        renamed_denied = assembly.accept_in_transaction(tx, renamed, request_key='temporal-reinterpret-renamed')
        self.assertNotIsInstance(renamed_denied, Ok, repr(renamed_denied))
        renamed_error = host._custody.last_attempt.error
        self.assertEqual(getattr(renamed_error, 'sql_state', getattr(renamed_error, 'sqlstate', None)), '0A000', repr(renamed_error))
        renamed_view = assembly.catalog_view_in_transaction(tx, assembly.catalog_view_request())
        self.assertIsInstance(renamed_view, Ok, repr(renamed_view))
        self.assertEqual(renamed_view.value.view.original_bytes, baseline_view.original_bytes)
        self.assertEqual(self.admin.execute("SELECT props->%s FROM truss.object WHERE id=%s", (local_property_id, object_id)).fetchone()[0], stored_before)
        self.assertEqual(c.execute('SELECT 42').fetchone(), (42,))
        after_rename_read = assembly.get_object_in_transaction(tx, document_id='adoc', module_id='m', record_id='A', object_id=object_id)
        self.assertIsInstance(after_rename_read.value, ObjectFound, repr(after_rename_read))
        self.assertEqual(dict(after_rename_read.value.object.values)['A-local'], TextValue(kind='timestamp', text=original))
        host.detach(); c.rollback()

    def test_legacy_name_only_rename_keeps_timestamp_family(self):
        c, host, assembly, tx = self.ready(support_profile=DATE10_PROFILE)
        self._grant_registrar()
        baseline_view = assembly.catalog_view_in_transaction(tx, assembly.catalog_view_request())
        self.assertIsInstance(baseline_view, Ok, repr(baseline_view))
        local_property_id = self._property_id(baseline_view.value.view, 'A-local')
        source = json.loads(self.documents[0].content)
        field = next(e for e in source['modules'][0]['elements'] if e.get('id') == 'A-local')
        field['name'] = 'A-local-renamed'
        candidate = CatalogDocument('adoc', 'r2', json.dumps(source, ensure_ascii=False).encode())
        renamed = assembly.prepare_catalog((candidate,), source_version='0.10.0',
            support_profile=DATE10_PROFILE, bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE', 'bun'))
        result = assembly.accept_in_transaction(tx, renamed, request_key='legacy-name-only-rename')
        self.assertIsInstance(result, Ok, repr(result) + ' ' + str(host._custody.last_attempt.error))
        self.assertEqual(result.value.revision, 2)
        current_view = assembly.catalog_view_in_transaction(tx, assembly.catalog_view_request())
        self.assertIsInstance(current_view, Ok, repr(current_view))
        current_property_id = self._property_id(current_view.value.view, 'A-local')
        self.assertEqual(current_property_id, local_property_id)
        public_property = next(entry for entry in current_view.value.view.definitions
            if entry.reference.kind == 'property' and entry.reference.property_id == local_property_id)
        self.assertEqual(json.loads(base64.b64decode(public_property.definition.bytes_base64))['scalarType'], 'timestamp')
        accepted = assembly.accepted_document_in_transaction(tx, document_id='adoc')
        self.assertIsInstance(accepted, Ok, repr(accepted))
        self.assertEqual(accepted.value.content, candidate.content)
        host.detach(); c.rollback()

    def test_temporal_support_cannot_be_paired_with_downgraded_summary(self):
        c, host, assembly, tx = self.ready()
        self._grant_registrar()
        support = evaluate_catalog_support(self.prepared)
        source = compose_original_catalog_report_semantics(self.prepared, support)
        self.assertEqual(source['sourceFormat'], 'truss-registration-summary/2.1')
        downgraded = dict(source, sourceFormat='truss-registration-summary/2.0')
        before = self.admin.execute('SELECT (SELECT rev FROM truss.schema_head), (SELECT count(*) FROM truss.schema_doc), (SELECT count(*) FROM truss.catalog_registration_request), (SELECT count(*) FROM truss.journal)').fetchone()
        with self.assertRaises(psycopg.Error) as raised:
            with c.transaction():
                c.execute('SELECT * FROM truss.person_catalog_accept_with_keys(%s,%s,%s,%s,%s,%s,%s,%s)',
                    (self.prepared.input_bytes, self.prepared.archive_documents_bytes,
                     self.prepared.declarations_bytes, canonical_numeric_free(downgraded),
                     b'{}', 'downgraded-temporal-summary', None, False)).fetchall()
        self.assertEqual(raised.exception.sqlstate, '22023', str(raised.exception))
        self.assertEqual(self.admin.execute('SELECT (SELECT rev FROM truss.schema_head), (SELECT count(*) FROM truss.schema_doc), (SELECT count(*) FROM truss.catalog_registration_request), (SELECT count(*) FROM truss.journal)').fetchone(), before)
        host.detach(); c.rollback()

    def test_legacy_support_cannot_be_paired_with_temporal_summary(self):
        c, host, assembly, tx = self.ready(support_profile=DATE10_PROFILE)
        legacy_support = evaluate_catalog_support(self.prepared)
        legacy_semantic = compose_original_catalog_report_semantics(self.prepared, legacy_support)
        self.assertEqual(legacy_semantic['sourceFormat'], 'truss-registration-summary/2.0')
        source = json.loads(self.documents[0].content)
        temporal_prepared = assembly.prepare_catalog((CatalogDocument('adoc', 'r2', json.dumps(source).encode()),),
            source_version='0.10.0', support_profile=TEMPORAL_PROFILE,
            bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE', 'bun'))
        temporal_semantic = compose_original_catalog_report_semantics(
            temporal_prepared, evaluate_catalog_support(temporal_prepared))
        self.assertEqual(temporal_semantic['sourceFormat'], 'truss-registration-summary/2.1')
        self._grant_registrar()
        before = self.admin.execute('SELECT (SELECT rev FROM truss.schema_head), (SELECT count(*) FROM truss.schema_doc), (SELECT count(*) FROM truss.catalog_registration_request), (SELECT count(*) FROM truss.journal)').fetchone()
        with self.assertRaises(psycopg.Error) as raised:
            with c.transaction():
                c.execute('SELECT * FROM truss.person_catalog_accept_with_keys(%s,%s,%s,%s,%s,%s,%s,%s)',
                    (self.prepared.input_bytes, self.prepared.archive_documents_bytes, b'',
                     canonical_numeric_free(temporal_semantic), b'{}',
                     'temporal-summary-on-legacy-support', None, False)).fetchall()
        self.assertEqual(raised.exception.sqlstate, '22023', str(raised.exception))
        self.assertEqual(self.admin.execute('SELECT (SELECT rev FROM truss.schema_head), (SELECT count(*) FROM truss.schema_doc), (SELECT count(*) FROM truss.catalog_registration_request), (SELECT count(*) FROM truss.journal)').fetchone(), before)
        host.detach(); c.rollback()

    def test_public_accept_atomically_refuses_stripped_temporal_owner_declarations(self):
        c, host, assembly, tx = self.ready()
        context = assembly.group_context_in_transaction(tx).value
        operation = self.create_temporal('public-negative-baseline',
            '2024-02-03T04:05:06.123456Z',
            LocalTimestampValue(text='2024-02-03T04:05:06.123456'),
            TextValue(kind='date', text='2024-02-03'))
        created = assembly.apply_in_transaction(tx, context.input((operation,), MapValue(entries=())),
            RequestNone(), documents=self.documents,
            bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE', 'bun'))
        self.assertIsInstance(created, Ok, repr(created))
        self.assertIsInstance(created.value, GroupSuccess, repr(created) + ' ' + str(host._custody.last_attempt.error))
        object_id = int(created.value.response.semantic.results[0].identity.id)
        host.detach(); c.commit()

        c, host, assembly, tx = self.consumer()
        self._grant_registrar()
        semantic = compose_original_catalog_report_semantics(
            self.prepared, evaluate_catalog_support(self.prepared))
        self.assertEqual(semantic['sourceFormat'], 'truss-registration-summary/2.1')
        source_packet = {key: semantic[key] for key in
            ('sourceFormat', 'umf', 'documentValidations', 'ownerAccessProfile')}
        source_bytes = canonical_numeric_free(source_packet)
        original_declarations = json.loads(self.prepared.declarations_bytes)

        def accept_packet(declarations_bytes, request_key):
            return c.execute('''SELECT * FROM truss.person_catalog_accept_with_keys(
                %s,%s,%s,%s,%s,%s,NULL,false,-1,%s)''',
                (self.prepared.input_bytes, self.prepared.archive_documents_bytes,
                 declarations_bytes, source_bytes, b'{}', request_key, b'[]')).fetchall()

        # This exact owner-issued packet must remain admissible before malformed
        # variants are attempted, so each negative exercises the intended gate.
        positive = accept_packet(self.prepared.declarations_bytes, 'public-valid-original-control')
        self.assertEqual(len(positive), 1)
        self.assertEqual(positive[0][0], '1')
        self.assertIsNone(positive[0][6], repr(positive[0]))
        host.detach(); c.commit()

        c, host, assembly, tx = self.consumer()
        baseline_view = assembly.catalog_view_in_transaction(tx, assembly.catalog_view_request())
        self.assertIsInstance(baseline_view, Ok, repr(baseline_view))
        baseline_view_bytes = baseline_view.value.view.original_bytes
        baseline_object = assembly.get_object_in_transaction(tx, document_id='adoc', module_id='m',
            record_id='A', object_id=object_id)
        self.assertIsInstance(baseline_object.value, ObjectFound, repr(baseline_object))
        baseline_values = dict(baseline_object.value.object.values)
        self.assertEqual(baseline_values['A-local'], LocalTimestampValue(text='2024-02-03T04:05:06.123456'))
        local_property_id = self._property_id(baseline_view.value.view, 'A-local')
        baseline_state = self.admin.execute('''SELECT
            (SELECT rev FROM truss.schema_head),
            (SELECT count(*) FROM truss.schema_doc),
            (SELECT count(*) FROM truss.catalog_registration_request),
            (SELECT count(*) FROM truss.catalog_acceptance_report),
            (SELECT count(*) FROM truss.journal),
            (SELECT props->%s FROM truss.object WHERE id=%s)''',
            (local_property_id, object_id)).fetchone()

        def mutated(change):
            value = json.loads(json.dumps(original_declarations))
            # Preparation carries a one-entry document array whose document
            # identity is bound through its staged Record entries.
            document = value[0]
            change(document)
            return json.dumps(value, ensure_ascii=True, separators=(',', ':'), allow_nan=False).encode('utf8')

        def local_record(document):
            return next(record for record in document['records']
                if record['moduleId'] == 'm' and record['elementId'] == 'A')

        def local_member(record):
            return next(field for field in record['fields']
                if field['reference'] == {'module': 'm', 'element': 'A-local'})

        def owner_local_record(document):
            return next(record for record in document['accessAdmission']['records']
                if record['ref'] == {'module': 'm', 'element': 'A'})

        def remove_owner_local_field(document):
            owner_record = owner_local_record(document)
            owner_record['fields'] = [field for field in owner_record['fields']
                if field['ref'] != {'module': 'm', 'element': 'A-local'}]

        cases = (
            ('descriptor-removed', mutated(lambda document: local_member(local_record(document)).pop('nativeDescriptor'))),
            ('declaration-native-field-removed', mutated(lambda document: local_record(document)['fields'].remove(local_member(local_record(document))))),
            ('declaration-access-admission-field-removed', mutated(remove_owner_local_field)),
            ('declaration-record-removed', mutated(lambda document: document['records'].remove(local_record(document)))),
            ('empty-records', mutated(lambda document: document.__setitem__('records', []))),
            ('empty-declarations', b''),
        )
        for index, (label, declarations_bytes) in enumerate(cases):
            with self.subTest(variant=label):
                returned = None
                caught = None
                try:
                    with c.transaction():
                        returned = accept_packet(declarations_bytes, 'public-invalid-owner-' + str(index))
                except psycopg.Error as error:
                    caught = error
                if caught is not None:
                    self.assertEqual(caught.sqlstate, '22023', (label, str(caught)))
                else:
                    # A structurally valid but lossy declaration may return
                    # the established typed property-family refusal instead
                    # of raising. It must not publish a revision or report.
                    self.assertEqual(len(returned), 1, (label, returned))
                    row = returned[0]
                    self.assertEqual(row[0], '1', (label, row))
                    self.assertIsNone(row[1], (label, row))
                    self.assertIsNone(row[2], (label, row))
                    self.assertFalse(row[3], (label, row))
                    self.assertFalse(row[4], (label, row))
                    violations = json.loads(bytes(row[6]))
                    self.assertEqual(len(violations), 1, (label, violations))
                    self.assertEqual(violations[0].get('rule'), 'property.scalar_type', (label, violations))
                    self.assertEqual(violations[0].get('fieldId'), 'A-local', (label, violations))
                self.assertEqual(c.execute('SELECT 42').fetchone(), (42,))
                current_view = assembly.catalog_view_in_transaction(tx, assembly.catalog_view_request())
                self.assertIsInstance(current_view, Ok, (label, repr(current_view)))
                self.assertEqual(current_view.value.view.original_bytes, baseline_view_bytes, label)
                current_object = assembly.get_object_in_transaction(tx, document_id='adoc', module_id='m',
                    record_id='A', object_id=object_id)
                self.assertIsInstance(current_object.value, ObjectFound, (label, repr(current_object)))
                self.assertEqual(dict(current_object.value.object.values), baseline_values, label)

        host.detach(); c.commit()
        persisted_state = self.admin.execute('''SELECT
            (SELECT rev FROM truss.schema_head),
            (SELECT count(*) FROM truss.schema_doc),
            (SELECT count(*) FROM truss.catalog_registration_request),
            (SELECT count(*) FROM truss.catalog_acceptance_report),
            (SELECT count(*) FROM truss.journal),
            (SELECT props->%s FROM truss.object WHERE id=%s)''',
            (local_property_id, object_id)).fetchone()
        self.assertEqual(persisted_state, baseline_state)


if __name__ == '__main__':
    import unittest
    unittest.main()
