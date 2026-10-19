# SPDX-License-Identifier: MIT OR Apache-2.0
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


class ManagedTableFunctionGuardTests(ManagedFunctionGuardTests):
    for _name in tuple(n for n in dir(ManagedFunctionGuardTests) if n.startswith('test_')):
        locals()[_name]=None

    def setUp(self):
        super().setUp()
        self.connection.execute('''CREATE OR REPLACE FUNCTION truss.managed_guard_table_probe(delay_seconds double precision,row_count int)
            RETURNS TABLE(value text,marker int,raw bytea) LANGUAGE plpgsql VOLATILE AS $$ BEGIN
            INSERT INTO pg_temp.managed_guard_counter VALUES('called');
            PERFORM pg_sleep(delay_seconds);
            RETURN QUERY SELECT current_setting('statement_timeout'),i,decode('00ff','hex')
                FROM generate_series(1,row_count) i;END $$''')
        declared=(('value',25),('marker',23),('raw',17))
        call=('managed_guard_table_probe','truss.managed_guard_table_probe(%s,%s)',None)
        for target,entries in ((psycopg_host._MANAGED_TABLE_FUNCTIONS,{'managed_guard_table_probe':declared}),
                              (psycopg_host._MANAGED_TABLE_CALLS,{'SELECT * FROM truss.managed_guard_table_probe(%s,%s)':call})):
            selected=patch.dict(target,entries);selected.start();self.addCleanup(selected.stop)

    def tearDown(self):
        if not self.connection.closed:
            self.connection.rollback()
            self.connection.execute('DROP FUNCTION IF EXISTS truss.managed_guard_table_probe(double precision,int)')
        super().tearDown()

    def invoke(self,transaction,delay=0,rows=1):
        def execute(cursor,observed):
            cursor.execute('SELECT * FROM truss.managed_guard_table_probe(%s,%s)',(delay,rows),prepare=False)
            description=tuple((column.name,column.type_code) for column in cursor.description)
            return cursor.fetchall(),description
        return self.host._run_operation(transaction,execute,function_call=True)

    def test_matching_table_timeout_preserves_descriptor_and_three_commands(self):
        self.host._timeout=3000
        queries=self.count_host_commands()
        transaction=self.begin();queries.clear()
        self.assertEqual(self.invoke(transaction),Ok(([('3s',1,b'\x00\xff')],(('value',25),('marker',23),('raw',17)))))
        self.assertEqual(len(queries),3)
        self.assertEqual(self.connection.execute('SELECT count(*) FROM managed_guard_counter').fetchone(),(1,))

    def test_table_timeout_mismatch_has_zero_effect_before_single_dispatch(self):
        transaction=self.begin();observed=[]
        self.count_host_commands(lambda:observed.append(self.connection.execute('SELECT count(*) FROM managed_guard_counter').fetchone()[0]))
        for timeout in (100,7000):
            with self.subTest(timeout=timeout):
                self.connection.execute('TRUNCATE managed_guard_counter')
                self.connection.execute(f'SET LOCAL statement_timeout={timeout}')
                result=self.invoke(transaction)
                self.assertIsInstance(result,Ok)
                self.assertEqual(result.value[0],[('1s',1,b'\x00\xff')])
                self.assertEqual(observed[-1],0)
                self.assertEqual(self.connection.execute('SELECT count(*) FROM managed_guard_counter').fetchone(),(1,))
                self.assertEqual(self.connection.execute("SELECT setting FROM pg_settings WHERE name='statement_timeout'").fetchone(),(str(timeout),))

    def test_table_stale_transaction_and_wrong_row_counts_preserve_prior_work(self):
        self.host._timeout=3000
        transaction=self.begin()
        self.connection.execute("INSERT INTO managed_guard_counter VALUES('prior')")
        queries=self.count_host_commands()
        for rows in (0,2):
            with self.subTest(rows=rows):
                queries.clear()
                self.assertIsInstance(self.invoke(transaction,rows=rows),Error)
                self.assertEqual(self.connection.execute('TABLE managed_guard_counter').fetchall(),[('prior',)])
                self.assertEqual(sum(isinstance(query,str) and 'managed_guard_table_probe' in query for query in queries),1)
        self.connection.rollback();self.connection.execute('BEGIN')
        self.assertIsInstance(self.invoke(transaction),Error)
        self.assertEqual(self.connection.execute('SELECT count(*) FROM managed_guard_counter').fetchone(),(0,))

    def test_table_cancellation_preserves_prior_work_and_timeout(self):
        self.host._timeout=100;transaction=self.begin()
        self.connection.execute("INSERT INTO managed_guard_counter VALUES('prior')")
        result=self.invoke(transaction,delay=0.5)
        self.assertIsInstance(result,Error);self.assertEqual(result.error.code,'cancelled')
        self.assertEqual(self.connection.execute('TABLE managed_guard_counter').fetchall(),[('prior',)])
        self.assertEqual(self.connection.execute('SHOW statement_timeout').fetchone(),('3s',))

    def test_replaced_transaction_with_invalid_semantic_parameters_stays_contained(self):
        transaction=self.begin()
        self.connection.rollback();self.connection.execute('BEGIN')
        self.connection.execute("INSERT INTO managed_guard_counter VALUES('new caller work')")
        def invalid(ordinal):raise ValueError('Invalid original SDK input')
        def never(cursor,observed,ordinal,parameters):
            self.fail('Invalid parameters must not dispatch the TABLE function')
        result=self.host._run_semantic_operation(transaction,never,parameter_producer=invalid,function_call=True)
        self.assertIsInstance(result,Error)
        self.assertEqual(result.error.code,'invalid_transaction')
        self.assertFalse(self.host._custody.quarantined)
        self.assertFalse(self.host._transactions[transaction._key].usable)
        self.assertEqual(self.connection.execute('TABLE managed_guard_counter').fetchall(),[('new caller work',)])
        fresh=self.host.adopt_transaction()
        self.assertIsInstance(fresh,Ok)
        self.assertIsInstance(self.invoke(fresh.value),Ok)


