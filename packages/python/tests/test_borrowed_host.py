# SPDX-License-Identifier: MIT OR Apache-2.0
"""Borrowed native host controls and original hook restoration."""
import unittest
from unittest.mock import patch
from threading import Thread,Event
import socket
from test_native_pg8000 import NativeBoundaryFixture
from truss import adopt_pg8000_host,BorrowedHostAttachmentFailure,Ok,Error
from truss._native_attachment import DriverAttachment
from truss._native_pg8000 import NativeBoundaryRefusal


class BorrowedHostTests(NativeBoundaryFixture,unittest.TestCase):
    def setUp(self):
        self.raw=self.Connection(**self.kwargs)
        self.raw.run('SELECT 1')
        self.host=None

    def tearDown(self):
        if self.host is not None and self.host._attachment.phase!='detached':
            self.host.session.rollback()
            self.host.detach()
        if self.raw._sock is not None:self.raw.close()

    def test_real_host_transaction_and_raw_reuse(self):
        self.host=adopt_pg8000_host(self.raw)
        session=self.host.session
        self.host.connection.run_non_lifecycle('SELECT 1')
        self.assertIsInstance(session.observe_host_resource_baseline(),Ok)
        self.assertIsInstance(session.begin(),Ok)
        tx=session.adopt_transaction().value
        self.host.connection.run_non_lifecycle('CREATE TEMP TABLE borrowed_host_work(value text)')
        self.host.connection.run_non_lifecycle("INSERT INTO borrowed_host_work VALUES('before')")
        sp=session.savepoint(tx).value
        self.host.connection.run_non_lifecycle("INSERT INTO borrowed_host_work VALUES('after')")
        self.assertIsInstance(session.rollback_to_savepoint(tx,sp),Ok)
        self.assertIsInstance(session.release_savepoint(tx,sp),Ok)
        self.assertFalse(self.host.detach())
        self.assertEqual(session.commit().value.state,'committed')
        self.assertTrue(self.host.detach())
        self.assertTrue(self.host.detach())
        self.assertEqual(self.raw.run('SELECT value FROM borrowed_host_work'),[['before']])
        self.assertIsInstance(session.savepoint(tx),Error)
        self.assertIsInstance(session.begin(),Error)

    def test_active_failed_closed_and_already_attached_refuse(self):
        for command in ('BEGIN','BEGIN; SELECT 1/0'):
            try:self.raw.run(command)
            except Exception:pass
            handlers=dict(self.raw.message_types)
            with self.assertRaises(NativeBoundaryRefusal):adopt_pg8000_host(self.raw)
            self.assertEqual(self.raw.message_types,handlers)
            self.assertFalse(hasattr(self.raw,'_truss_native_boundary'))
            self.raw.run('ROLLBACK')
        self.host=adopt_pg8000_host(self.raw)
        with self.assertRaises(NativeBoundaryRefusal):adopt_pg8000_host(self.raw)
        self.assertTrue(self.host.detach())
        self.raw.close()
        with self.assertRaises(NativeBoundaryRefusal):adopt_pg8000_host(self.raw)

    def test_changed_driver_refuses_without_attachment(self):
        original=self.raw.message_types[b'N']
        self.raw.message_types[b'N']=lambda *args:None
        with self.assertRaises(NativeBoundaryRefusal):adopt_pg8000_host(self.raw)
        self.assertFalse(hasattr(self.raw,'_truss_native_boundary'))
        self.raw.message_types[b'N']=original
        self.assertEqual(self.raw.run('SELECT 7'),[[7]])

    def test_substituted_extended_handlers_and_extra_dispatch_refuse(self):
        for code in (b'1',b'2',b'3'):
            with self.subTest(code=code):
                original=self.raw.message_types[code]
                self.raw.message_types[code]=lambda *args:None
                try:
                    with self.assertRaises(NativeBoundaryRefusal):adopt_pg8000_host(self.raw)
                    self.assertFalse(hasattr(self.raw,'_truss_native_boundary'))
                finally:self.raw.message_types[code]=original
        self.raw.message_types[b'?']=lambda *args:None
        try:
            with self.assertRaises(NativeBoundaryRefusal):adopt_pg8000_host(self.raw)
            self.assertFalse(hasattr(self.raw,'_truss_native_boundary'))
        finally:del self.raw.message_types[b'?']

    def test_unselected_transport_refuses_before_attachment(self):
        original_socket=self.raw._usock
        other=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        try:
            self.raw._usock=other
            with self.assertRaises(NativeBoundaryRefusal):adopt_pg8000_host(self.raw)
            self.assertFalse(hasattr(self.raw,'_truss_native_boundary'))
        finally:self.raw._usock=original_socket;other.close()
        timeout=original_socket.gettimeout()
        try:
            original_socket.settimeout(0)
            with self.assertRaises(NativeBoundaryRefusal):adopt_pg8000_host(self.raw)
            self.assertFalse(hasattr(self.raw,'_truss_native_boundary'))
        finally:original_socket.settimeout(timeout)
        self.assertEqual(self.raw.run('SELECT 7'),[[7]])

    def test_every_publication_failure_restores_original_connection(self):
        original=DriverAttachment._publish
        points=('handlers','_truss_native_boundary','send_PARSE','close_prepared_statement','send_BIND')
        for point in points:
            for after in (False,True):
                with self.subTest(point=point,after=after):
                    handlers=dict(self.raw.message_types)
                    def fail(record,name,callback):
                        if name==point and not after:raise MemoryError('publication')
                        original(record,name,callback)
                        if name==point and after:raise MemoryError('publication')
                    with patch.object(DriverAttachment,'_publish',fail):
                        with self.assertRaises(BorrowedHostAttachmentFailure) as caught:
                            adopt_pg8000_host(self.raw)
                    self.assertTrue(caught.exception.restored)
                    self.assertEqual(self.raw.message_types,handlers)
                    self.assertFalse(hasattr(self.raw,'_truss_native_boundary'))
                    self.assertEqual(self.raw.run('SELECT 7'),[[7]])

    def test_foreign_replacement_retains_unresolved_custody(self):
        original=DriverAttachment._publish
        foreign=lambda *args:None
        def fail(record,name,callback):
            original(record,name,callback)
            if name=='send_BIND':
                record.connection.send_BIND=foreign
                raise MemoryError('foreign replacement')
        with patch.object(DriverAttachment,'_publish',fail):
            with self.assertRaises(BorrowedHostAttachmentFailure) as caught:adopt_pg8000_host(self.raw)
        error=caught.exception
        self.assertFalse(error.restored)
        self.assertIs(self.raw.send_BIND,foreign)
        self.assertTrue(error.attachment.boundary._quarantined)
        with self.assertRaises(NativeBoundaryRefusal):adopt_pg8000_host(self.raw)
        # Trusted test cleanup restores the known original ownership, no SQL.
        self.raw.send_BIND=error.attachment.boundary._bind_entry
        self.assertTrue(error.attachment.restore())

    def test_busy_detach_and_dispose_preserve_host_rollback(self):
        self.host=adopt_pg8000_host(self.raw)
        session=self.host.session
        self.host.connection.run_non_lifecycle('SELECT 1')
        self.assertIsInstance(session.observe_host_resource_baseline(),Ok)
        self.assertIsInstance(session.begin(),Ok)
        self.host.dispose()
        self.assertFalse(self.host.detach())
        self.assertEqual(session.rollback().value.state,'rolled_back')
        session._lock.acquire()
        try:self.assertFalse(self.host.detach())
        finally:session._lock.release()
        self.assertTrue(self.host.detach())
        self.assertEqual(self.raw.run('SELECT 7'),[[7]])

    def test_connection_close_requires_explicit_detach(self):
        self.host=adopt_pg8000_host(self.raw)
        with self.assertRaises(NativeBoundaryRefusal):self.host.connection.close()
        self.assertTrue(self.host.detach())
        self.assertEqual(self.raw.run('SELECT 7'),[[7]])

    def test_subclass_refuses_before_mutation(self):
        class OtherConnection(self.Connection):pass
        con=OtherConnection(**self.kwargs)
        try:
            con.run('SELECT 1')
            with self.assertRaises(NativeBoundaryRefusal):adopt_pg8000_host(con)
            self.assertFalse(hasattr(con,'_truss_native_boundary'))
            self.assertEqual(con.run('SELECT 7'),[[7]])
        finally:con.close()

    def test_concurrent_attachment_has_one_owner(self):
        start=Event();results=[]
        def attach():
            start.wait()
            try:results.append(adopt_pg8000_host(self.raw))
            except (NativeBoundaryRefusal,BorrowedHostAttachmentFailure):results.append(None)
        threads=[Thread(target=attach) for _ in range(2)]
        for thread in threads:thread.start()
        start.set()
        for thread in threads:thread.join(timeout=3);self.assertFalse(thread.is_alive())
        owners=[result for result in results if result is not None]
        self.assertEqual(len(results),2)
        self.assertEqual(len(owners),1)
        self.host=owners[0]
        self.assertTrue(self.host.detach())

    def test_detach_refuses_during_mediated_call(self):
        self.host=adopt_pg8000_host(self.raw)
        entered=Event();release=Event();results=[]
        boundary=self.host._attachment.boundary
        original=boundary._call
        def run(invoke,*args,**kwargs):
            def delayed():
                entered.set()
                if not release.wait(timeout=3):raise RuntimeError('test release absent')
                return invoke()
            return original(delayed,*args,**kwargs)
        def call():results.append(self.host.connection.run_non_lifecycle('SELECT CAST(:value AS int)',value=7))
        with patch.object(boundary,'_call',side_effect=run):
            thread=Thread(target=call);thread.start()
            try:
                self.assertTrue(entered.wait(timeout=3))
                self.assertFalse(self.host.detach())
            finally:release.set();thread.join(timeout=3)
        self.assertFalse(thread.is_alive())
        self.assertEqual(results,[[[7]]])
        self.assertTrue(self.host.detach())

    def test_changed_hooks_refuse_detachment_without_overwriting(self):
        self.host=adopt_pg8000_host(self.raw)
        original=self.raw.run
        self.raw.run=lambda *args:None
        self.assertFalse(self.host.detach())
        self.raw.run=original
        self.assertTrue(self.host.detach())

    def test_late_composition_failure_preserves_connection(self):
        with patch('truss._host_session.NativeHostSession',side_effect=MemoryError('late composition')):
            with self.assertRaises(BorrowedHostAttachmentFailure) as caught:adopt_pg8000_host(self.raw)
        self.assertTrue(caught.exception.restored)
        self.assertEqual(self.raw.run('SELECT 7'),[[7]])

    def test_cleanup_failure_retains_original_attachment(self):
        with patch('truss._host_session.NativeHostSession',side_effect=MemoryError('composition')):
            with patch.object(DriverAttachment,'restore',side_effect=MemoryError('cleanup')):
                with self.assertRaises(BorrowedHostAttachmentFailure) as caught:adopt_pg8000_host(self.raw)
        error=caught.exception
        self.assertFalse(error.restored)
        self.assertIs(self.raw._truss_native_boundary,error.attachment.boundary)
        self.assertTrue(error.attachment.boundary._quarantined)
        with self.assertRaises(NativeBoundaryRefusal):adopt_pg8000_host(self.raw)
        self.assertTrue(error.attachment.restore())
        self.assertEqual(self.raw.run('SELECT 7'),[[7]])

    def test_partial_detach_cleanup_can_be_retried_without_io(self):
        self.host=adopt_pg8000_host(self.raw)
        def partial(record):
            record.connection.message_types.update(record.handlers)
            record.phase='unresolved'
            raise MemoryError('partial hook restoration')
        with patch.object(DriverAttachment,'restore',partial):
            with self.assertRaises(MemoryError):self.host.detach()
        self.assertIsInstance(self.host.detach_failure,MemoryError)
        self.assertTrue(self.host._attachment.boundary._quarantined)
        self.assertIsInstance(self.host.session.begin(),Error)
        original_socket=self.raw._usock
        other=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        try:
            self.raw._usock=other
            self.assertFalse(self.host.detach())
            self.assertIs(self.raw._usock,other)
        finally:self.raw._usock=original_socket;other.close()
        self.assertTrue(self.host.detach())
        self.assertIsNone(self.host.detach_failure)
        self.assertEqual(self.raw.run('SELECT 7'),[[7]])

    def test_attachment_has_no_io_and_requires_original_mediated_baseline(self):
        before=self.raw._context
        self.host=adopt_pg8000_host(self.raw)
        self.assertIs(self.raw._context,before)
        self.assertIsNone(self.host._attachment.boundary.last_call)
        self.assertIsInstance(self.host.session.observe_host_resource_baseline(),Error)
        self.assertIsNone(self.host._attachment.boundary.last_call)
        self.host.connection.run_non_lifecycle('SELECT 1')
        self.assertIsInstance(self.host.session.observe_host_resource_baseline(),Ok)
        self.assertTrue(self.host.detach())
