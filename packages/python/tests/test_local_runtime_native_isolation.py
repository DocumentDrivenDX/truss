# SPDX-License-Identifier: MIT OR Apache-2.0
"""Native Unix checks for isolated local PostgreSQL clusters."""
from pathlib import Path
import os
import stat
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import psutil

from truss import LocalPostgres


def query(runtime, sql):
    return subprocess.check_output(
        [str(runtime.psql_path), runtime.info.connection_uri, '-X', '-q', '-A', '-t',
         '-v', 'ON_ERROR_STOP=1', '-c', sql], text=True, timeout=30).strip()


def tcp_listeners(pid):
    """Return TCP listeners owned by the cluster postmaster process."""
    process = psutil.Process(pid)
    return [connection for connection in process.net_connections(kind='tcp')
            if connection.status == psutil.CONN_LISTEN]


class LocalRuntimeNativeIsolationTests(unittest.TestCase):
    @unittest.skipUnless(os.name == 'posix', 'the isolated local runtime requires Unix-domain sockets')
    def test_parallel_private_clusters_are_unix_only_and_retain_separate_data(self):
        with tempfile.TemporaryDirectory(prefix='truss-native-isolation-', dir='/tmp') as root:
            root_path = Path(root)
            first_dir = root_path / 'first'
            # A deliberately long data path exercises the separate short socket path.
            long_dir = root_path / ('segment-' + 'a' * 43) / ('segment-' + 'b' * 43) / 'second'
            self.assertGreater(len(str(long_dir)), 120)

            # Poison libpq's ambient defaults. The runtime and its explicit URI must
            # continue to select each cluster's private Unix socket.
            poisoned_pg_env = {
                'PGHOST': '127.0.0.1', 'PGPORT': '1', 'PGDATABASE': 'missing_host_db',
                'PGUSER': 'missing_host_user', 'PGPASSWORD': 'must-not-be-used',
            }
            with patch.dict(os.environ, poisoned_pg_env):
                with LocalPostgres(first_dir) as first:
                    with LocalPostgres(long_dir) as second:
                        first_socket_dir = first.info.socket_directory
                        second_socket_dir = second.info.socket_directory
                        self.assertEqual(first.info.server_version, '18.6')
                        self.assertEqual(second.info.server_version, '18.6')
                        self.assertEqual(first.info.port, second.info.port)
                        self.assertEqual(first.info.port, 5432)
                        self.assertNotEqual(first.info.socket_directory, second.info.socket_directory)

                        for runtime in (first, second):
                            self.assertEqual(query(runtime, 'SHOW listen_addresses'), '')
                            self.assertEqual(query(runtime, 'SHOW port'), '5432')
                            data_dir = runtime.info.data_directory
                            socket_dir = runtime.info.socket_directory
                            self.assertEqual(stat.S_IMODE(data_dir.stat().st_mode), 0o700)
                            self.assertEqual(stat.S_IMODE(socket_dir.stat().st_mode), 0o700)
                            self.assertLess(len(str(socket_dir / '.s.PGSQL.5432')), 104)
                            socket_path = socket_dir / '.s.PGSQL.5432'
                            socket_mode = socket_path.stat().st_mode
                            self.assertTrue(stat.S_ISSOCK(socket_mode), socket_path)
                            self.assertEqual(stat.S_IMODE(socket_mode), 0o700)
                            pid = int((data_dir / 'postmaster.pid').read_text().splitlines()[0])
                            self.assertEqual(tcp_listeners(pid), [])

                        self.assertNotEqual(first.info.socket_directory.name, second.info.socket_directory.name)
                        self.assertEqual((first.info.socket_directory / '.s.PGSQL.5432').name,
                                         (second.info.socket_directory / '.s.PGSQL.5432').name)

                        query(first, "CREATE TABLE isolation_probe(value text); INSERT INTO isolation_probe VALUES ('first-only');")
                        query(second, "CREATE TABLE isolation_probe(value text); INSERT INTO isolation_probe VALUES ('second-only');")
                        self.assertEqual(query(first, 'SELECT value FROM isolation_probe'), 'first-only')
                        self.assertEqual(query(second, 'SELECT value FROM isolation_probe'), 'second-only')

            self.assertFalse((first_dir / 'postmaster.pid').exists())
            self.assertFalse((long_dir / 'postmaster.pid').exists())
            # A retained config must not redirect the first lifecycle into the
            # second instance's durable state, even though both belong to us.
            with (first_dir / 'postgresql.conf').open('a') as config:
                config.write("\ndata_directory = '" + str(long_dir) + "'\n")
            with LocalPostgres(first_dir) as first_restarted, LocalPostgres(long_dir) as second_restarted:
                self.assertEqual(Path(query(first_restarted, 'SHOW data_directory')).resolve(), first_dir.resolve())
                self.assertEqual(query(first_restarted, 'SELECT value FROM isolation_probe'), 'first-only')
                self.assertEqual(query(second_restarted, 'SELECT value FROM isolation_probe'), 'second-only')
                self.assertEqual(first_restarted.info.socket_directory, first_socket_dir)
                self.assertEqual(second_restarted.info.socket_directory, second_socket_dir)


if __name__ == '__main__':
    unittest.main()
