"""Atomic original call bookkeeping; not native admission authority."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from truss._native_arbitration import NativeOperationSession, _OperationCall, _OperationCallRoot


class NativeCallRootTests(unittest.TestCase):
    def session(self):
        return NativeOperationSession(None, None, None, None, None, b'component', 8)

    def test_generic_cleanup_rebases_all_containment_branches(self):
        session = self.session()
        rollback = _OperationCall(0, None, None)
        release = _OperationCall(0, None, None)
        session._call_root = _OperationCallRoot.build((), (), rollback, release)
        boundary = SimpleNamespace(_revision=4)
        with patch.object(NativeOperationSession, '_check_call'):
            entry = session._reserve_call(boundary, None, object(), None, object())
        root = session._call_root
        self.assertEqual(root.cleanup_calls, (entry,))
        self.assertEqual(root.rollback_root, (entry, rollback))
        self.assertEqual(root.rollback_release_root, (entry, rollback, release))
        self.assertEqual(root.release_root, (entry, release))
        self.assertEqual(root.held_cleanup, 2)
        self.assertIsNone(rollback.native_call)
        self.assertIsNone(release.native_call)

    def test_allocation_failure_preserves_original_containment(self):
        session = self.session()
        rollback = _OperationCall(0, None, None)
        release = _OperationCall(0, None, None)
        previous = _OperationCallRoot.build((), (), rollback, release)
        session._call_root = previous
        with patch.object(NativeOperationSession, '_check_call'), patch.object(
                _OperationCallRoot, 'build', side_effect=MemoryError('root allocation')):
            with self.assertRaises(MemoryError):
                session._reserve_call(SimpleNamespace(_revision=4), None, None, None, object())
        self.assertIs(session._call_root, previous)
        self.assertEqual(session.cleanup_calls, ())

    def test_lost_publication_retains_entry_and_rebased_branches_together(self):
        session = self.session()
        rollback = _OperationCall(0, None, None)
        release = _OperationCall(0, None, None)
        previous = _OperationCallRoot.build((), (), rollback, release)
        session._call_root = previous
        original = NativeOperationSession._publish_call_root
        def lost(owner, root):
            original(owner, root)
            raise MemoryError('publication reply lost')
        with patch.object(NativeOperationSession, '_check_call'), patch.object(
                NativeOperationSession, '_publish_call_root', lost):
            with self.assertRaises(MemoryError):
                session._reserve_call(SimpleNamespace(_revision=4), None, None, None, object())
        root = session._call_root
        self.assertIsNot(root, previous)
        self.assertEqual(len(root.cleanup_calls), 1)
        self.assertEqual(root.rollback_release_root, (*root.cleanup_calls, rollback, release))
        self.assertEqual(root.release_root, (*root.cleanup_calls, release))


    def test_boundary_closes_after_lost_cleanup_publication_without_native_fact(self):
        from threading import Lock
        from truss._native_pg8000 import NativeBoundary, NativeBoundaryRefusal, _Ownership
        for after in (False, True):
            session = self.session()
            boundary = object.__new__(NativeBoundary)
            boundary._ownership = _Ownership(ledger=session, pending=session)
            boundary._lock = Lock()
            boundary._quarantined = False
            boundary._cancel_pending = None
            boundary._calling = False
            boundary._host_control_pending = None
            boundary._revision = 0
            boundary._transaction_tracker = None
            invoked = []
            original = NativeOperationSession._publish_call_root
            def lost(owner, root):
                if after:
                    original(owner, root)
                raise MemoryError('publication reply lost')
            with patch.object(NativeOperationSession, '_check_call'), patch.object(
                    NativeOperationSession, '_publish_call_root', lost):
                with self.assertRaises(MemoryError):
                    boundary._call(lambda: invoked.append(True), cleanup=object())
            self.assertEqual(invoked, [])
            self.assertEqual(boundary._revision, 0)
            self.assertEqual(boundary._quarantined, after)
            self.assertEqual(session.admission_closed, after)
            if after:
                self.assertIsNone(session.cleanup_calls[0].native_call)
                with self.assertRaises(NativeBoundaryRefusal):
                    boundary._call(lambda: invoked.append(True))
                self.assertEqual(invoked, [])


    def test_post_reservation_setup_fault_cannot_reuse_unsent_cleanup_entry(self):
        from threading import Lock
        from truss._native_pg8000 import NativeBoundary, NativeBoundaryRefusal, _Ownership
        session = self.session()
        boundary = object.__new__(NativeBoundary)
        boundary._ownership = _Ownership(ledger=session, pending=session)
        boundary._lock = Lock()
        boundary._quarantined = False
        boundary._cancel_pending = None
        boundary._calling = False
        boundary._host_control_pending = None
        boundary._revision = 0
        boundary._transaction_tracker = None
        # Original run-method lookup fails after call-root publication.
        boundary._connection = object()
        invoked = []
        with patch.object(NativeOperationSession, '_check_call'):
            with self.assertRaises(AttributeError):
                boundary._call(lambda: invoked.append(True), cleanup=object())
        self.assertTrue(boundary._quarantined)
        self.assertTrue(session.admission_closed)
        self.assertEqual(len(session.cleanup_calls), 1)
        self.assertIsNone(session.cleanup_calls[0].native_call)
        self.assertEqual(invoked, [])
        with self.assertRaises(NativeBoundaryRefusal):
            boundary._call(lambda: invoked.append(True))
        self.assertEqual(invoked, [])


if __name__ == '__main__':
    unittest.main()
