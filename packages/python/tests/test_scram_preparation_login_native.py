# SPDX-License-Identifier: MIT OR Apache-2.0
"""Actual SCRAM exchange under explicit disposable HBA; no human admission."""
from pathlib import Path
import secrets
import time
import unittest
from unittest.mock import patch
import os
import tempfile
import psycopg
from psycopg import sql
import test_catalog_runtime_native as base
from truss._scram_preparation_login import ScramPreparationLogin


class ScramPreparationLoginNativeTests(base.PublicCatalogRuntimeTests):
    for name in tuple(n for n in dir(base.PublicCatalogRuntimeTests) if n.startswith('test_')):
        locals()[name] = None

    def test_required_scram_rejects_wrong_absent_and_trust_authentication(self):
        self.host.detach(); self.admin.rollback()
        password = secrets.token_urlsafe(32)
        self.admin.execute("SET password_encryption='scram-sha-256'")
        self.admin.execute(sql.SQL('ALTER ROLE consumer PASSWORD {}').format(sql.Literal(password)))
        params = psycopg.conninfo.conninfo_to_dict(self.info.connection_uri)
        provider = ScramPreparationLogin(params['host'], int(params.get('port', '5432')),
            params.get('dbname', params.get('user', 'postgres')), 'consumer', password)
        self.assertNotIn(password, repr(provider))
        # Current default trust HBA must not pass the provider's libpq
        # require_auth contract even though a password was supplied.
        with self.assertRaises(ValueError):
            provider.open_connection()
        hba = Path(self.admin.execute('SHOW hba_file').fetchone()[0])
        original = hba.read_bytes()
        try:
            hba.write_bytes(b'local all consumer scram-sha-256\n' + original)
            before = self.admin.execute('SELECT pg_catalog.pg_conf_load_time()').fetchone()[0]
            self.assertEqual(self.admin.execute('SELECT pg_catalog.pg_reload_conf()').fetchone(), (True,))
            deadline = time.monotonic() + 5
            while self.admin.execute('SELECT pg_catalog.pg_conf_load_time()').fetchone()[0] == before:
                if time.monotonic() >= deadline:
                    self.fail('Original HBA reload was not observed')
                time.sleep(.01)
            self.assertEqual(self.admin.execute('SELECT type,user_name,auth_method,error FROM pg_catalog.pg_hba_file_rules ORDER BY rule_number LIMIT 1').fetchone(), ('local', ['consumer'], 'scram-sha-256', None))
            self.assertEqual(self.admin.execute("SELECT rolpassword LIKE 'SCRAM-SHA-256$%' FROM pg_catalog.pg_authid WHERE rolname='consumer'").fetchone(), (True,))
            with self.assertRaises(ValueError):
                ScramPreparationLogin(provider.socket_directory, provider.port,
                    provider.database, provider.native_login, secrets.token_urlsafe(32)).open_connection()
            with self.assertRaises(ValueError):
                ScramPreparationLogin(provider.socket_directory, provider.port,
                    provider.database, provider.native_login, '').open_connection()
            # Exercise actual absent credentials as well as provider preflight;
            # exclude ambient password/passfile fallback from this witness.
            with patch.dict(os.environ, {}, clear=True), tempfile.NamedTemporaryFile() as empty_passfile:
                with self.assertRaises(psycopg.OperationalError):
                    psycopg.connect(host=provider.socket_directory,port=provider.port,
                        dbname=provider.database,user=provider.native_login,
                        passfile=empty_passfile.name,require_auth='scram-sha-256',connect_timeout=5)
            with provider.open_connection() as connection:
                self.assertTrue(connection.pgconn.used_password)
                self.assertEqual(connection.execute('SELECT current_user,session_user').fetchone(), ('consumer', 'consumer'))
                self.assertNotEqual(connection.info.backend_pid, self.admin.info.backend_pid)
        finally:
            hba.write_bytes(original)
            self.admin.execute('SELECT pg_catalog.pg_reload_conf()')
