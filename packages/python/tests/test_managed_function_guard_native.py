"""Three-command fixed-function calls with unchanged borrowed-host containment."""
from unittest.mock import patch
from truss import psycopg_host
from truss.execution import Ok,Error
import test_psycopg_host_native as base

class ManagedFunctionGuardTests(base.PsycopgHostNativeTests):
    for _name in tuple(n for n in dir(base.PsycopgHostNativeTests) if n.startswith('test_')):
        locals()[_name]=None

    def setUp(self):
        super().setUp()
        self.connection.execute('CREATE SCHEMA IF NOT EXISTS truss')
        self.connection.execute('CREATE TEMP TABLE managed_guard_counter(value text)')
        self.connection.execute('''CREATE OR REPLACE FUNCTION truss.managed_guard_probe(delay_seconds double precision) RETURNS text
            LANGUAGE plpgsql VOLATILE AS $$ BEGIN
            INSERT INTO pg_temp.managed_guard_counter VALUES('called');
            PERFORM pg_sleep(delay_seconds);
            RETURN current_setting('statement_timeout');END $$''')
        self.allowed=patch.object(psycopg_host,'_MANAGED_FUNCTIONS',psycopg_host._MANAGED_FUNCTIONS|{'managed_guard_probe'})
        self.allowed.start();self.addCleanup(self.allowed.stop)

    def tearDown(self):
        if not self.connection.closed:
            self.connection.rollback()
            self.connection.execute('DROP FUNCTION IF EXISTS truss.managed_guard_probe(double precision)')
        super().tearDown()

    def invoke(self,transaction,delay=0):
        def execute(cursor,observed):
            cursor.execute('SELECT truss.managed_guard_probe(%s)',(delay,),prepare=False)
            return cursor.fetchone()[0]
        return self.host._run_operation(transaction,execute,function_call=True)

    def count_host_commands(self,after_guard=None):
        original=self.host._cursor;queries=[]
        class Counted:
            def __init__(self,cursor):self.cursor=cursor
            def __getattr__(self,name):return getattr(self.cursor,name)
            def execute(self,query,*args,**kwargs):
                queries.append(query)
                result=self.cursor.execute(query,*args,**kwargs)
                if after_guard is not None and isinstance(query,str) and query.startswith('WITH truss_guard'):
                    after_guard()
                return result
        self.host._cursor=lambda:Counted(original())
        return queries

    def test_matching_timeout_uses_three_commands(self):
        self.host._timeout=3000
        queries=self.count_host_commands()
        transaction=self.begin()
        self.assertEqual(len(queries),3)
        queries.clear()
        self.assertEqual(self.invoke(transaction),Ok('3s'))
        self.assertEqual(len(queries),3)
        self.assertEqual(self.connection.execute('SELECT count(*) FROM managed_guard_counter').fetchone(),(1,))

    def test_changed_timeout_guard_has_no_effect_then_executes_once(self):
        transaction=self.begin()
        observed=[]
        self.count_host_commands(lambda:observed.append(self.connection.execute('SELECT count(*) FROM managed_guard_counter').fetchone()[0]))
        for timeout in (100,7000):
            with self.subTest(timeout=timeout):
                self.connection.execute('TRUNCATE managed_guard_counter')
                self.connection.execute(f'SET LOCAL statement_timeout={timeout}')
                self.assertEqual(self.invoke(transaction),Ok('1s'))
                self.assertEqual(observed[-1],0)
                self.assertEqual(self.connection.execute('SELECT count(*) FROM managed_guard_counter').fetchone(),(1,))
                self.assertEqual(self.connection.execute("SELECT setting FROM pg_settings WHERE name='statement_timeout'").fetchone(),(str(timeout),))

    def test_stale_transaction_never_invokes_function(self):
        transaction=self.begin()
        self.connection.rollback();self.connection.execute('BEGIN')
        self.assertIsInstance(self.invoke(transaction),Error)
        self.assertEqual(self.connection.execute('SELECT count(*) FROM managed_guard_counter').fetchone(),(0,))

    def test_cancelled_function_preserves_prior_work_and_timeout(self):
        self.host._timeout=100
        transaction=self.begin()
        self.connection.execute("INSERT INTO managed_guard_counter VALUES('prior')")
        result=self.invoke(transaction,0.5)
        self.assertIsInstance(result,Error);self.assertEqual(result.error.code,'cancelled')
        self.assertEqual(self.connection.execute('TABLE managed_guard_counter').fetchall(),[('prior',)])
        self.assertEqual(self.connection.execute('SHOW statement_timeout').fetchone(),('3s',))
