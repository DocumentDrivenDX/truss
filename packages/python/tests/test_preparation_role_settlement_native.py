# SPDX-License-Identifier: MIT OR Apache-2.0
"""Basic stock PG18 role-writer settlement check; not full authority closure."""
from importlib.resources import files
from pathlib import Path
import tempfile
import unittest
import psycopg
from truss import LocalPostgres


class PreparationRoleSettlementNativeTests(unittest.TestCase):
    def test_pending_role_writers_and_fresh_catalog_cut_exclude_each_other(self):
        with tempfile.TemporaryDirectory(prefix='truss-role-settlement-') as directory:
            with LocalPostgres(Path(directory)/'data') as runtime:
                with psycopg.connect(runtime.info.connection_uri,autocommit=True) as writer, psycopg.connect(runtime.info.connection_uri,autocommit=True) as reader:
                    writer.execute('CREATE SCHEMA truss;CREATE TABLE truss.module_access(dummy integer);CREATE ROLE cut_member NOLOGIN;CREATE ROLE cut_target NOLOGIN')
                    writer.execute(files('truss').joinpath('_security_bootstrap','preparation-authority-lock.sql').read_text())
                    cases = [
                        (None,'ALTER ROLE cut_member CONNECTION LIMIT 7','pg_authid'),
                        ('REVOKE cut_target FROM cut_member','GRANT cut_target TO cut_member','pg_auth_members'),
                        ('GRANT cut_target TO cut_member','REVOKE cut_target FROM cut_member','pg_auth_members'),
                    ]
                    for setup, command, catalog in cases:
                        with self.subTest(command=command):
                            if setup: writer.execute(setup)
                            writer.execute('BEGIN')
                            try:
                                writer.execute(command)
                                # Observe the granted lock after the statement
                                # returns, while its transaction is uncommitted.
                                held = reader.execute("SELECT EXISTS(SELECT 1 FROM pg_catalog.pg_locks WHERE pid=%s AND locktype='relation' AND relation=to_regclass(%s) AND mode='RowExclusiveLock' AND granted)",(writer.info.backend_pid,'pg_catalog.'+catalog)).fetchone()[0]
                                self.assertTrue(held)
                                reader.execute('BEGIN')
                                try:
                                    reader.execute("SET LOCAL lock_timeout='1ms'")
                                    with self.assertRaises(psycopg.errors.LockNotAvailable):
                                        reader.execute('SELECT truss.acquire_preparation_authority_lock()')
                                finally:
                                    reader.execute('ROLLBACK')
                            finally:
                                writer.execute('ROLLBACK')
                            reader.execute('BEGIN')
                            try:
                                reader.execute("SET LOCAL lock_timeout='1ms'")
                                reader.execute('SELECT truss.acquire_preparation_authority_lock()')
                                writer.execute('BEGIN')
                                try:
                                    writer.execute("SET LOCAL lock_timeout='1ms'")
                                    with self.assertRaises(psycopg.errors.LockNotAvailable):
                                        writer.execute(command)
                                finally:
                                    writer.execute('ROLLBACK')
                            finally:
                                reader.execute('ROLLBACK')
