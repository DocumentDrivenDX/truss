# SPDX-License-Identifier: MIT OR Apache-2.0
"""Native read-only observations for all selected group precondition kinds."""
from truss import Ok, CatalogRuntimeConfiguration, adopt_psycopg_host, create_reference_assembly
import psycopg
from truss.contracts import MapValue, TextValue
from truss.groups import (ObjectExists, KeyAbsent, PropertyEquals,
    RelationshipAbsent, RelationshipCount, GroupSuccess)
from truss.preview import GroupConditionPreviewInput, PreviewObserved, PreviewRefused
from truss._preview_runtime import _json_bytes, _wire
from truss.catalog_runtime import _release
import json
import concurrent.futures
import time
import test_group_preconditions_native as precondition_tests


class GroupPreviewNativeTests(precondition_tests.GroupPreconditionTests):
    for _name in tuple(n for n in dir(precondition_tests.GroupPreconditionTests)
                       if n.startswith('test_')):
        locals()[_name] = None

    def test_readonly_preview_observes_all_five_conditions_without_effects(self):
        """@covers US-040-AC1 / US-040-AC2: preview reports an observation only."""
        connection, host, assembly, tx, a, b, pin = self.initialized()
        conditions = (
            ObjectExists(id='exists', reason='target remains present', target=a),
            KeyAbsent(id='key-free', reason='new key remains unallocated',
                type_definition_pin=a.definition_pin, key_id='a-primary',
                values=(TextValue(kind='string', text='new-preview-key'),
                        TextValue(kind='string', text='unused'))),
            PropertyEquals(id='property', reason='original label remains', target=a,
                name='A-label', value=TextValue(kind='string', text='one')),
            RelationshipAbsent(id='relationship-absent', reason='no edge exists',
                relationship_definition_pin=pin, source=a, target=b),
            RelationshipCount(id='relationship-count', reason='no outgoing edges',
                relationship_definition_pin=pin, anchor=a, direction='outgoing', maximum='0'),
        )
        context = assembly.group_context_in_transaction(tx).value
        group_input = context.input((self.create(),), MapValue(entries=()),
                                    preconditions=conditions)
        preview_input = GroupConditionPreviewInput(
            layout_profile=group_input.layout_profile,
            mutation_profile=group_input.mutation_profile,
            value_profile=group_input.value_profile,
            catalog=group_input.catalog,
            preconditions=conditions)
        counts = ('SELECT (SELECT count(*) FROM truss.runtime_object_attempt),'
            '(SELECT count(*) FROM truss.request_receipt),'
            '(SELECT count(*) FROM truss.journal),'
            '(SELECT count(*) FROM truss.object),'
            '(SELECT last_value FROM truss.id_seq)')
        before = self.admin.execute(counts).fetchone()
        connection.execute('CREATE TEMP TABLE preview_sentinel(value text)')
        connection.execute("INSERT INTO preview_sentinel VALUES ('kept')")
        observed = assembly.preview_group_conditions_in_transaction(
            tx, preview_input, documents=self.documents)
        self.assertIsInstance(observed, Ok, repr(observed))
        self.assertIsInstance(observed.value, PreviewObserved, repr(observed.value))
        self.assertEqual(tuple((item.condition_id, item.rule, item.passed)
                               for item in observed.value.conditions),
                         tuple((condition.id, condition.condition, True)
                               for condition in conditions))
        self.assertEqual(observed.value.basis.status, 'observed')
        self.assertTrue(observed.value.basis.snapshot)
        self.assertEqual(connection.execute('SELECT * FROM preview_sentinel').fetchall(), [('kept',)])
        self.assertEqual(connection.execute('SELECT 42').fetchone(), (42,))
        self.assertEqual(self.admin.execute(counts).fetchone(), before)
        host.detach()
        connection.commit()
        self.assertEqual(self.admin.execute(counts).fetchone(), before)

    def test_preview_runs_on_an_adopted_read_only_transaction(self):
        """@covers US-040-AC1 / US-040-AC2: all five predicates work in READ ONLY."""
        connection, host, assembly, tx, a, b, pin = self.initialized()
        conditions = (
            ObjectExists(id='exists-ro', reason='target remains present', target=a),
            KeyAbsent(id='key-free-ro', reason='new key remains unallocated',
                type_definition_pin=a.definition_pin, key_id='a-primary',
                values=(TextValue(kind='string', text='new-preview-key'),
                        TextValue(kind='string', text='unused'))),
            PropertyEquals(id='property-ro', reason='original label remains', target=a,
                name='A-label', value=TextValue(kind='string', text='one')),
            RelationshipAbsent(id='relationship-absent-ro', reason='no edge exists',
                relationship_definition_pin=pin, source=a, target=b),
            RelationshipCount(id='relationship-count-ro', reason='no outgoing edges',
                relationship_definition_pin=pin, anchor=a, direction='outgoing', maximum='0'),
        )
        preview = self._preview_input(assembly, tx, a, conditions)
        host.detach()
        connection.rollback()
        connection.execute('BEGIN READ ONLY')
        host = adopt_psycopg_host(connection, statement_timeout_ms=10000, operation_timeout_ms=30000)
        assembly = create_reference_assembly(CatalogRuntimeConfiguration(), host).value
        tx = host.adopt_transaction(access_mode='read_only').value
        self.assertEqual(connection.execute("SELECT current_setting('transaction_read_only')").fetchone(), ('on',))
        counts = ('SELECT (SELECT count(*) FROM truss.runtime_object_attempt),'
            '(SELECT count(*) FROM truss.request_receipt),'
            '(SELECT count(*) FROM truss.journal),'
            '(SELECT count(*) FROM truss.object),'
            '(SELECT last_value FROM truss.id_seq)')
        before = self.admin.execute(counts).fetchone()
        observed = assembly.preview_group_conditions_in_transaction(tx, preview, documents=self.documents)
        self.assertIsInstance(observed, Ok, repr(observed))
        self.assertIsInstance(observed.value, PreviewObserved, repr(observed.value))
        self.assertEqual(tuple((item.condition_id, item.rule, item.passed)
                               for item in observed.value.conditions),
                         tuple((condition.id, condition.condition, True) for condition in conditions))
        self.assertEqual(connection.execute("SELECT current_setting('transaction_read_only')").fetchone(), ('on',))
        self.assertEqual(self.admin.execute(counts).fetchone(), before)
        host.detach()
        connection.rollback()
        self.assertEqual(self.admin.execute(counts).fetchone(), before)

    def _preview_input(self, assembly, tx, identity, conditions):
        context = assembly.group_context_in_transaction(tx).value
        group_input = context.input((self.create(),), MapValue(entries=()),
                                    preconditions=conditions)
        return GroupConditionPreviewInput(
            layout_profile=group_input.layout_profile,
            mutation_profile=group_input.mutation_profile,
            value_profile=group_input.value_profile,
            catalog=group_input.catalog,
            preconditions=conditions)

    def test_preview_accepts_153_heterogeneous_conditions(self):
        """@covers US-040-AC1 / US-040-AC2: preview preserves the native batch ceiling."""
        connection, host, assembly, tx, a, _b, _pin = self.initialized()
        conditions = tuple(condition for index in range(51) for condition in (
            ObjectExists(id=f'e{index:02d}', reason='r', target=a),
            PropertyEquals(id=f'p{index:02d}', reason='r', target=a,
                name='A-label', value=TextValue(kind='string', text='one')),
            KeyAbsent(id=f'k{index:02d}', reason='r',
                type_definition_pin=a.definition_pin, key_id='a-primary',
                values=(TextValue(kind='string', text='preview-153-free'),
                        TextValue(kind='string', text='unused')))))
        preview = self._preview_input(assembly, tx, a, conditions)
        observed = assembly.preview_group_conditions_in_transaction(
            tx, preview, documents=self.documents)
        self.assertIsInstance(observed, Ok, repr(observed))
        self.assertIsInstance(observed.value, PreviewObserved, repr(observed.value))
        self.assertEqual(len(observed.value.conditions), 153)
        self.assertTrue(all(item.passed for item in observed.value.conditions))
        host.detach(); connection.commit()

    def test_preview_accepts_3072_conditions(self):
        """@covers US-040-AC1: the owned preview ceiling is accepted."""
        connection, host, assembly, tx, a, _b, _pin = self.initialized()
        conditions = tuple(ObjectExists(id=f'c{index:04d}', reason='r', target=a)
                           for index in range(3072))
        preview = self._preview_input(assembly, tx, a, conditions)
        observed = assembly.preview_group_conditions_in_transaction(
            tx, preview, documents=self.documents)
        self.assertIsInstance(observed, Ok, repr(observed))
        self.assertIsInstance(observed.value, PreviewObserved, repr(observed.value))
        self.assertEqual(len(observed.value.conditions), 3072)
        self.assertTrue(all(item.passed for item in observed.value.conditions))
        host.detach(); connection.commit()

    def test_preview_data_uses_one_snapshot_across_concurrent_update(self):
        """@covers US-040-AC1: condition reads share the reported snapshot basis."""
        connection,host,assembly,tx,a,_b,_pin=self.initialized()
        conditions=tuple(PropertyEquals(id=f'snapshot-{index:04d}',reason='old value remains visible',
            target=a,name='A-label',value=TextValue(kind='string',text='one'))
            for index in range(3072))
        preview=self._preview_input(assembly,tx,a,conditions)
        backend_pid=connection.execute('SELECT pg_backend_pid()').fetchone()[0]
        writer_connection,writer_host,writer_assembly,writer_tx=self.consumer()

        def observe():
            try:
                return assembly.preview_group_conditions_in_transaction(
                    tx,preview,documents=self.documents)
            finally:
                host.detach()

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            pending=pool.submit(observe)
            deadline=time.monotonic()+15
            active=False
            while time.monotonic()<deadline and not pending.done():
                active=self.admin.execute(
                    "SELECT EXISTS(SELECT 1 FROM pg_stat_activity WHERE pid=%s "
                    "AND state='active' AND query ILIKE '%%preview_group_conditions%%')",
                    (backend_pid,)).fetchone()[0]
                if active:
                    changed,_,_=self.condition_group(writer_assembly,writer_tx,a,(),
                        'change-during-preview-snapshot')
                    self.assertIsInstance(changed,GroupSuccess,repr(changed))
                    self.assertEqual(dict(self.read(writer_assembly,writer_tx,a).object.values)['A-label'],'new')
                    writer_host.detach();writer_connection.commit()
                    break
                time.sleep(0.002)
            self.assertTrue(active,'native preview completed before the concurrent update began')
            observed=pending.result(timeout=25)

        self.assertIsInstance(observed,Ok,repr(observed))
        self.assertIsInstance(observed.value,PreviewObserved,repr(observed.value))
        self.assertEqual(len(observed.value.conditions),3072)
        self.assertTrue(all(item.passed for item in observed.value.conditions))
        self.assertTrue(observed.value.basis.snapshot)
        connection.rollback()

    def test_preview_refuses_when_reader_is_revoked_during_observation(self):
        """@covers US-040-AC2: a mid-observation reader revocation withholds results."""
        connection,host,assembly,tx,a,_b,_pin=self.initialized()
        before=self.admin.execute('SELECT count(*) FROM truss.runtime_object_attempt').fetchone()
        conditions=tuple(ObjectExists(id=f'revoke-{index:04d}',reason='present',target=a)
                         for index in range(3072))
        preview=self._preview_input(assembly,tx,a,conditions)
        backend_pid=connection.execute('SELECT pg_backend_pid()').fetchone()[0]

        def observe():
            try:
                return assembly.preview_group_conditions_in_transaction(
                    tx,preview,documents=self.documents)
            finally:
                host.detach()

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            pending=pool.submit(observe)
            deadline=time.monotonic()+15
            active=False
            while time.monotonic()<deadline and not pending.done():
                active=self.admin.execute(
                    "SELECT EXISTS(SELECT 1 FROM pg_stat_activity WHERE pid=%s "
                    "AND state='active' AND query ILIKE '%%preview_group_conditions%%')",
                    (backend_pid,)).fetchone()[0]
                if active:
                    self.admin.execute('REVOKE group_reader FROM consumer')
                    self.admin.execute('REVOKE group_writer FROM consumer')
                    break
                time.sleep(0.002)
            self.assertTrue(active,'native preview completed before the revocation race was observed')
            result=pending.result(timeout=25)
        self.assertIsInstance(result,Ok,repr(result))
        self.assertIsInstance(result.value,PreviewRefused,repr(result.value))
        self.assertEqual(result.value.reason,'unauthorized')
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.runtime_object_attempt').fetchone(),before)
        connection.rollback()

    def test_native_preview_3073_refuses_without_effects(self):
        """@covers US-040-AC2: native preview enforces its independent ceiling."""
        connection, host, assembly, tx, a, _b, _pin = self.initialized()
        context = assembly.group_context_in_transaction(tx).value
        group_input = context.input((self.create(),), MapValue(entries=()),
            preconditions=(ObjectExists(id='c0000', reason='r', target=a),))
        preview = GroupConditionPreviewInput(
            layout_profile=group_input.layout_profile,
            mutation_profile=group_input.mutation_profile,
            value_profile=group_input.value_profile,
            catalog=group_input.catalog,
            preconditions=group_input.preconditions)
        raw = _wire(preview)
        raw['preconditions'] = [dict(raw['preconditions'][0], id=f'c{index:04d}')
                                for index in range(3073)]
        original = _json_bytes(raw)
        self.assertLess(len(original), 1_048_576)
        documents = _json_bytes([{'documentId': item.document_id,
                                  'sourceText': item.content.decode('utf8')}
                                 for item in self.documents])
        manifest, digest, _ = _release()
        counts = ('SELECT (SELECT count(*) FROM truss.runtime_object_attempt),'
            '(SELECT count(*) FROM truss.request_receipt),'
            '(SELECT count(*) FROM truss.journal),'
            '(SELECT count(*) FROM truss.object),'
            '(SELECT last_value FROM truss.id_seq)')
        before = self.admin.execute(counts).fetchone()
        connection.execute('SAVEPOINT preview_over_limit')
        with self.assertRaises(psycopg.errors.ProgramLimitExceeded) as raised:
            connection.execute('SELECT truss.preview_group_conditions(%s,%s,%s,%s)',
                (original, documents, manifest['releaseId'], digest))
        self.assertEqual(raised.exception.sqlstate, '54000')
        connection.execute('ROLLBACK TO SAVEPOINT preview_over_limit')
        connection.execute('RELEASE SAVEPOINT preview_over_limit')
        self.assertEqual(connection.execute('SELECT 42').fetchone(), (42,))
        self.assertEqual(self.admin.execute(counts).fetchone(), before)
        host.detach(); connection.commit()
        self.assertEqual(self.admin.execute(counts).fetchone(), before)


if __name__ == '__main__':
    import unittest
    unittest.main()
