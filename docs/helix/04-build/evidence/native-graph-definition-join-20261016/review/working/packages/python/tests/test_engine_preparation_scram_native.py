"""One native SCRAM connection through pre-RR capture, RR and COMMIT."""
from pathlib import Path
import secrets
import time
import psycopg
from psycopg import sql
import test_catalog_runtime_native as base
from truss import Ok
from truss._scram_preparation_login import ScramPreparationLogin
from truss._engine_preparation import _EnginePreparationSession


class EnginePreparationScramNativeTests(base.PublicCatalogRuntimeTests):
    for name in tuple(n for n in dir(base.PublicCatalogRuntimeTests) if n.startswith('test_')):
        locals()[name]=None

    def test_original_scram_connection_survives_prephase_rr_and_commit(self):
        self.host.detach();self.admin.rollback()
        password=secrets.token_urlsafe(32)
        self.admin.execute("SET password_encryption='scram-sha-256'")
        self.admin.execute(sql.SQL('ALTER ROLE consumer PASSWORD {}').format(sql.Literal(password)))
        params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri)
        login=ScramPreparationLogin(params['host'],int(params.get('port','5432')),
            params.get('dbname',params.get('user','postgres')),'consumer',password)
        hba=Path(self.admin.execute('SHOW hba_file').fetchone()[0]);original=hba.read_bytes()
        session=_EnginePreparationSession.from_scram_login(login,10000,30000)
        try:
            hba.write_bytes(b'local all consumer scram-sha-256\n'+original)
            before=self.admin.execute('SELECT pg_catalog.pg_conf_load_time()').fetchone()[0]
            self.admin.execute('SELECT pg_catalog.pg_reload_conf()')
            deadline=time.monotonic()+5
            while self.admin.execute('SELECT pg_catalog.pg_conf_load_time()').fetchone()[0]==before:
                if time.monotonic()>=deadline:self.fail('Original HBA reload not observed')
                time.sleep(.01)
            cap=session.prepare_connection()
            self.assertIsNone(session._scram_login)
            self.assertTrue(session.connection.pgconn.used_password)
            original_connection=session.connection;pid=original_connection.info.backend_pid
            def identity(cursor):
                cursor.execute('SELECT session_user::pg_catalog.text,current_user::pg_catalog.text,pg_catalog.pg_backend_pid()::pg_catalog.text',prepare=False)
                return cursor.fetchmany(2)
            self.assertEqual(session.capture_before_snapshot(cap,identity),[('consumer','consumer',str(pid))])
            host,tx=session.begin()
            observed=session.run_operation(lambda cursor,context:identity(cursor))
            self.assertIsInstance(observed,Ok)
            self.assertEqual(observed.value,[('consumer','consumer',str(pid))])
            self.assertIs(session.connection,original_connection)
            committed,rolled_back=object(),object()
            settled,error=session.complete(commit=True,committed=committed,rolled_back=rolled_back)
            self.assertIs(settled,committed);self.assertIsNone(error)
            self.assertEqual(session.completion_observation().disposition,'committed')
            with self.assertRaises(ValueError):session.begin()
        finally:
            session.close()
            hba.write_bytes(original);self.admin.execute('SELECT pg_catalog.pg_reload_conf()')
