# SPDX-License-Identifier: MIT OR Apache-2.0
"""A separate module-audit role discloses complete mutation metadata only."""
import json
from datetime import timedelta
import psycopg

from truss import Ok
from truss.load_audit import (MutationGroupAuditListingEnd, LoadAuditUnavailable,
                              MutationGroupAuditPage)
from truss.groups import UpdateObject, StoredObjectReference, AuthoredValue
from truss.contracts import MapValue, MapEntry, TextValue
import test_object_mutations_native as mutation_tests


class MutationGroupAuditNativeTests(mutation_tests.ObjectMutationTests):
    for _name in tuple(n for n in dir(mutation_tests.ObjectMutationTests) if n.startswith('test_')):
        locals()[_name] = None

    def test_group_audit_requires_separate_role_and_preserves_noop_metadata(self):
        connection, host, assembly, tx = self.ready()
        action = MapValue(entries=(MapEntry(key='x-action', value=TextValue(kind='string', text='test-action')),
                                    MapEntry(key='x-secret', value=TextValue(kind='string', text='never-disclose'))))
        context = assembly.group_context_in_transaction(tx).value
        input = context.input((self.create(label='audit-secret', value='payload-secret'),), action)
        applied = assembly.apply_in_transaction(tx, input, context.request('audit-create'),
            documents=self.documents, bun_executable='/opt/homebrew/bin/bun')
        self.assertIsInstance(applied, Ok, repr(applied))
        identity = applied.value.response.semantic.results[0].identity
        create_writer_xid = connection.execute('SELECT pg_current_xact_id()::text').fetchone()[0]
        host.detach(); connection.commit()
        # Read the private native attempt inventory only from the admin test
        # connection after commit; the consumer facade has no table privilege.
        create_attempt = self.admin.execute(
            'SELECT id::text FROM truss.runtime_object_attempt WHERE writer_xid=%s::xid8 AND complete ORDER BY id DESC LIMIT 1',
            (create_writer_xid,)).fetchone()[0]
        native_plan = self.admin.execute('SELECT truss.runtime_owned_plan(%s::uuid,0)', (create_attempt,)).fetchone()[0]
        if isinstance(native_plan, str): native_plan = json.loads(native_plan)
        created_state = next(state for state in native_plan['afterNodes'].values()
            if state['identity']['owner'] == {'documentId': 'adoc', 'moduleId': 'm'})
        created_image = created_state['image']
        key_number, key_pin, key_properties = self.admin.execute(
            'SELECT k.key_num,d.definition_pin,k.prop_ids FROM truss.key_def k '
            'JOIN truss.type_def t ON t.type_id=k.type_id '
            'JOIN truss.runtime_definition_source d ON d.rev=k.definition_rev AND d.ord=k.definition_doc_ord '
            'AND d.doc_id=k.definition_document_id AND d.module_id=t.module AND d.element_id=t.element '
            'AND d.kind=\'key\' AND d.key_id=k.key_id '
            'WHERE k.type_id=%s AND k.key_id=\'z-alt\' AND k.retired_rev IS NULL',
            (int(created_state['identity']['typeId']),)).fetchone()
        entity_key = {'documentId': 'adoc', 'moduleId': 'm', 'typeId': created_state['identity']['typeId'],
            'keyNumber': str(key_number), 'definitionPin': key_pin,
            'values': [created_image['props'][str(prop_id)] for prop_id in key_properties]}
        wrong_key = dict(entity_key, values=[dict(entity_key['values'][0], text='missing-key')])

        connection, host, assembly, tx = self.consumer()
        # Same values produce a retained successful no-op operation.
        noop = UpdateObject(target=StoredObjectReference(identity=identity),
            set=(AuthoredValue(name='A-label', value=TextValue(kind='string', text='audit-secret')),
                 AuthoredValue(name='A-value', value=TextValue(kind='string', text='payload-secret'))), unset=())
        noop_context = assembly.group_context_in_transaction(tx).value
        applied = self.apply(assembly, tx, noop_context.input((noop,), action), noop_context.request('audit-noop'))
        noop_writer_xid = connection.execute('SELECT pg_current_xact_id()::text').fetchone()[0]
        host.detach(); connection.commit()
        noop_attempt = self.admin.execute(
            'SELECT id::text FROM truss.runtime_object_attempt WHERE writer_xid=%s::xid8 AND complete ORDER BY id DESC LIMIT 1',
            (noop_writer_xid,)).fetchone()[0]

        connection, host, assembly, tx = self.consumer()
        mixed_context = assembly.group_context_in_transaction(tx).value
        unchanged = UpdateObject(target=StoredObjectReference(identity=identity),
            set=(AuthoredValue(name='A-label', value=TextValue(kind='string', text='audit-secret')),
                 AuthoredValue(name='A-value', value=TextValue(kind='string', text='payload-secret'))), unset=())
        changed = UpdateObject(target=StoredObjectReference(identity=identity),
            set=(AuthoredValue(name='A-label', value=TextValue(kind='string', text='audit-changed')),), unset=())
        self.apply(assembly, tx, mixed_context.input((unchanged, changed), action), mixed_context.request('audit-mixed'))
        mixed_writer_xid = connection.execute('SELECT pg_current_xact_id()::text').fetchone()[0]
        host.detach(); connection.commit()
        mixed_attempt = self.admin.execute(
            'SELECT id::text FROM truss.runtime_object_attempt WHERE writer_xid=%s::xid8 AND complete ORDER BY id DESC LIMIT 1',
            (mixed_writer_xid,)).fetchone()[0]
        no_op_at, changed_at = self.admin.execute(
            'SELECT a.audit_observed_at, min((j.value->>\'at\')::timestamptz) '
            'FROM truss.runtime_object_attempt a JOIN truss.runtime_object_transition t ON t.attempt_id=a.id '
            'CROSS JOIN LATERAL jsonb_array_elements(t.journal) j(value) WHERE a.id=%s::uuid GROUP BY a.audit_observed_at',
            (mixed_attempt,)).fetchone()

        auditor = 'group_audit_reader'
        self.admin.execute(psycopg.sql.SQL('CREATE ROLE {} NOLOGIN NOINHERIT').format(psycopg.sql.Identifier(auditor)))
        connection, host, assembly, tx = self.consumer()
        try:
            # Give the caller only the public page selector to prove the native
            # membership gate refuses a writer without a distinct audit grant.
            self.admin.execute('GRANT EXECUTE ON FUNCTION truss.page_mutation_group_audit(jsonb,int,bytea,text,text) TO consumer')
            scope = {'documentId': 'adoc', 'moduleId': 'm'}
            denied = assembly.page_mutation_group_audit_in_transaction(tx, filters={**scope, 'attemptId': create_attempt})
            self.assertIsInstance(denied, Ok)
            self.assertIsInstance(denied.value, LoadAuditUnavailable)
            self.assertEqual(denied.value.reason, 'unauthorized')
            denied_empty = assembly.page_mutation_group_audit_in_transaction(tx, filters=scope)
            self.assertIsInstance(denied_empty, Ok)
            self.assertIsInstance(denied_empty.value, LoadAuditUnavailable)
            self.assertEqual(denied_empty.value.reason, 'unauthorized')
            denied_existing_key = assembly.page_mutation_group_audit_in_transaction(tx,
                filters={**scope, 'attemptId': create_attempt, 'entityKey': entity_key})
            denied_missing_key = assembly.page_mutation_group_audit_in_transaction(tx,
                filters={**scope, 'attemptId': create_attempt, 'entityKey': wrong_key})
            self.assertEqual(denied_existing_key.value.reason, 'unauthorized')
            self.assertEqual(denied_missing_key.value.reason, 'unauthorized')
            self.admin.execute('INSERT INTO truss.runtime_import_audit_access(document_id,module,auditor_oid,granted_by) '
                'SELECT %s,%s,oid,(SELECT oid FROM pg_roles WHERE rolname=session_user) FROM pg_roles WHERE rolname=%s',
                ('adoc', 'm', auditor))
            self.admin.execute(psycopg.sql.SQL('GRANT {} TO consumer WITH INHERIT TRUE, SET FALSE').format(psycopg.sql.Identifier(auditor)))
            page_result = assembly.page_mutation_group_audit_in_transaction(tx,
                filters={**scope, 'attemptId': create_attempt, 'entityKey': entity_key})
            self.assertIsInstance(page_result, Ok, repr(page_result)+" "+str(assembly._host._custody.last_attempt.error))
            page = page_result.value
            self.assertIsInstance(page, MutationGroupAuditPage, repr(page))
            self.assertEqual(page.asserted_action, 'test-action')
            serialized = repr(page)
            self.assertNotIn('audit-secret', serialized)
            self.assertNotIn('payload-secret', serialized)
            self.assertNotIn('never-disclose', serialized)
            continuation = assembly.page_mutation_group_audit_in_transaction(tx,
                filters={**scope, 'attemptId': create_attempt, 'entityKey': entity_key}, cursor=page.next_page_cursor)
            self.assertIsInstance(continuation, Ok, repr(continuation))
            self.assertIsInstance(continuation.value, MutationGroupAuditListingEnd, repr(continuation.value))
            missing_key = assembly.page_mutation_group_audit_in_transaction(tx,
                filters={**scope, 'attemptId': create_attempt, 'entityKey': wrong_key})
            self.assertIsInstance(missing_key, Ok, repr(missing_key))
            self.assertIsInstance(missing_key.value, MutationGroupAuditListingEnd, repr(missing_key.value))
            noop_page = assembly.page_mutation_group_audit_in_transaction(tx, filters={**scope, 'attemptId': noop_attempt})
            self.assertIsInstance(noop_page, Ok, repr(noop_page))
            self.assertIsInstance(noop_page.value, MutationGroupAuditPage, repr(noop_page.value))
            self.assertEqual(noop_page.value.entries[0].operation, 'update_object')
            mixed_page = assembly.page_mutation_group_audit_in_transaction(tx, filters={**scope,
                'attemptId': mixed_attempt,
                'observedAtFrom': no_op_at.isoformat(timespec='microseconds').replace('+00:00', 'Z'),
                'observedAtUntil': changed_at.isoformat(timespec='microseconds').replace('+00:00', 'Z')})
            self.assertIsInstance(mixed_page, Ok, repr(mixed_page))
            self.assertIsInstance(mixed_page.value, MutationGroupAuditPage, repr(mixed_page.value))
            self.assertIn('0', {entry.operation_index for entry in mixed_page.value.entries})

        finally:
            host.detach(); connection.rollback()
            self.admin.execute('REVOKE EXECUTE ON FUNCTION truss.page_mutation_group_audit(jsonb,int,bytea,text,text) FROM consumer')
            self.admin.execute('REVOKE group_audit_reader FROM consumer')
            self.admin.execute('DELETE FROM truss.runtime_import_audit_access WHERE document_id=%s AND module=%s', ('adoc', 'm'))
            self.admin.execute('DROP ROLE group_audit_reader')


if __name__ == '__main__':
    import unittest
    unittest.main()
