"""Pinned resource capture against real files; no native install qualification."""
from hashlib import sha256
from pathlib import Path
import tempfile
import unittest
from truss._installation_resources import capture_resource
from truss._resource_account import BytePermitAccount


class ResourceCaptureTests(unittest.TestCase):
    def test_real_file_capture_retains_verified_bytes_after_change(self):
        producer = object(); account = BytePermitAccount(producer, 100, 100, 10)
        with tempfile.TemporaryDirectory() as directory:
            resource = Path(directory) / 'original.sql'
            original = b'SELECT 1;\n'; resource.write_bytes(original)
            captured = capture_resource(resource, len(original), sha256(original).hexdigest(), 100, account, producer)
            resource.write_bytes(b'SELECT 2;\n')
            self.assertEqual(captured.original, original)
            self.assertIs(captured.account, account)
            self.assertEqual(account.snapshot(producer), (len(original)+1, 0, len(original)+1, False))
            allocation = captured.allocation
            del captured
            account.release(producer, allocation)
            self.assertEqual(account.snapshot(producer), (0, 0, len(original)+1, False))

    def test_missing_changed_truncated_appended_resources_quarantine_once(self):
        original = b'original'; digest = sha256(original).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            resource = Path(directory) / 'input'
            for replacement in (None, b'origina', b'changed!', b'originalx'):
                with self.subTest(replacement=replacement):
                    if replacement is not None: resource.write_bytes(replacement)
                    producer = object(); account = BytePermitAccount(producer, 100, 100, 10)
                    with self.assertRaises((ValueError, FileNotFoundError)):
                        capture_resource(resource, len(original), digest, 100, account, producer)
                    self.assertEqual(account.snapshot(producer), (9, 0, 9, True))
                    with self.assertRaises(ValueError): account.reserve(producer, 1)

    def test_reservation_refusal_precedes_open_and_invalid_pin_is_inert(self):
        class Unopened:
            def open(self, mode): raise AssertionError('Must not open')
        producer = object(); account = BytePermitAccount(producer, 0, 0, 10)
        with self.assertRaises(ValueError):
            capture_resource(Unopened(), 0, sha256(b'').hexdigest(), 100, account, producer)
        self.assertEqual(account.snapshot(producer), (0, 0, 0, True))
        for length, digest in [(True, sha256(b'').hexdigest()), (0, 'A'*64), (101, '0'*64)]:
            account = BytePermitAccount(producer, 100, 100, 10)
            with self.assertRaises(ValueError):
                capture_resource(Unopened(), length, digest, 100, account, producer)
            self.assertEqual(account.snapshot(producer), (0, 0, 0, False))
