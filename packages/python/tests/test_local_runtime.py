"""Native component tests: owned lifecycle, refusal custody, retained commit."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from truss import LocalPostgres, LocalRuntimeError


def query(runtime, sql):
    return subprocess.check_output(
        [str(runtime.psql_path), runtime.info.connection_uri, '-X', '-q', '-A', '-t',
         '-v', 'ON_ERROR_STOP=1', '-c', sql], text=True, timeout=30).strip()


class LocalRuntimeTests(unittest.TestCase):
    def test_retained_commit_and_exception_cleanup(self):
        with tempfile.TemporaryDirectory(prefix='truss-python-runtime-') as parent:
            directory = Path(parent) / 'retained data'
            runtime = LocalPostgres(directory)
            with self.assertRaisesRegex(ValueError, 'caller failure'):
                with runtime:
                    self.assertEqual(runtime.info.server_version, '16.2')
                    self.assertEqual(runtime.info.truss_installation, 'not_checked')
                    self.assertEqual(query(runtime, "SELECT to_regnamespace('truss') IS NULL"), 't')
                    query(runtime, "CREATE TABLE persistence_probe(value text); INSERT INTO persistence_probe VALUES ('9223372036854775807');")
                    raise ValueError('caller failure')
            runtime.close()
            self.assertTrue((directory / 'PG_VERSION').exists())
            self.assertFalse((directory / 'postmaster.pid').exists())
            with self.assertRaises(LocalRuntimeError):
                _ = runtime.info
            with LocalPostgres(directory) as restarted:
                self.assertEqual(query(restarted, 'SELECT value FROM persistence_probe'), '9223372036854775807')

    def test_nested_directory_custody_and_independent_servers(self):
        with tempfile.TemporaryDirectory(prefix='truss-python-runtime-') as parent:
            directory = Path(parent) / 'one'
            with LocalPostgres(directory) as first:
                child = subprocess.run([sys.executable, '-c',
                    "from truss import LocalPostgres, LocalRuntimeError; import sys\n"
                    "try: LocalPostgres(sys.argv[1]).__enter__()\n"
                    "except LocalRuntimeError as e: print(str(e)); sys.exit(23)\n"
                    "sys.exit(0)", str(directory)], capture_output=True, text=True, timeout=30)
                self.assertEqual(child.returncode, 23, child.stderr)
                self.assertIn('leased by another process', child.stdout)
                rejected = LocalPostgres(directory)
                with self.assertRaisesRegex(LocalRuntimeError, 'already in use'):
                    rejected.__enter__()
                rejected.close()
                with self.assertRaisesRegex(LocalRuntimeError, 'already in use'):
                    LocalPostgres(directory).__enter__()
                with LocalPostgres(Path(parent) / 'two') as second:
                    self.assertNotEqual(first.info.connection_uri, second.info.connection_uri)
                    self.assertEqual(query(first, 'SELECT 1'), '1')
                    self.assertEqual(query(second, 'SELECT 2'), '2')
                self.assertEqual(query(first, 'SELECT 3'), '3')

    def test_failed_cleanup_retains_lease_until_explicit_recovery(self):
        with tempfile.TemporaryDirectory(prefix='truss-python-cleanup-') as parent:
            directory = Path(parent) / 'data'
            runtime = LocalPostgres(directory).__enter__()
            try:
                with patch.object(runtime._server, 'cleanup', side_effect=OSError('injected cleanup failure')) as cleanup:
                    with self.assertRaisesRegex(LocalRuntimeError, 'lease retained'):
                        runtime.close()
                    self.assertEqual(cleanup.call_count, 1)
                    with self.assertRaises(LocalRuntimeError):
                        _ = runtime.info
                    with self.assertRaisesRegex(LocalRuntimeError, 'already in use'):
                        LocalPostgres(directory).__enter__()
                with patch.object(runtime._server, 'cleanup', return_value=None) as cleanup:
                    with self.assertRaisesRegex(LocalRuntimeError, 'stop unconfirmed'):
                        runtime.close()
                    self.assertEqual(cleanup.call_count, 1)
                    with self.assertRaisesRegex(LocalRuntimeError, 'already in use'):
                        LocalPostgres(directory).__enter__()
                # Explicit host recovery, after removing the injected failure.
                runtime.close()
                self.assertFalse((directory / 'postmaster.pid').exists())
                with LocalPostgres(directory) as restarted:
                    self.assertEqual(query(restarted, 'SELECT 1'), '1')
            finally:
                runtime.close()

    def test_constructor_failure_with_postmaster_marker_retains_custody(self):
        # Synthetic constructor fault; this creates no native server/process.
        with tempfile.TemporaryDirectory(prefix='truss-python-startup-fault-') as parent:
            directory = Path(parent) / 'data'
            runtime = LocalPostgres(directory)
            def fail_startup(*args, **kwargs):
                directory.mkdir()
                (directory / 'PG_VERSION').write_text('16\n')
                (directory / 'postmaster.pid').write_text('synthetic unresolved marker\n')
                raise OSError('injected constructor failure')
            try:
                with patch('pgserver.get_server', side_effect=fail_startup) as startup:
                    with self.assertRaisesRegex(LocalRuntimeError, 'startup stop unconfirmed'):
                        runtime.__enter__()
                    self.assertEqual(startup.call_count, 1)
                with self.assertRaises(LocalRuntimeError):
                    _ = runtime.info
                with self.assertRaisesRegex(LocalRuntimeError, 'already in use'):
                    LocalPostgres(directory).__enter__()
                with self.assertRaisesRegex(LocalRuntimeError, 'lease retained'):
                    runtime.close()
                # Model explicit host recovery of the synthetic marker, not a
                # production rule to delete a live postmaster's custody file.
                (directory / 'postmaster.pid').unlink()
                runtime.close()
                with patch('pgserver.get_server', side_effect=OSError('before native startup')):
                    with self.assertRaisesRegex(OSError, 'before native startup'):
                        LocalPostgres(directory).__enter__()
            finally:
                if (directory / 'postmaster.pid').exists():
                    (directory / 'postmaster.pid').unlink()
                runtime.close()

    def test_nonempty_and_wrong_version_directories_refuse_unchanged(self):
        with tempfile.TemporaryDirectory(prefix='truss-python-refusal-') as parent:
            directory = Path(parent) / 'foreign'
            directory.mkdir()
            marker = directory / 'consumer-file'
            marker.write_text('retain me')
            with self.assertRaisesRegex(LocalRuntimeError, 'Nonempty'):
                with LocalPostgres(directory):
                    self.fail('foreign directory admitted')
            self.assertEqual(marker.read_text(), 'retain me')
            (directory / 'PG_VERSION').write_text('17\n')
            with self.assertRaisesRegex(LocalRuntimeError, 'no automatic upgrade'):
                with LocalPostgres(directory):
                    self.fail('incompatible version admitted')
            self.assertEqual((directory / 'PG_VERSION').read_text(), '17\n')


if __name__ == '__main__':
    unittest.main()
