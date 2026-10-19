# SPDX-License-Identifier: MIT OR Apache-2.0
"""Fresh public host composition with original control custody, no graph API."""
import unittest
from unittest.mock import patch
from test_native_pg8000 import NativeBoundaryFixture
from truss.host import connect_pg8000_host
from truss import Ok,Error,TransactionHandle

class PublicHostTests(NativeBoundaryFixture,unittest.TestCase):
    def setUp(self):
        self.host=connect_pg8000_host(user='postgres',database='postgres',unix_sock=self.kwargs['unix_sock'])
    def tearDown(self):
        self.host.close()
    def test_real_host_work_and_adoption(self):
        h=self.host;s=h.session
        self.assertIsInstance(s.observe_host_resource_baseline(),Ok)
        self.assertIsInstance(s.begin(),Ok)
        tx=s.adopt_transaction().value
        self.assertIsInstance(tx,TransactionHandle)
        h.connection.run_non_lifecycle('CREATE TEMP TABLE public_host_work(value text)')
        h.connection.run_non_lifecycle("INSERT INTO public_host_work VALUES('before')")
        savepoint=s.savepoint(tx).value
        h.connection.run_non_lifecycle("INSERT INTO public_host_work VALUES('after')")
        self.assertIsInstance(s.rollback_to_savepoint(tx,savepoint),Ok)
        self.assertIsInstance(s.release_savepoint(tx,savepoint),Ok)
        self.assertEqual(s.commit().value.state,'committed')
        self.assertEqual(h.connection.run_non_lifecycle('SELECT value FROM public_host_work'),[['before']])
        self.assertIsInstance(s.savepoint(tx),Error)
    def test_dispose_leaves_host_rollback_route(self):
        s=self.host.session
        self.assertIsInstance(s.observe_host_resource_baseline(),Ok)
        self.assertIsInstance(s.begin(),Ok)
        tx=s.adopt_transaction().value
        s.dispose()
        self.assertIsInstance(s.savepoint(tx),Error)
        self.assertEqual(s.rollback().value.state,'rolled_back')

    def test_failed_composition_closes_created_connection(self):
        from truss._native_bootstrap import NativeConnectionFactory
        captured=[];original=NativeConnectionFactory.connect
        def connect(factory,**kwargs):
            boundary=original(factory,**kwargs);captured.append(boundary);return boundary
        with patch.object(NativeConnectionFactory,'connect',connect), patch('truss._host_session.NativeHostSession',side_effect=ValueError('composition')):
            with self.assertRaisesRegex(ValueError,'composition'):
                connect_pg8000_host(user='postgres',database='postgres',unix_sock=self.kwargs['unix_sock'])
        self.assertEqual(len(captured),1)
        self.assertTrue(captured[0]._quarantined)
        self.assertTrue(captured[0]._original_stream.closed)
        self.assertEqual(captured[0]._connection._usock.fileno(),-1)

    def test_failed_cleanup_retains_original_connection(self):
        from truss.host import HostCompositionFailure
        from truss._native_pg8000 import NativeBoundary
        with patch('truss._host_session.NativeHostSession',side_effect=ValueError('composition')), patch('truss._native_bootstrap.NativeConnectionFactory.close_host',side_effect=OSError('cleanup')):
            with self.assertRaises(HostCompositionFailure) as raised:
                connect_pg8000_host(user='postgres',database='postgres',unix_sock=self.kwargs['unix_sock'])
        failure=raised.exception
        self.assertIsInstance(failure.primary_failure,ValueError)
        self.assertIsInstance(failure.cleanup_failure,OSError)
        failure._factory.close_host(failure.connection)

    def test_host_close_proves_original_stream_and_descriptor_release(self):
        stream=self.host.connection._boundary._original_stream
        sock=self.host.connection._boundary._connection._usock
        self.assertTrue(self.host.close())
        self.assertTrue(stream.closed)
        self.assertEqual(sock.fileno(),-1)
        self.assertTrue(self.host.close())

    def test_close_refuses_active_operation_without_discarding_resource(self):
        from truss._native_pg8000 import NativeBoundaryRefusal
        b=self.host.connection._boundary;token=b.acquire_operation()
        try:
            with self.assertRaises(NativeBoundaryRefusal):self.host.close()
            self.assertFalse(b._original_stream.closed)
        finally:b.release_operation(token)
        self.assertTrue(self.host.close())

    def test_close_reservation_blocks_concurrent_host_call(self):
        from threading import Event,Thread
        from truss._native_pg8000 import NativeBoundaryRefusal
        record=self.host._factory._records[0]
        entered=Event();proceed=Event();results=[]
        original=type(record)._close_resources
        def paused(item,**kwargs):
            entered.set()
            if not proceed.wait(5):raise RuntimeError('Test synchronization timeout')
            return original(item,**kwargs)
        with patch.object(type(record),'_close_resources',paused):
            worker=Thread(target=lambda:results.append(self.host.close()))
            worker.start()
            try:
                self.assertTrue(entered.wait(5))
                with self.assertRaises(NativeBoundaryRefusal):self.host.connection.run_non_lifecycle('SELECT 1')
                with self.assertRaises(NativeBoundaryRefusal):self.host.close(retry=True)
            finally:proceed.set();worker.join(5)
        self.assertFalse(worker.is_alive())
        self.assertEqual(results,[True])

    def test_namespaces_counters_do_not_rewind_after_release(self):
        s=self.host.session
        s.observe_host_resource_baseline();s.begin();tx=s.adopt_transaction().value
        first=s.savepoint(tx).value
        self.assertRegex(first._key,r'^truss_sp_[0-9a-f]{32}_1$')
        self.assertIsInstance(s.rollback_to_savepoint(tx,first),Ok)
        self.assertIsInstance(s.release_savepoint(tx,first),Ok)
        second=s.savepoint(tx).value
        self.assertEqual(second._key,first._key[:-1]+'2')
        from truss._native_pg8000 import NativeBoundaryRefusal
        with self.assertRaises(NativeBoundaryRefusal):s.tracker.savepoint(second._key)
        s.release_savepoint(tx,second)
        s.tracker._state.generation.namespaces[0].next_counter=18446744073709551616
        self.assertIsInstance(s.savepoint(tx),Error)
        self.assertEqual(s.rollback().value.state,'rolled_back')

    def test_lost_inner_factory_publication_reply_closes_unreturned_resource(self):
        from truss._native_bootstrap import NativeConnectionFactory,BootstrapFailure
        original=NativeConnectionFactory._publish;records=[]
        def lost(factory,record,boundary):
            original(factory,record,boundary);records.append(record)
            raise OSError('lost publication reply')
        with patch.object(NativeConnectionFactory,'_publish',lost):
            with self.assertRaises(BootstrapFailure):
                connect_pg8000_host(user='postgres',database='postgres',unix_sock=self.kwargs['unix_sock'])
        self.assertTrue(records[0].exposed)
        self.assertTrue(records[0].closed)
        self.assertTrue(records[0].stream.closed)
        self.assertEqual(records[0].socket.fileno(),-1)

    def test_host_savepoints_share_native_stack_and_reserve_truss_namespace(self):
        s=self.host.session
        s.observe_host_resource_baseline();s.begin();tx=s.adopt_transaction().value
        host=s.host_savepoint('host_boundary').value
        truss=s.savepoint(tx).value
        self.assertIsInstance(s.host_savepoint(truss._key),Error)
        self.assertIsInstance(s.host_rollback_to_savepoint(host),Ok)
        self.assertIsInstance(s.release_savepoint(tx,truss),Error)
        self.assertIsInstance(s.host_release_savepoint(host),Ok)
        self.assertEqual(s.rollback().value.state,'rolled_back')

    def test_original_recovery_observation_is_pure(self):
        s=self.host.session
        s.observe_host_resource_baseline();s.begin()
        reference=s.last_call_reference
        before=self.host.connection._boundary.last_call
        observation=s.recovery.observe(reference)
        self.assertIsInstance(observation,Ok)
        self.assertIs(self.host.connection._boundary.last_call,before)
        self.assertEqual(s.rollback().value.state,'rolled_back')

    def test_released_namespace_name_cannot_be_submitted_again(self):
        from truss._native_pg8000 import NativeBoundaryRefusal
        s=self.host.session
        s.observe_host_resource_baseline();s.begin();tx=s.adopt_transaction().value
        handle=s.savepoint(tx).value
        self.assertIsInstance(s.release_savepoint(tx,handle),Ok)
        port=s.executor._original_custody(tx).port
        boundary=self.host.connection._boundary
        token=boundary.acquire_operation()
        before=boundary.last_call
        try:
            port.bind_operation(token)
            with self.assertRaisesRegex(NativeBoundaryRefusal,'One-use'):
                port.control('SAVEPOINT '+handle._key)
            self.assertIs(boundary.last_call,before)
        finally:boundary.release_operation(token)
        self.assertEqual(s.rollback().value.state,'rolled_back')

    def test_fatal_lost_factory_reply_preserves_exception_and_closes_resource(self):
        from truss._native_bootstrap import NativeConnectionFactory
        original=NativeConnectionFactory._publish
        for exception in (KeyboardInterrupt('publication'),SystemExit('publication')):
            records=[]
            def lost(factory,record,boundary):
                original(factory,record,boundary);records.append(record)
                raise exception
            with patch.object(NativeConnectionFactory,'_publish',lost):
                with self.assertRaises(type(exception)) as raised:
                    connect_pg8000_host(user='postgres',database='postgres',unix_sock=self.kwargs['unix_sock'])
            self.assertIs(raised.exception,exception)
            self.assertTrue(records[0].exposed)
            self.assertTrue(records[0].closed)
            self.assertTrue(records[0].stream.closed)
            self.assertEqual(records[0].socket.fileno(),-1)

    def test_known_savepoint_refusals_preserve_rollback(self):
        s=self.host.session
        self.assertIsInstance(s.host_savepoint('idle'),Error)
        s.observe_host_resource_baseline();s.begin()
        s.tracker._limit=1
        point=s.host_savepoint('caller').value
        self.assertIsInstance(s.host_savepoint('overflow'),Error)
        try:self.host.connection.run_non_lifecycle('SELECT 1/0')
        except Exception:pass
        self.assertIsInstance(s.host_release_savepoint(point),Error)
        self.assertEqual(s.rollback().value.state,'rolled_back')

    def test_host_savepoint_lifecycle_survives_executor_disposal(self):
        s=self.host.session
        s.observe_host_resource_baseline();s.begin()
        point=s.host_savepoint('caller').value
        s.dispose()
        self.assertIsInstance(s.host_rollback_to_savepoint(point),Ok)
        self.assertIsInstance(s.host_release_savepoint(point),Ok)
        self.assertEqual(s.rollback().value.state,'rolled_back')

    def test_sibling_assemblies_preserve_real_host_transaction(self):
        from test_reference_assembly import configuration
        from truss.assembly import create_reference_assembly,HostServices,RecoveryServiceRegistration
        class Trap:
            def __getattribute__(self,name):raise AssertionError('Unexpected host service callback')
        cfg=configuration()
        services=HostServices(recovery_registry=RecoveryServiceRegistration(
            profile=cfg.recovery.registry_profile,retention='process_lifetime',implementation=Trap()))
        s=self.host.session
        a=create_reference_assembly(cfg,s.executor,services).value
        b=create_reference_assembly(configuration('sibling'),s.executor,services).value
        s.observe_host_resource_baseline();s.begin()
        tx=s.adopt_transaction().value
        a.dispose()
        self.assertEqual(b.observe_readiness(cfg.capabilities[0]).value.state,'unverified')
        self.assertIsInstance(s.savepoint(tx),Ok)
        self.assertEqual(s.rollback().value.state,'rolled_back')
        self.assertIsInstance(s.begin(),Ok)
        b.dispose()
        self.assertEqual(s.commit().value.state,'committed')