import test_catalog_runtime_native as catalog_base


class CatalogTableFunctionGuardTests(catalog_base.PublicCatalogRuntimeTests):
    for _name in tuple(n for n in dir(catalog_base.PublicCatalogRuntimeTests) if n.startswith('test_')):
        locals()[_name]=None

    def count_commands(self,host):
        original=host._cursor;queries=[]
        class Counted:
            def __init__(self,cursor):self.cursor=cursor
            def __getattr__(self,name):return getattr(self.cursor,name)
            def execute(self,query,*args,**kwargs):
                queries.append(query)
                return self.cursor.execute(query,*args,**kwargs)
        selected=patch.object(host,'_cursor',side_effect=lambda:Counted(original()))
        selected.start();self.addCleanup(selected.stop)
        return queries

    def test_installed_status_and_acceptance_use_three_commands(self):
        self.install();connection,host,assembly,tx=self.consumer()
        prepared=self.prepared(assembly)
        queries=self.count_commands(host)
        status=assembly.status_in_transaction(tx)
        self.assertIsInstance(status,Ok,repr(status));self.assertTrue(status.value.installed)
        self.assertEqual(len(queries),3)
        queries.clear()
        registered=assembly.accept_in_transaction(tx,prepared,request_key='table-guard')
        self.assertIsInstance(registered,Ok,repr(registered)+' '+str(host._custody.last_attempt.error))
        self.assertFalse(registered.value.replayed);self.assertEqual(len(queries),3)
        queries.clear()
        replay=assembly.accept_in_transaction(tx,prepared,request_key='table-guard')
        self.assertIsInstance(replay,Ok,repr(replay));self.assertTrue(replay.value.replayed)
        self.assertEqual(replay.value.report_bytes,registered.value.report_bytes)
        # Replay also obtains the current head through one fixed projection.
        self.assertEqual(len(queries),4)
        host.detach();connection.commit()

    def test_absent_installation_status_preserves_caller_work(self):
        self.admin.execute("CREATE TEMP TABLE caller_work(value text);INSERT INTO caller_work VALUES('kept')")
        result=self.assembly.status_in_transaction(self.tx)
        self.assertIsInstance(result,Ok,repr(result));self.assertFalse(result.value.installed)
        self.assertEqual(self.admin.execute('TABLE caller_work').fetchall(),[('kept',)])
        self.assertFalse(self.host._custody.quarantined)

    def test_existing_schema_without_status_keeps_the_native_error(self):
        self.admin.execute('CREATE SCHEMA truss')
        self.admin.execute("CREATE TEMP TABLE caller_work(value text);INSERT INTO caller_work VALUES('kept')")
        result=self.assembly.status_in_transaction(self.tx)
        self.assertIsInstance(result,Error)
        self.assertEqual(result.error.sql_state,'42883')
        self.assertEqual(self.admin.execute('TABLE caller_work').fetchall(),[('kept',)])
        self.assertFalse(self.host._custody.quarantined)

    def test_catalog_table_calls_keep_stock_parameter_and_result_adapters(self):
        catalog_base.PublicCatalogRuntimeTests.test_host_custom_adapters_cannot_change_catalog_parameters_or_results(self)
