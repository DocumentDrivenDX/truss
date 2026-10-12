"""Native role-setting evidence for profile selection, not facade qualification."""
from pathlib import Path
import unittest
import os
import shutil
import subprocess
import tempfile
import psycopg
from psycopg import sql

class RoleSettingTests(unittest.TestCase):
    @classmethod
    def run_pg(cls, name, *args):
        subprocess.run([str(cls.pgbin/name), *args], check=True,
                       capture_output=True, text=True, timeout=60)

    @classmethod
    def setUpClass(cls):
        cls.root = Path(tempfile.mkdtemp(prefix='truss-role-', dir='/tmp'))
        cls.data = cls.root/'data'
        cls.socket = cls.root/'socket'
        cls.pgbin = Path(os.environ['TRUSS_CENSUS_POSTGRES_BIN'])
        cls.database = 'postgres'
        cls.start_attempted = False
        cls.addClassCleanup(cls.cleanup_owned_server)
        cls.socket.mkdir()
        cls.run_pg('initdb', '-D', str(cls.data), '-U', 'postgres', '--auth=trust', '--encoding=UTF8')
        cls.start_attempted = True
        cls.run_pg('pg_ctl', '-D', str(cls.data), '-l', str(cls.root/'server.log'), '-w',
                   '-o', f"-h '' -k {cls.socket}", 'start')
        with psycopg.connect(host=str(cls.socket), user='postgres', dbname=cls.database) as conn:
            actual = conn.execute('SHOW server_version_num').fetchone()[0]
            if actual != '180006':
                raise RuntimeError(f'Expected PostgreSQL 180006, got {actual}')

    @classmethod
    def cleanup_owned_server(cls):
        if cls.start_attempted:
            try:
                cls.run_pg('pg_ctl', '-D', str(cls.data), '-w', '-m', 'immediate', 'stop')
            except Exception as error:
                raise RuntimeError(f'Shutdown unconfirmed; retained {cls.root}') from error
        shutil.rmtree(cls.root)

    def test_exact_names_and_reserved_none(self):
        with psycopg.connect(host=str(self.socket),user='postgres',dbname=self.database) as conn:
            self.assertEqual(conn.execute("SELECT pg_catalog.current_setting('role')").fetchone()[0],'none')
            for name in ('plain_actor','Mixed Case','quoted"actor','é actor'):
                with self.subTest(name=name):
                    conn.execute('SAVEPOINT role_case')
                    conn.execute(sql.SQL('CREATE ROLE {} NOLOGIN').format(sql.Identifier(name)))
                    conn.execute(sql.SQL('SET LOCAL ROLE {}').format(sql.Identifier(name)))
                    self.assertEqual(conn.execute("SELECT current_user::text,pg_catalog.current_setting('role')").fetchone(),(name,name))
                    conn.execute('ROLLBACK TO role_case');conn.execute('RELEASE role_case')
            conn.execute('SAVEPOINT reserved')
            with self.assertRaises(psycopg.errors.ReservedName):conn.execute('CREATE ROLE "none"')
            conn.execute('ROLLBACK TO reserved')
    def test_role_setting_name_can_resolve_to_replacement_oid(self):
        with psycopg.connect(host=str(self.socket),user='postgres',dbname=self.database,autocommit=True) as admin:
            admin.execute('CREATE ROLE cached_actor NOLOGIN')
            with psycopg.connect(host=str(self.socket),user='postgres',dbname=self.database) as caller:
                caller.execute('SET LOCAL ROLE cached_actor')
                original=caller.execute("SELECT r.oid FROM pg_catalog.pg_roles r WHERE r.rolname=current_user").fetchone()[0]
                admin.execute('ALTER ROLE cached_actor RENAME TO renamed_actor')
                admin.execute('CREATE ROLE cached_actor NOLOGIN')
                effective,hint,effective_oid,hint_oid=caller.execute("""SELECT current_user::text,pg_catalog.current_setting('role'),
                    (SELECT oid FROM pg_catalog.pg_roles WHERE rolname=current_user),
                    (SELECT oid FROM pg_catalog.pg_roles WHERE rolname=pg_catalog.current_setting('role'))""").fetchone()
                self.assertEqual((effective,hint,effective_oid),('renamed_actor','cached_actor',original))
                self.assertNotEqual(hint_oid,original)
            admin.execute('DROP ROLE cached_actor,renamed_actor')

if __name__=='__main__':unittest.main(verbosity=2)
