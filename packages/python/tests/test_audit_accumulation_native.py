# SPDX-License-Identifier: MIT OR Apache-2.0
"""Public audit controls for the bounded native accumulation implementation."""
from collections import Counter

from truss import Ok, MutationGroupAuditPage, LoadAuditUnavailable
from truss.groups import UpdateObject, AliasObjectReference, AuthoredValue
from truss.contracts import TextValue

import test_audit_disclosure_native as base


class AuditAccumulationNativeTests(base.AuditDisclosureNativeTests):
    # Reuse only the fixture and public helpers. Keep the pre-existing audit
    # suite's cases owned by its original module.
    for _name in tuple(name for name in dir(base.AuditDisclosureNativeTests) if name.startswith('test_')):
        locals()[_name] = None

    def commit_group(self, operations, action):
        connection, host, assembly, tx = self.consumer()
        context = assembly.group_context_in_transaction(tx).value
        applied = assembly.apply_in_transaction(tx,
            context.input(tuple(operations), self.action(action)),
            context.request(action), documents=self.documents)
        self.assertIsInstance(applied, Ok,
            repr(applied) + ' ' + str(host._custody.last_attempt.error))
        self.assertEqual(applied.value.outcome, 'success', repr(applied.value))
        results = applied.value.response.semantic.results
        writer_xid = connection.execute('SELECT pg_current_xact_id()::text').fetchone()[0]
        host.detach()
        connection.commit()
        attempt_id = self.admin.execute(
            'SELECT id::text FROM truss.runtime_object_attempt '
            'WHERE writer_xid=%s::xid8 AND complete ORDER BY id DESC LIMIT 1',
            (writer_xid,)).fetchone()[0]
        return results, attempt_id

    @staticmethod
    def action(value):
        from truss.contracts import MapEntry, MapValue
        return MapValue(entries=(MapEntry(key='x-action',
            value=TextValue(kind='string', text=value)),))

    def test_mixed_group_preserves_event_order_indexes_and_noop_operation(self):
        self.setup_scopes()
        alias = 'accumulate-create-update-noop'
        label = 'changed-label'
        value = 'changed-value'
        operations = (
            self.create(label='initial-label', value='initial-value', alias=alias),
            UpdateObject(target=AliasObjectReference(alias=alias), set=(
                AuthoredValue(name='A-label', value=TextValue(kind='string', text=label)),
                AuthoredValue(name='A-value', value=TextValue(kind='string', text=value))), unset=()),
            UpdateObject(target=AliasObjectReference(alias=alias), set=(
                AuthoredValue(name='A-label', value=TextValue(kind='string', text=label)),
                AuthoredValue(name='A-value', value=TextValue(kind='string', text=value))), unset=()),
        )
        results, attempt_id = self.commit_group(operations, 'array-accumulation-order')
        self.assertEqual([result.outcome for result in results], ['created', 'changed', 'unchanged'])

        connection, host, assembly, tx = self.audit_person()
        page = self.page(assembly, tx,
            {'documentId': 'adoc', 'moduleId': 'm', 'attemptId': attempt_id})
        self.assertIsInstance(page, MutationGroupAuditPage, repr(page))
        self.assertEqual(int(page.operation_count), 3)
        # The create retains one event; the changed update retains two
        # property events plus its metadata event; the successful no-op has
        # one retained operation entry despite having no journal row.
        self.assertEqual(int(page.event_count), 5)
        self.assertEqual([(entry.operation_index, entry.operation) for entry in page.entries], [
            ('0', 'create'),
            ('1', 'property'), ('1', 'property'), ('1', 'metadata'),
            ('2', 'update_object'),
        ])
        self.assertEqual(Counter(entry.operation_index for entry in page.entries),
                         Counter({'0': 1, '1': 3, '2': 1}))
        # Owner-shaped values occur repeatedly in plans and retained events;
        # the public owner census is the exact distinct owner set.
        self.assertEqual(page.owner_scopes, ({'documentId': 'adoc', 'moduleId': 'm'},))
        self.assertNotIn(alias, repr(page))
        host.detach()
        connection.rollback()

    def test_mixed_owner_group_refuses_until_each_owner_grant_and_after_revoke(self):
        self.setup_scopes()
        results, attempt_id = self.commit_group((
            self.create(document='adoc', label='visible-owner-secret', alias='owner-a'),
            self.create(document='zdoc', label='hidden-owner-secret', alias='owner-z'),
        ), 'mixed-owner-accumulation')
        self.assertEqual([result.outcome for result in results], ['created', 'created'])

        connection, host, assembly, tx = self.audit_person()
        filters = {'documentId': 'adoc', 'moduleId': 'm', 'attemptId': attempt_id}
        refused = self.page(assembly, tx, filters)
        self.assertIsInstance(refused, LoadAuditUnavailable, repr(refused))
        self.assertEqual(refused.reason, 'unauthorized')
        self.assertNotIn('visible-owner-secret', repr(refused))
        self.assertNotIn('hidden-owner-secret', repr(refused))
        # The public refusal is contained at its savepoint; the caller's
        # read-only transaction remains usable.
        self.assertEqual(connection.execute('SELECT 42').fetchone(), (42,))

        self.admin.execute('GRANT journal_b TO journal_person WITH INHERIT TRUE, SET FALSE')
        complete = self.page(assembly, tx, filters)
        self.assertIsInstance(complete, MutationGroupAuditPage, repr(complete))
        self.assertEqual(complete.owner_scopes, (
            {'documentId': 'adoc', 'moduleId': 'm'},
            {'documentId': 'zdoc', 'moduleId': 'm'},
        ))
        self.assertNotIn('visible-owner-secret', repr(complete))
        self.assertNotIn('hidden-owner-secret', repr(complete))
        host.detach()
        connection.rollback()

        self.admin.execute('REVOKE journal_b FROM journal_person')
        connection, host, assembly, tx = self.audit_person()
        revoked = self.page(assembly, tx, filters)
        self.assertIsInstance(revoked, LoadAuditUnavailable, repr(revoked))
        self.assertEqual(revoked.reason, 'unauthorized')
        self.assertEqual(connection.execute('SELECT 42').fetchone(), (42,))
        host.detach()
        connection.rollback()


if __name__ == '__main__':
    import unittest
    unittest.main()
