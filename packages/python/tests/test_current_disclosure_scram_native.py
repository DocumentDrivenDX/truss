"""Explicit isolated SCRAM caller extension of the native disclosure campaign.

Both TRUSS_DISCLOSURE_NATIVE_QUALIFICATION=1 and
TRUSS_DISCLOSURE_SCRAM_QUALIFICATION=1 are required. No shared server is used.
The original fixture binding remains unadmitted: authentication alone does not
qualify native binding/current authority or complete the original132 cases.
"""
import os,secrets,time,unittest
from pathlib import Path
import psycopg
from psycopg import sql
import test_current_disclosure_runtime_native as base
from truss import (Ok,adopt_psycopg_host,create_reference_assembly,CatalogRuntimeConfiguration)

_ENABLED=(os.environ.get('TRUSS_DISCLOSURE_NATIVE_QUALIFICATION')=='1'
          and os.environ.get('TRUSS_DISCLOSURE_SCRAM_QUALIFICATION')=='1')


@unittest.skipUnless(_ENABLED,'requires serialized explicit isolated SCRAM native campaign')
class CurrentDisclosureScramNativeTests(base.CurrentDisclosureRuntimeNativeTests):
    def setUp(self):
        super().setUp()
        # Reconfigure only this test's newly created local role/server before
        # adopting the fresh bootstrap transaction. Never print the credential.
        self.host.detach();self.admin.rollback()
        self._caller_password=secrets.token_urlsafe(32)
        self.admin.execute("SET password_encryption='scram-sha-256'")
        self.admin.execute(sql.SQL('ALTER ROLE consumer PASSWORD {}').format(sql.Literal(self._caller_password)))
        self.assertEqual(self.admin.execute("SELECT rolpassword LIKE 'SCRAM-SHA-256$%' FROM pg_authid WHERE rolname='consumer'").fetchone(),(True,))
        hba=Path(self.admin.execute('SHOW hba_file').fetchone()[0]).resolve()
        self.assertTrue(hba.is_relative_to(self.root.resolve()),'HBA must belong to the isolated class server')
        original=hba.read_bytes();self.assertLessEqual(len(original),1048576)
        def restore():
            hba.write_bytes(original)
            self.assertEqual(hba.read_bytes(),original)
            self.assertEqual(self.admin.execute('SELECT pg_reload_conf()').fetchone(),(True,))
        self.addCleanup(restore)
        before=self.admin.execute('SELECT pg_conf_load_time()').fetchone()[0]
        hba.write_bytes(b'local all consumer scram-sha-256\n'+original)
        self.assertEqual(self.admin.execute('SELECT pg_reload_conf()').fetchone(),(True,))
        end=time.monotonic()+5
        while self.admin.execute('SELECT pg_conf_load_time()').fetchone()[0]<=before:
            if time.monotonic()>=end:self.fail('Isolated HBA reload did not complete')
            time.sleep(.01)
        self.assertEqual(self.admin.execute('SELECT count(*) FROM pg_hba_file_rules WHERE error IS NOT NULL').fetchone(),(0,))
        params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri)
        params.update(user='consumer',password=secrets.token_urlsafe(32),connect_timeout=5)
        with self.assertRaises(psycopg.OperationalError) as refused:
            psycopg.connect(**params)
        # psycopg's libpq connection-failure wrapper may have no PGresult
        # SQLSTATE. Require the native authentication failure itself as well.
        self.assertIn(refused.exception.sqlstate,(None,'28P01'))
        self.assertIn('password authentication failed for user "consumer"',str(refused.exception))
        self.assertEqual(self.admin.execute('SELECT type,user_name,auth_method FROM pg_hba_file_rules WHERE line_number=1').fetchone(),('local',['consumer'],'scram-sha-256'))
        params['password']=self._caller_password
        with psycopg.connect(**params,autocommit=True) as authenticated:
            self.assertEqual(authenticated.execute('SELECT session_user,current_user').fetchone(),('consumer','consumer'))
            self.assertEqual(authenticated.info.server_version,180006)
        self.admin.execute('BEGIN')
        self.host=adopt_psycopg_host(self.admin,statement_timeout_ms=10000,operation_timeout_ms=30000)
        self.addCleanup(self.host.detach)
        self.tx=self.host.adopt_transaction().value
        assembled=create_reference_assembly(CatalogRuntimeConfiguration(),self.host)
        self.assertIsInstance(assembled,Ok);self.assembly=assembled.value

    def consumer(self):
        params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri)
        params.update(user='consumer',password=self._caller_password,connect_timeout=5)
        connection=psycopg.connect(**params,autocommit=True,options='-c statement_timeout=10000')
        self.addCleanup(connection.close);connection.execute('BEGIN')
        self.assertEqual(connection.execute('SELECT session_user,current_user').fetchone(),('consumer','consumer'))
        host=adopt_psycopg_host(connection,statement_timeout_ms=10000,operation_timeout_ms=30000)
        self.addCleanup(host.detach);self.consumer_connections.append((connection,host))
        assembly=create_reference_assembly(CatalogRuntimeConfiguration(),host).value
        return connection,host,assembly,host.adopt_transaction().value

    def test_scram_credential_control(self):
        # setUp has already proved incorrect-credential refusal and successful
        # authentication by the same enrolled native role on the owned server.
        self.assertTrue(self._caller_password)
