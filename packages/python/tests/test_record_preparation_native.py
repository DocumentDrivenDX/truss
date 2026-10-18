"""Production value preparation uses one immutable schema and live admission."""
import json
from unittest.mock import patch

from truss import Ok, CatalogRuntimeConfiguration, HistoryEntity, HistoricalRecord, ObjectFound, adopt_psycopg_host, create_reference_assembly
from truss.contracts import MapValue, TextValue
from truss.groups import AuthoredValue, GroupFailed, GroupSuccess, GroupUnavailable, RequestNone, StoredObjectReference, UpdateObject
import test_group_create_native as base


class RecordPreparationTests(base.PublicCreateGroupTests):
    for name in tuple(n for n in dir(base.PublicCreateGroupTests) if n.startswith('test_')):
        locals()[name] = None

    def install(self):
        result = super().install()
        self.admin.execute("ALTER ROLE consumer SET track_functions='all'")
        return result

    def test_cold_schema_and_warm_batches_do_not_replay_native_value_validation(self):
        connection, host, assembly, tx = self.ready(document_ids=('adoc',))
        import truss._record_schema as schema
        context = assembly.group_context_in_transaction(tx).value
        with patch.object(schema, 'compile_records', wraps=schema.compile_records) as compile_once:
            first = assembly.apply_in_transaction(tx, context.input(tuple(
                self.create(label=f'first-{i}', alias=f'first-{i}') for i in range(16)), MapValue(entries=())),
                RequestNone(), documents=self.documents)
            self.assertIsInstance(first, Ok, repr(first) + ' ' + str(host._custody.last_attempt.error))
            self.assertIsInstance(first.value, GroupSuccess)
            identities = tuple(item.identity for item in first.value.response.semantic.results)
            updated = assembly.apply_in_transaction(tx, context.input(tuple(
                UpdateObject(target=StoredObjectReference(identity=identity),
                    set=(AuthoredValue(name='A-value', value=TextValue(kind='string', text=f'updated-{i}')),), unset=())
                for i, identity in enumerate(identities)), MapValue(entries=())), RequestNone(), documents=self.documents)
            self.assertIsInstance(updated, Ok, repr(updated) + ' ' + str(host._custody.last_attempt.error))
            self.assertIsInstance(updated.value, GroupSuccess)
            facade = create_reference_assembly(CatalogRuntimeConfiguration(), host).value
            self.assertIs(facade._record_schema_state, assembly._record_schema_state)
            other = facade.apply_in_transaction(tx, context.input((
                self.create(label='second-type', record='B', alias='other'),), MapValue(entries=())),
                RequestNone(), documents=self.documents)
            self.assertIsInstance(other, Ok, repr(other) + ' ' + str(host._custody.last_attempt.error))
            self.assertIsInstance(other.value, GroupSuccess)
            self.assertEqual(compile_once.call_count, 1)
        calls = dict(connection.execute('''SELECT p.proname, sum(s.calls) FROM pg_stat_xact_user_functions s
            JOIN pg_proc p ON p.oid=s.funcid WHERE s.schemaname='truss' GROUP BY p.proname''').fetchall())
        self.assertEqual(calls.get('writer_schema_basis'), 1)
        self.assertEqual(calls.get('runtime_owned_application_values'), 49)
        self.assertEqual(calls.get('owned_object_values', 0), 0)
        self.assertEqual(calls.get('runtime_owned_object_value_delta', 0), 0)
        # Exercise deferred settlement before observing its counters. Readback
        # intentionally follows this assertion: rendering validates read values
        # independently and must not be mistaken for write semantic replay.
        connection.execute('SET CONSTRAINTS ALL IMMEDIATE')
        settled = dict(connection.execute('''SELECT p.proname, sum(s.calls) FROM pg_stat_xact_user_functions s
            JOIN pg_proc p ON p.oid=s.funcid WHERE s.schemaname='truss' GROUP BY p.proname''').fetchall())
        self.assertGreater(settled.get('runtime_object_commit_check', 0), 0)
        self.assertEqual(settled.get('owned_object_values', 0), 0)
        self.assertEqual(settled.get('runtime_owned_object_value_delta', 0), 0)
        self.assertEqual(settled.get('valid_property_value', 0), 0)
        host.detach(); connection.commit()
        compact = self.admin.execute('''SELECT count(*),bool_and(
            NOT (plan->'beforeNodes'->(plan->>'primary')->'image' ? 'props')
            AND NOT (plan->'afterNodes'->(plan->>'primary')->'image' ? 'props')
            AND plan ? 'applicationPatch' AND plan ? 'desiredImageSha256')
            FROM truss.runtime_owned_operation
            WHERE plan->>'compactProfile'='truss-application-value-plan/0.1' ''').fetchone()
        self.assertEqual(compact, (16, True))
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone()[0], 17)

    def test_connection_selection_survives_host_and_transaction_rebinding(self):
        connection, host, assembly, tx = self.ready(document_ids=('adoc',))
        import truss._record_schema as schema
        with patch.object(schema, 'compile_records', wraps=schema.compile_records) as compile_once:
            context = assembly.group_context_in_transaction(tx).value
            self.assertIsInstance(self.apply(assembly, tx,
                context.input((self.create(),), MapValue(entries=())), RequestNone()), GroupSuccess)
            state = assembly._record_schema_state
            host.detach(); connection.commit()
            # Function statistics include this backend's unflushed prior work.
            # Flush it while idle so the next transaction's exact counters
            # observe only its own warm write, not the preceding cold write.
            connection.execute('SELECT pg_stat_force_next_flush()')
            connection.execute('BEGIN')
            host = adopt_psycopg_host(connection, statement_timeout_ms=10000, operation_timeout_ms=30000)
            self.addCleanup(host.detach)
            self.consumer_connections.append((connection, host))
            tx = host.adopt_transaction().value
            rebound = create_reference_assembly(CatalogRuntimeConfiguration(), host).value
            self.assertIs(rebound._record_schema_state, state)
            context = rebound.group_context_in_transaction(tx).value
            self.assertIsInstance(self.apply(rebound, tx, context.input((
                self.create(label='after-commit', alias='after-commit'),), MapValue(entries=())), RequestNone()), GroupSuccess)
            self.assertEqual(compile_once.call_count, 1)
            calls = dict(connection.execute('''SELECT p.proname, sum(s.calls) FROM pg_stat_xact_user_functions s
                JOIN pg_proc p ON p.oid=s.funcid WHERE s.schemaname='truss' GROUP BY p.proname''').fetchall())
            self.assertEqual(calls.get('writer_schema_basis', 0), 0)
            self.assertEqual(calls.get('runtime_owned_application_values'), 1)
            host.detach(); connection.commit()

    def test_invalid_and_revoked_warm_writes_keep_native_failures(self):
        connection, host, assembly, tx = self.ready(document_ids=('adoc',))
        context = assembly.group_context_in_transaction(tx).value
        first = self.apply(assembly, tx, context.input((self.create(),), MapValue(entries=())), RequestNone())
        self.assertIsInstance(first, GroupSuccess)
        identity = first.response.semantic.results[0].identity
        bad = UpdateObject(target=StoredObjectReference(identity=identity),
            set=(AuthoredValue(name='A-value', value=TextValue(kind='integer', text='1')),), unset=())
        failed = self.apply(assembly, tx, context.input((bad,), MapValue(entries=())), RequestNone())
        self.assertIsInstance(failed, GroupFailed)
        good = UpdateObject(target=StoredObjectReference(identity=identity),
            set=(AuthoredValue(name='A-value', value=TextValue(kind='string', text='next')),), unset=())
        self.admin.execute('REVOKE group_writer FROM consumer')
        refused = assembly.apply_in_transaction(tx, context.input((good,), MapValue(entries=())),
            RequestNone(), documents=self.documents)
        self.assertIsInstance(refused, Ok, repr(refused))
        self.assertIsInstance(refused.value, GroupFailed)
        self.assertEqual(refused.value.failure.__class__.__name__, 'UnauthorizedPerson')
        host.detach(); connection.rollback()

    def test_native_fallback_after_compact_update_keeps_effects_and_history(self):
        connection, host, assembly, tx = self.ready(document_ids=('adoc',))
        context = assembly.group_context_in_transaction(tx).value
        created = self.apply(assembly, tx, context.input((self.create(),), MapValue(entries=())), RequestNone())
        identity = created.response.semantic.results[0].identity
        def update(text):
            return context.input((UpdateObject(target=StoredObjectReference(identity=identity),
                set=(AuthoredValue(name='A-value', value=TextValue(kind='string', text=text)),),
                unset=()),), MapValue(entries=()))
        self.assertIsInstance(self.apply(assembly, tx, update('compiled'), RequestNone()), GroupSuccess)
        import truss._record_preparation as preparation
        with patch.object(preparation, 'prepare_records', return_value=None):
            self.assertIsInstance(self.apply(assembly, tx, update('native'), RequestNone()), GroupSuccess)
        host.detach(); connection.commit()
        counts = self.admin.execute('''SELECT
            count(*) FILTER(WHERE plan->>'compactProfile'='truss-application-value-plan/0.1'),
            count(*) FILTER(WHERE NOT (plan ? 'compactProfile'))
            FROM truss.runtime_owned_operation WHERE plan->'operation'->>'operation'='update_object' ''').fetchone()
        self.assertEqual(counts, (1, 1))
        value_id = str(self.admin.execute("SELECT prop_id FROM truss.prop_def WHERE name='A-value'").fetchone()[0])
        connection, host, assembly, tx = self.consumer()
        read = assembly.get_object_in_transaction(tx, document_id='adoc', module_id='m', record_id='A', object_id=int(identity.id))
        self.assertIsInstance(read.value, ObjectFound, repr(read))
        self.assertEqual(read.value.object.version, 3)
        self.assertEqual(dict(read.value.object.values)['A-value'], 'native')
        for version, text in enumerate(('value', 'compiled', 'native'), 1):
            history = assembly.reconstruct_in_transaction(tx,
                entity=HistoryEntity(kind='object', document_id='adoc', module_id='m', definition_id='A', id=int(identity.id)),
                version=version)
            self.assertIsInstance(history.value, HistoricalRecord, repr(history))
            image = json.loads(history.value.record)
            values = {entry['propertyId']: entry['value'] for entry in image['properties']}
            self.assertEqual(values[value_id], {'kind': 'string', 'text': text})
        host.detach(); connection.commit()

    def test_stale_prepared_registration_refuses_without_effects_or_retry(self):
        connection, host, assembly, tx = self.ready(document_ids=('adoc',))
        context = assembly.group_context_in_transaction(tx).value
        self.assertIsInstance(self.apply(assembly, tx,
            context.input((self.create(),), MapValue(entries=())), RequestNone()), GroupSuccess)
        connection.execute("CREATE TEMP TABLE earlier_work(value text); INSERT INTO earlier_work VALUES('kept')")
        import truss._record_preparation as preparation
        actual = preparation.prepare_records
        observed = []
        def stale(*args, **kwargs):
            result = actual(*args, **kwargs)
            self.assertIsNotNone(result)
            result['basis']['registrationId'] = '00000000-0000-0000-0000-000000000000'
            observed.append(result)
            return result
        second = context.input((self.create(label='second', alias='second'),), MapValue(entries=()))
        with patch.object(preparation, 'prepare_records', stale):
            refused = self.apply(assembly, tx, second, RequestNone())
        self.assertIsInstance(refused, GroupUnavailable)
        self.assertEqual(refused.reason, 'observation')
        self.assertEqual(len(observed), 1)
        self.assertEqual(assembly._record_schema_state, {})
        self.assertEqual(connection.execute('TABLE earlier_work').fetchall(), [('kept',)])
        # The caller makes the next explicit attempt; no internal retry occurred.
        self.assertIsInstance(self.apply(assembly, tx, second, RequestNone()), GroupSuccess)
        host.detach(); connection.commit()
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone()[0], 2)
