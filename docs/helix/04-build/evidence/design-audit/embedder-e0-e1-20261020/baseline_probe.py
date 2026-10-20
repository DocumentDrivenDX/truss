"""Expected pre-change failures, against the frozen E0 wheel only."""
from dataclasses import replace
import base64
import json
from truss import Error, Ok
from truss.groups import GroupFailed, GroupSuccess, ObjectExists
import test_group_preconditions_native as conditions


class BaselineProbe(conditions.GroupPreconditionTests):
    for _name in tuple(n for n in dir(conditions.GroupPreconditionTests) if n.startswith('test_')):
        locals()[_name] = None

    def test_153_conditions_are_refused_before_change(self):
        connection, host, assembly, tx, a, b, pin = self.initialized()
        checks = tuple(ObjectExists(id='condition-'+str(i), reason='exists', target=a) for i in range(153))
        result, _, _ = self.condition_group(assembly, tx, a, checks, 'baseline-153')
        self.assertIsInstance(result, GroupFailed)
        self.assertEqual(result.failure.code, 'invalid')
        self.assertEqual(dict(self.read(assembly, tx, a).object.values)['A-label'], 'one')
        host.detach(); connection.rollback()

    def test_guarded_client_statement_baseline(self):
        import os
        import time
        from pathlib import Path
        from unittest.mock import patch
        import psycopg as native
        from truss.contracts import MapValue, TextValue
        from truss.groups import AuthoredValue, UpdateObject, StoredObjectReference, RequestNone
        connection, host, assembly, tx, a, b, pin = self.initialized()
        observed = []
        original = native.Cursor
        class CountedCursor(original):
            def execute(self, query, params=None, **kwargs):
                observed.append(str(query))
                return super().execute(query, params, **kwargs)
        measurements = {}
        def measure(name, invoke):
            observed.clear()
            start = time.perf_counter()
            with patch.object(native, 'Cursor', CountedCursor):
                result = invoke()
            self.assertIsInstance(result, Ok, repr(result))
            measurements[name] = {'clientStatements':len(observed),
                                  'elapsedSeconds':time.perf_counter()-start,
                                  'statementTemplates':observed.copy()}
            return result.value
        context = measure('groupContext', lambda:assembly.group_context_in_transaction(tx))
        measure('readerCatalog', lambda:assembly.reader_catalog_in_transaction(tx))
        measure('pointObjectRead', lambda:assembly.get_object_in_transaction(tx,
            document_id='adoc', module_id='m', record_id='A', object_id=int(a.id)))
        operation = UpdateObject(target=StoredObjectReference(identity=a),
            set=(AuthoredValue(name='A-label',value=TextValue(kind='string',text='measured')),),unset=())
        applied = measure('oneUpdateApply', lambda:assembly.apply_in_transaction(tx,
            context.input((operation,),MapValue(entries=())),RequestNone(),documents=self.documents))
        self.assertIsInstance(applied, GroupSuccess)
        measurements['scope'] = 'Single calls in one already adopted caller transaction; setup/BEGIN/COMMIT, network round trips and server-internal statements excluded. One observation per call, no latency distribution or speed guarantee.'
        label = os.environ['TRUSS_EMBEDDER_MEASUREMENT_LABEL']
        (Path(__file__).parent/(label+'-measurements.json')).write_text(json.dumps(measurements,indent=2)+'\n')
        host.detach(); connection.rollback()

    def test_second_create_collision_reports_zero_before_change(self):
        connection, host, assembly, tx, a, b, pin = self.initialized()
        result, _, _ = self.run_group(assembly, tx,
            (self.create(label='baseline-free', alias='free'), self.create(alias='collision')))
        self.assertIsInstance(result, GroupFailed)
        original = json.loads(base64.b64decode(result.failure.inner_error.bytes_base64))
        self.assertEqual(original['code'], 'key_conflict')
        self.assertEqual(result.failure.operation_index, '0')
        host.detach(); connection.rollback()

    def test_nonmember_context_is_raw_error_before_change(self):
        connection, host, assembly, tx, a, b, pin = self.initialized()
        host.detach(); connection.rollback()
        self.admin.execute('REVOKE group_writer FROM consumer')
        connection, host, assembly, tx = self.consumer()
        result = assembly.group_context_in_transaction(tx)
        self.assertIsInstance(result, Error)
        self.assertEqual(result.error.sql_state, '42501')
        self.assertEqual(connection.execute('SELECT 42').fetchone(), (42,))
        host.detach(); connection.rollback()
