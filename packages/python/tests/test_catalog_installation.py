"""Actual original-owner DDL constructor; no ready installation publication."""
import json
import unittest
from unittest.mock import patch
from test_native_pg8000 import NativeBoundaryFixture
from truss._catalog_installation import construct_provisional_catalog_layout,CatalogConstructionFailure,_statements


class CatalogInstallationInputTests(unittest.TestCase):
    def test_statement_substitution_refuses_before_sql(self):
        class NoCalls:
            def run(self,*args,**kwargs):raise AssertionError('No SQL permitted')
        with patch('truss._catalog_installation.STATEMENTS_SHA256','0'*64),self.assertRaises(ValueError):
            construct_provisional_catalog_layout(NoCalls())

    def test_caller_runtime_transaction_not_adopted(self):
        class NoCalls:
            _transaction_status=b'T'
            def run(self,*args,**kwargs):raise AssertionError('No SQL permitted')
        with self.assertRaisesRegex(ValueError,'idle installer'):
            construct_provisional_catalog_layout(NoCalls())


class CatalogInstallationNativeTests(NativeBoundaryFixture,unittest.TestCase):
    def setUp(self):
        # The constructor owns this administrative transaction; no runtime mediator.
        self.connection=self.Connection(**self.kwargs)
        self.connection.run('SELECT 1')

    def tearDown(self):self.connection.close()

    def test_exact_owner_construction_genesis_and_rollback(self):
        value=construct_provisional_catalog_layout(self.connection)
        observed=json.loads(value.namespace_observation)
        tables=[r for r in observed['relations'] if r['relkind'] in ('r','p')]
        self.assertEqual(len(tables),48)
        table_oids={r['oid'] for r in tables}
        columns=[a for a in observed['columns'] if a['attrelid'] in table_oids and a['attnum']>0 and not a['attisdropped']]
        self.assertEqual(len(columns),454)
        self.assertEqual(value.statement_count,'112')
        self.assertEqual(len(observed['routines']),2)
        self.assertTrue(value.rollback_confirmed)
        self.assertFalse(value.installation_ready)
        self.assertEqual(self.connection.run("SELECT to_regnamespace('truss')::text"),[[None]])

    def test_hostile_search_path_is_contained_and_restored(self):
        self.connection.run('CREATE SCHEMA constructor_shadow')
        self.connection.run("CREATE FUNCTION constructor_shadow.to_jsonb(anyelement) RETURNS jsonb LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'shadow function reached'; END $$")
        self.connection.run('SET search_path = constructor_shadow, pg_catalog, public')
        before=self.connection.run('SHOW search_path')
        with self.assertRaisesRegex(Exception,'shadow function reached'):
            self.connection.run('SELECT to_jsonb(1)')
        try:
            value=construct_provisional_catalog_layout(self.connection)
            observed=json.loads(value.namespace_observation)
            self.assertEqual(len(observed['routines']),2)
            self.assertEqual(self.connection.run('SHOW search_path'),before)
            self.assertTrue(value.rollback_confirmed)
        finally:
            self.connection.run('RESET search_path')
            self.connection.run('DROP SCHEMA constructor_shadow CASCADE')

    def test_existing_namespace_preserved_without_overwrite(self):
        self.connection.run('CREATE SCHEMA truss')
        self.connection.run('CREATE TABLE truss.sentinel(value text)')
        try:
            with self.assertRaises(CatalogConstructionFailure) as refused:
                construct_provisional_catalog_layout(self.connection)
            self.assertTrue(refused.exception.rollback_confirmed)
            self.assertEqual(self.connection.run("SELECT count(*) FROM pg_class WHERE relnamespace='truss'::regnamespace"),[[1]])
        finally:self.connection.run('DROP SCHEMA truss CASCADE')

    def test_failures_after_ddl_and_revocations_restore_absence(self):
        _,statements=_statements()
        for selected in (statements[0]['sql'],statements[45]['sql'],statements[-1]['sql'],'REVOKE ALL ON ALL FUNCTIONS IN SCHEMA truss FROM PUBLIC'):
            connection=self.connection
            failure=RuntimeError('Original injected late construction failure')
            class Port:
                @property
                def _transaction_status(self):return connection._transaction_status
                def run(self,sql):
                    result=connection.run(sql)
                    if sql==selected:raise failure
                    return result
            with self.subTest(stage=selected[:40]),self.assertRaises(CatalogConstructionFailure) as refused:
                construct_provisional_catalog_layout(Port())
            self.assertIs(refused.exception.primary_failure,failure)
            self.assertTrue(refused.exception.rollback_confirmed)
            self.assertEqual(connection.run("SELECT to_regnamespace('truss')::text"),[[None]])

    def test_public_bypass_denied_in_constructed_namespace(self):
        self.connection.run('CREATE ROLE constructor_consumer NOLOGIN')
        connection=self.connection;checked=[]
        class Port:
            @property
            def _transaction_status(self):return connection._transaction_status
            def run(self,sql):
                result=connection.run(sql)
                if sql=='REVOKE ALL ON ALL FUNCTIONS IN SCHEMA truss FROM PUBLIC':
                    rights=connection.run("SELECT has_schema_privilege('constructor_consumer','truss','USAGE'),has_table_privilege('constructor_consumer','truss.object','INSERT'),has_table_privilege('constructor_consumer','truss.object','TRUNCATE'),has_function_privilege('constructor_consumer','truss.catalog_global_high_water_v01()','EXECUTE')")
                    checked.append(rights)
                return result
        construct_provisional_catalog_layout(Port())
        self.assertEqual(checked,[[[False,False,False,False]]])

    def test_lost_rollback_reply_retains_original_attempt_without_retry(self):
        connection=self.connection;commands=[]
        loss=OSError('Lost original rollback reply')
        class Port:
            @property
            def _transaction_status(self):return connection._transaction_status
            def run(self,sql):
                commands.append(sql);result=connection.run(sql)
                if sql=='ROLLBACK':raise loss
                return result
        with self.assertRaises(CatalogConstructionFailure) as refused:
            port=Port()
            construct_provisional_catalog_layout(port)
        self.assertIs(refused.exception.original_connection,port)
        self.assertTrue(refused.exception.original_attempt['rollback_submitted'])
        self.assertFalse(refused.exception.original_attempt['rollback_reply_observed'])
        self.assertEqual(len(refused.exception.original_attempt['submitted_statements']),112)
        self.assertIs(refused.exception.cleanup_failure,loss)
        self.assertFalse(refused.exception.rollback_confirmed)
        self.assertEqual(commands.count('BEGIN'),1)
        self.assertEqual(commands.count('ROLLBACK'),1)
        self.assertTrue(refused.exception.original_statements)
        self.assertTrue(refused.exception.original_target)
        self.assertEqual(connection.run("SELECT to_regnamespace('truss')::text"),[[None]])
