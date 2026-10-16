"""Private complete native control custody; no public recovery qualification."""
import unittest
from unittest.mock import patch
from test_native_pg8000 import NativeBoundaryFixture
from truss._host_execution import HostExecutor
from truss._native_transactions import NativeTransactions
from truss._native_arbitration import NativeArbitration
from truss._host_session import NativeHostSession
from truss._host_control_custody import HostControlCustody
from truss.execution import Ok,Error

class HostControlCustodyTests(NativeBoundaryFixture,unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.boundary.run('SELECT 1')
        self.executor=HostExecutor();self.tracker=NativeTransactions(self.boundary)
        self.service=NativeArbitration(self.executor)
        self.producer=HostControlCustody(self.executor)
        self.session=NativeHostSession(self.executor,self.tracker,self.service,control_producer=self.producer)

    def baseline(self):
        result=self.session.observe_host_resource_baseline()
        self.assertIsInstance(result,Ok)
        self.assertIs(self.boundary._resource_baseline,result.value)

    def test_explicit_baseline_required_without_implicit_sql(self):
        before=self.boundary.last_call
        self.assertEqual(self.session.begin().error.code,'execution_obligation')
        self.assertIs(self.boundary.last_call,before)
        self.assertIsNone(self.boundary._operation)
        self.baseline()
        self.assertIsInstance(self.session.begin(),Ok)
        self.assertIsInstance(self.session.rollback(),Ok)

    def test_complete_workflow_restores_context_and_transfers_savepoint(self):
        original=self.connection._context
        self.baseline()
        self.assertIs(self.connection._context,original)
        self.assertIsInstance(self.session.begin(),Ok)
        tx=self.session.adopt_transaction().value
        self.assertEqual(len(self.producer._ledgers[-1].calls),3)
        self.boundary.run('CREATE TEMP TABLE custody_fixture(value int)',token=None)
        self.boundary.run('INSERT INTO custody_fixture VALUES(1)')
        host_context=self.connection._context
        sp=self.session.savepoint(tx).value
        ledger=self.producer._ledgers[-1]
        self.assertIs(ledger.completion.savepoints[-1],self.tracker._state.savepoints[-1])
        self.assertTrue(ledger.result_custody.detached)
        self.assertIs(self.connection._context,host_context)
        self.assertTrue(all(e.context.rows is None and e.context.columns is None for e in ledger.calls))
        self.boundary.run('INSERT INTO custody_fixture VALUES(2)')
        self.assertIsInstance(self.session.rollback_to_savepoint(tx,sp),Ok)
        self.assertIsInstance(self.session.release_savepoint(tx,sp),Ok)
        self.assertEqual(self.session.commit().value.state,'committed')
        self.assertEqual(self.boundary.run('SELECT value FROM custody_fixture'),[[1]])
        self.assertIsNone(self.boundary._host_control_pending)

    def test_duplicate_adoption_is_known_refusal_without_poisoning(self):
        self.baseline();self.session.begin();tx=self.session.adopt_transaction().value
        before=self.boundary.last_call
        self.assertEqual(self.session.adopt_transaction().error.code,'invalid_transaction')
        self.assertIs(self.boundary.last_call,before)
        self.assertIsInstance(self.session.savepoint(tx),Ok)
        self.session.rollback()

    def test_sql_prepare_baseline_refuses_and_preserves_host_resource(self):
        self.boundary.run('PREPARE host_owned AS SELECT 1')
        result=self.session.observe_host_resource_baseline()
        self.assertIsInstance(result,Error)
        self.assertEqual(result.error.code,'invalid_transaction')
        self.assertIsNone(self.boundary._operation)
        self.assertIsNone(self.boundary._resource_baseline)
        self.assertEqual(self.boundary.run('EXECUTE host_owned'),[[1]])
        self.boundary.run('DEALLOCATE host_owned');self.baseline()

    def test_parse_and_named_bind_history_refuses_until_host_baseline(self):
        self.baseline()
        self.boundary.run('SELECT :value::pg_catalog.text',value='host')
        self.assertTrue(self.boundary._unnamed_pending)
        last=self.boundary.last_call
        self.assertIsInstance(self.session.begin(),Error)
        self.assertIs(self.boundary.last_call,last)
        self.baseline()
        prepared=self.boundary.prepare('SELECT :value::pg_catalog.text')
        prepared.run(value='host')
        self.assertTrue(self.boundary._unnamed_pending)
        last=self.boundary.last_call
        self.assertIsInstance(self.session.begin(),Error)
        self.assertIs(self.boundary.last_call,last)
        prepared.close();self.baseline()

    def test_original_context_is_reserved_before_failed_send(self):
        self.baseline()
        original=self.connection.send_QUERY
        def fail(sql):
            ledger=self.boundary._host_control_pending
            self.assertIsNotNone(ledger.calls[-1].context)
            self.assertIs(ledger.result_custody.contexts[0],ledger.calls[-1].context)
            raise OSError('Selected failed native send')
        # Inject only after pure entry profile selection, at the original adapter seam.
        run=self.producer.attach
        def attach(boundary,record):
            ledger=run(boundary,record)
            self.connection.send_QUERY=fail
            return ledger
        try:
            with patch.object(self.producer,'attach',side_effect=attach):
                result=self.session.begin()
            self.assertEqual(result.error.code,'transaction_unusable')
            ledger=self.boundary._host_control_pending
            self.assertIsNotNone(ledger.calls[-1].context)
            self.assertFalse(ledger.calls[-1].native_call.capture_complete)
            self.assertIs(self.boundary._operation,ledger.token)
        finally:self.connection.send_QUERY=original

    def test_hostile_operator_cannot_hide_held_named_cursor(self):
        self.boundary.run('CREATE SCHEMA hostile_baseline')
        self.boundary.run("CREATE FUNCTION hostile_baseline.hide(pg_catalog.text,pg_catalog.text) RETURNS pg_catalog.bool LANGUAGE SQL AS 'SELECT false'")
        self.boundary.run('CREATE OPERATOR hostile_baseline.<> (LEFTARG=pg_catalog.text,RIGHTARG=pg_catalog.text,FUNCTION=hostile_baseline.hide)')
        self.tracker.begin()
        self.boundary.run('DECLARE preserved_cursor CURSOR WITH HOLD FOR SELECT 7')
        self.tracker.commit()
        self.boundary.run('SET search_path=hostile_baseline,pg_catalog')
        try:
            self.assertIsInstance(self.session.observe_host_resource_baseline(),Error)
            self.assertIsNone(self.boundary._resource_baseline)
            self.assertEqual(self.boundary.run('FETCH ALL FROM preserved_cursor'),[[7]])
            self.boundary.run('CLOSE preserved_cursor')
            self.baseline()
        finally:
            self.boundary.run('SET search_path=pg_catalog')
            self.boundary.run('DROP SCHEMA hostile_baseline CASCADE')

    def test_foreign_bound_simple_methods_refuse_without_sql(self):
        self.baseline()
        other=self.Connection(**self.kwargs);other.run('SELECT 9')
        try:
            for name in ('send_QUERY','_send_message','execute_simple'):
                with self.subTest(name=name):
                    before=self.boundary.last_call;context=other._context
                    original=getattr(self.connection,name)
                    try:
                        setattr(self.connection,name,getattr(other,name))
                        self.assertIsInstance(self.session.begin(),Error)
                        self.assertIs(self.boundary.last_call,before)
                        self.assertIs(other._context,context)
                        self.assertIsNone(self.boundary._operation)
                    finally:setattr(self.connection,name,original)
            self.assertIsInstance(self.session.begin(),Ok);self.session.rollback()
        finally:other.close()

    def test_restoration_publication_fault_retains_boundary_owned_ledger(self):
        self.baseline();self.session.begin();self.session.adopt_transaction()
        publish=self.boundary._publish_ownership
        def lose_restore(root):
            ledger=self.boundary._host_control_pending
            publish(root)
            if ledger is not None and root is ledger.original_root:
                raise MemoryError('Lost restoration reply')
        with patch.object(self.boundary,'_publish_ownership',side_effect=lose_restore):
            result=self.session.commit()
        self.assertEqual((result.value.state,result.value.handback),('committed','quarantined'))
        ledger=self.boundary._host_control_pending
        self.assertIs(self.boundary._ownership,ledger.original_root)
        self.assertTrue(ledger.result_custody.detached)
        self.assertFalse(ledger.record.release.published)
        with self.assertRaises(Exception):self.boundary.run('SELECT 1',token=ledger.token)
        with self.assertRaises(Exception):self.boundary.release_operation(ledger.token)

    def test_lost_release_reply_reconciles_exact_completed_control(self):
        self.baseline();self.session.begin();self.session.adopt_transaction()
        publish=self.boundary._publish_ownership
        def lose_release(root):
            ledger=self.boundary._host_control_pending
            publish(root)
            if ledger is not None and root is ledger.record.release.after:
                raise MemoryError('Lost completed release reply')
        with patch.object(self.boundary,'_publish_ownership',side_effect=lose_release):
            result=self.session.commit()
        self.assertEqual((result.value.state,result.value.handback),('committed','released'))
        self.assertIsNone(self.boundary._host_control_pending)
        self.assertIsNone(self.boundary._operation)
        self.assertIsInstance(self.session.begin(),Ok);self.session.rollback()

    def test_missing_profile_command_complete_never_publishes_handle(self):
        from truss._host_control_custody import PROFILE_SQL
        self.baseline();self.session.begin()
        attach=self.producer.attach
        dropped=[]
        def intercept(boundary,record):
            ledger=attach(boundary,record)
            gate=ledger.result_custody
            read=gate.read
            def filtered(size):
                header=read(size)
                if size==5 and header[:1]==b'C' and ledger.calls[-1].sql==PROFILE_SQL:
                    payload=read(int.from_bytes(header[1:],'big')-4)
                    self.assertEqual(payload,b'SELECT 1\0')
                    dropped.append(payload)
                    return read(size)
                return header
            gate.read=filtered
            return ledger
        with patch.object(self.producer,'attach',side_effect=intercept):
            result=self.session.adopt_transaction()
        self.assertIsInstance(result,Error)
        self.assertEqual(dropped,[b'SELECT 1\0'])
        ledger=self.boundary._host_control_pending
        self.assertFalse(ledger.calls[-1].native_call.capture_complete)
        self.assertTrue(ledger.admission_closed)
        self.assertIs(self.boundary._operation,ledger.token)

    def test_one_producer_per_executor_and_shared_capacity(self):
        with self.assertRaises(ValueError):HostControlCustody(self.executor)
        self.producer._limit=1
        self.baseline()
        before=self.boundary.last_call
        self.assertEqual(self.session.begin().error.code,'execution_obligation')
        self.assertIs(self.boundary.last_call,before)
        self.assertIsNone(self.boundary._operation)
        self.assertFalse(self.boundary._quarantined)

    def test_busy_shared_reservation_refuses_without_sql(self):
        before=self.boundary.last_call
        self.producer._lock.acquire()
        try:result=self.session.observe_host_resource_baseline()
        finally:self.producer._lock.release()
        self.assertEqual(result.error.code,'execution_obligation')
        self.assertIs(self.boundary.last_call,before)
        self.assertIsNone(self.boundary._operation)
        self.assertFalse(self.boundary._quarantined)

    def test_verified_text_cleanup_allows_next_host_control(self):
        from truss._native_operation import NativeOperationRunner
        self.baseline();self.session.begin()
        tx=self.session.adopt_transaction().value
        runner=NativeOperationRunner(self.service)
        statement=runner.register('SELECT :value::pg_catalog.text','SELECT')
        result=runner.execute(tx,statement,{'value':'composed'})
        self.assertIsInstance(result,Ok,repr(result))
        self.assertEqual(result.value,(('composed',),))
        self.assertFalse(self.boundary._unnamed_pending)
        self.assertIsInstance(self.session.savepoint(tx),Ok)
        self.assertEqual(self.session.commit().value.state,'committed')

    def test_text_runner_preserves_host_unnamed_resources(self):
        from truss._native_operation import NativeOperationRunner
        self.baseline();self.session.begin()
        tx=self.session.adopt_transaction().value
        self.boundary.run('SELECT :value::pg_catalog.text',value='host')
        runner=NativeOperationRunner(self.service)
        statement=runner.register('SELECT :value::pg_catalog.text','SELECT')
        before=self.boundary.last_call
        self.assertIsInstance(runner.execute(tx,statement,{'value':'refused'}),Error)
        self.assertIs(self.boundary.last_call,before)
        self.assertTrue(self.boundary._unnamed_pending)

    def test_known_deferred_abort_survives_composed_result_fault(self):
        self.boundary.run('CREATE TEMP TABLE deferred_fixture(value int UNIQUE DEFERRABLE INITIALLY DEFERRED)')
        self.baseline();self.session.begin();self.session.adopt_transaction()
        self.boundary.run('INSERT INTO deferred_fixture VALUES(1),(1)')
        with patch.object(self.session,'_settlement_result',side_effect=MemoryError):
            result=self.session.commit()
        self.assertIsInstance(result,Ok)
        self.assertEqual(result.value.state,'rolled_back')
        self.assertEqual(result.value.sql_state,'23505')
        self.assertEqual(result.value.handback,'quarantined')
        self.assertTrue(self.boundary._host_control_pending.admission_closed)
        self.assertIsNotNone(self.boundary._operation)

    def test_two_boundaries_share_atomic_capacity(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        from truss._native_pg8000 import NativeBoundary
        other=self.Connection(**self.kwargs)
        try:
            other.run('SELECT 1')
            boundary=NativeBoundary(other)
            boundary.run('SELECT 1')
            tracker=NativeTransactions(boundary)
            session=NativeHostSession(self.executor,tracker,self.service,control_producer=self.producer)
            self.producer._limit=1
            rendezvous=Barrier(2)
            original=self.producer.preflight
            def preflight(b,kind):
                result=original(b,kind)
                rendezvous.wait(timeout=5)
                return result
            before=(self.boundary.last_call,boundary.last_call)
            with patch.object(self.producer,'preflight',side_effect=preflight):
                with ThreadPoolExecutor(max_workers=2) as workers:
                    futures=[workers.submit(s.observe_host_resource_baseline) for s in (self.session,session)]
                    results=[f.result(timeout=10) for f in futures]
            self.assertEqual(sum(isinstance(r,Ok) for r in results),1)
            self.assertEqual(len(self.producer._ledgers),1)
            for b,old,result in zip((self.boundary,boundary),before,results):
                self.assertIsNone(b._operation)
                self.assertFalse(b._quarantined)
                if isinstance(result,Error):
                    self.assertEqual(result.error.code,'execution_obligation')
                    self.assertIs(b.last_call,old)
        finally:other.close()

    def test_extended_ack_is_refused_in_simple_query(self):
        from truss._host_control_custody import PROFILE_SQL
        self.baseline();self.session.begin()
        attach=self.producer.attach
        def intercept(boundary,record):
            ledger=attach(boundary,record)
            gate=ledger.result_custody
            messages=gate.original_handle_messages
            def inject(context):
                if ledger.calls[-1].sql==PROFILE_SQL:
                    # Synthetic unexpected-frame fault, not a native server claim.
                    gate._handlers[b'1'](b'',context)
                return messages(context)
            gate.original_handle_messages=inject
            return ledger
        with patch.object(self.producer,'attach',side_effect=intercept):
            result=self.session.adopt_transaction()
        self.assertIsInstance(result,Error)
        self.assertTrue(self.boundary._quarantined)
        self.assertIsNotNone(self.boundary._host_control_pending)
        self.assertIsNone(self.boundary._host_control_pending.completion)

    def test_acknowledged_commit_before_lost_ready_remains_known(self):
        from uuid import uuid4
        table='control_ack_'+uuid4().hex
        self.boundary.run('CREATE TABLE '+table+' (value int)')
        self.baseline();self.session.begin();self.session.adopt_transaction()
        self.boundary.run('INSERT INTO '+table+' VALUES(1)')
        attach=self.producer.attach
        def intercept(boundary,record):
            ledger=attach(boundary,record)
            original=self.connection.message_types[b'C']
            def lose_ready(data,context):
                original(data,context)
                if data==b'COMMIT\0':raise OSError('lost Ready after native acknowledgment')
            self.connection.message_types[b'C']=lose_ready
            return ledger
        observer=self.Connection(**self.kwargs)
        try:
            with patch.object(self.producer,'attach',side_effect=intercept):
                result=self.session.commit()
            self.assertIsInstance(result,Ok)
            self.assertEqual((result.value.state,result.value.handback),('committed','quarantined'))
            self.assertFalse(self.boundary.last_call.capture_complete)
            self.assertIsNotNone(self.boundary._operation)
            self.assertEqual(observer.run('SELECT count(*) FROM '+table),[[1]])
        finally:
            observer.run('DROP TABLE '+table);observer.close()
