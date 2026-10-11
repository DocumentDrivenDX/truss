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

    def test_definition_baseline_substitution_refuses_before_sql(self):
        class NoCalls:
            def run(self,*args,**kwargs):raise AssertionError('No SQL permitted')
        with patch('truss._catalog_installation.DEFINITIONS_SHA256','0'*64),self.assertRaises(ValueError):
            construct_provisional_catalog_layout(NoCalls())

    def test_other_native_major_refuses_before_begin(self):
        class Port:
            _transaction_status=b'I'
            def run(self,sql):
                if not sql.startswith('SELECT pg_catalog.jsonb_build_object('):raise AssertionError('No transaction SQL permitted')
                return [[json.dumps({'version':'160015'})]]
        with self.assertRaisesRegex(ValueError,'PostgreSQL17'):
            construct_provisional_catalog_layout(Port())

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
        definitions=json.loads(value.definition_observation)
        self.assertEqual({k:len(v) for k,v in definitions.items()},{'expressions':63,'constraints':298,'indexes':86})
        self.assertEqual(sum(c['kind']=='p' for c in definitions['constraints']),48)
        self.assertTrue(value.original_definition_baseline)
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

    def test_native_descriptor_membership_and_content(self):
        connection=self.connection;independent={}
        class Port:
            @property
            def _transaction_status(self):return connection._transaction_status
            def run(self,sql):
                if sql.startswith('SELECT pg_catalog.jsonb_build_object(') and "'namespace'" in sql:
                    # Transactional control makes the otherwise empty rule surface observable.
                    connection.run('CREATE VIEW truss.constructor_rule_control AS SELECT 1 AS value')
                    for category,table,join,identity,expression in (
                        ('defaults','pg_attrdef','JOIN pg_catalog.pg_class c ON c.oid=x.adrelid JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace','x.oid','pg_catalog.pg_get_expr(x.adbin,x.adrelid,false)'),
                        ('sequences','pg_sequence','JOIN pg_catalog.pg_class c ON c.oid=x.seqrelid JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace','x.seqrelid',None),
                        ('types','pg_type','JOIN pg_catalog.pg_namespace n ON n.oid=x.typnamespace','x.oid',None),
                        ('rules','pg_rewrite','JOIN pg_catalog.pg_class c ON c.oid=x.ev_class JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace','x.oid','pg_catalog.pg_get_ruledef(x.oid,false)'),
                    ):
                        query='SELECT pg_catalog.row_to_json(x)::text'+(','+expression if expression else '')+' FROM pg_catalog.'+table+' x '+join+" WHERE n.nspname='truss' ORDER BY "+identity
                        rows=connection.run(query)
                        independent[category]=[{'native':json.loads(row[0]),'definition':row[1]} if expression else json.loads(row[0]) for row in rows]
                return connection.run(sql)
        with self.assertRaises(CatalogConstructionFailure) as refused:
            construct_provisional_catalog_layout(Port())
        observed=json.loads(refused.exception.original_attempt['namespace_observation'])
        for category,expected in independent.items():
            with self.subTest(category=category):
                self.assertTrue(expected)
                self.assertEqual(observed[category],expected)
        self.assertTrue(refused.exception.rollback_confirmed)
        self.assertEqual(connection.run("SELECT to_regnamespace('truss')::text"),[[None]])

    def test_membership_changes_refuse_and_restore_absence(self):
        for change in (
            'ALTER TABLE truss.setting RENAME TO setting_changed',
            'ALTER SEQUENCE truss.id_seq RENAME TO id_seq_changed',
            'ALTER TABLE truss.setting RENAME COLUMN value TO changed_value',
            'ALTER TABLE truss.setting DROP COLUMN value; ALTER TABLE truss.setting ADD COLUMN value jsonb',
            'CREATE FUNCTION truss.catalog_global_high_water_v01(integer) RETURNS integer LANGUAGE sql AS $$ SELECT 1 $$',
            'CREATE INDEX constructor_extra ON truss.setting(value)',
            'CREATE VIEW truss.constructor_extra AS SELECT 1 AS value',
        ):
            connection=self.connection
            class Port:
                @property
                def _transaction_status(self):return connection._transaction_status
                def run(self,sql):
                    if sql.startswith('SELECT pg_catalog.jsonb_build_object(') and "'namespace'" in sql:
                        connection.run(change)
                    return connection.run(sql)
            with self.subTest(change=change),self.assertRaises(CatalogConstructionFailure) as refused:
                construct_provisional_catalog_layout(Port())
            self.assertIsInstance(refused.exception.primary_failure,ValueError)
            self.assertTrue(refused.exception.rollback_confirmed)
            self.assertEqual(connection.run("SELECT to_regnamespace('truss')::text"),[[None]])

    def test_execution_definitions_refuse_changes_and_restore_absence(self):
        for change in (
            'ALTER SEQUENCE truss.id_seq MAXVALUE 9223372036854775806',
            'ALTER SEQUENCE truss.id_seq CACHE 2',
            'ALTER SEQUENCE truss.id_seq INCREMENT BY 2',
            'ALTER SEQUENCE truss.id_seq CYCLE',
            "CREATE OR REPLACE FUNCTION truss.catalog_global_high_water_v01() RETURNS TABLE(allocation_domain text,maximum_id text) LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$ BEGIN RETURN; END $$",
            'ALTER FUNCTION truss.catalog_global_high_water_v01() SECURITY INVOKER',
            'ALTER FUNCTION truss.catalog_global_high_water_v01() SET search_path TO public',
            'ALTER FUNCTION truss.catalog_global_high_water_v01() STRICT',
            'ALTER FUNCTION truss.catalog_global_high_water_v01() LEAKPROOF',
            'ALTER FUNCTION truss.catalog_global_high_water_v01() SET statement_timeout TO 1000',
        ):
            connection=self.connection
            class Port:
                @property
                def _transaction_status(self):return connection._transaction_status
                def run(self,sql):
                    if sql.startswith('SELECT pg_catalog.jsonb_build_object(') and "'namespace'" in sql:connection.run(change)
                    return connection.run(sql)
            with self.subTest(change=change),self.assertRaises(CatalogConstructionFailure) as refused:
                construct_provisional_catalog_layout(Port())
            self.assertIsInstance(refused.exception.primary_failure,ValueError)
            self.assertTrue(refused.exception.rollback_confirmed)
            self.assertEqual(connection.run("SELECT to_regnamespace('truss')::text"),[[None]])

    def test_column_definition_changes_refuse_and_restore_absence(self):
        original,_=_statements()
        profile=json.loads(original)
        generated=next((t['name'],c['name']) for t in profile['membership']['tables'] for c in t['columns'] if c['definition']['generated']=='s')
        for change in (
            'ALTER TABLE truss.setting ALTER COLUMN value TYPE json USING value::json',
            'ALTER TABLE truss.setting ALTER COLUMN value DROP NOT NULL',
            'ALTER TABLE truss.setting ALTER COLUMN key TYPE text COLLATE "C"',
            "ALTER TABLE truss.setting ALTER COLUMN value SET DEFAULT '{}'::jsonb",
            'ALTER TABLE truss.schema_rev ALTER COLUMN accepted_at DROP DEFAULT',
            'ALTER TABLE truss.edge_limit ALTER COLUMN side TYPE char(2)',
            'ALTER TABLE truss.key_def ALTER COLUMN prop_ids TYPE integer[][]',
            'ALTER TABLE truss."'+generated[0]+'" ALTER COLUMN "'+generated[1]+'" DROP EXPRESSION',
        ):
            connection=self.connection
            class Port:
                @property
                def _transaction_status(self):return connection._transaction_status
                def run(self,sql):
                    if sql.startswith('SELECT pg_catalog.jsonb_build_object(') and "'namespace'" in sql:connection.run(change)
                    return connection.run(sql)
            with self.subTest(change=change),self.assertRaises(CatalogConstructionFailure) as refused:
                construct_provisional_catalog_layout(Port())
            self.assertIsInstance(refused.exception.primary_failure,ValueError)
            self.assertTrue(refused.exception.rollback_confirmed)
            self.assertEqual(connection.run("SELECT to_regnamespace('truss')::text"),[[None]])

    def test_expression_constraint_and_index_drift_refuses(self):
        original,_=_statements();profile=json.loads(original)
        generated=next((t['name'],c['name']) for t in profile['membership']['tables'] for c in t['columns'] if c['definition']['generated']=='s')
        for change in (
            "ALTER TABLE truss.schema_rev ALTER COLUMN origin SET DEFAULT '{\"changed\":true}'::jsonb",
            'ALTER TABLE truss.setting ADD CONSTRAINT constructor_extra_unique UNIQUE(value)',
            'ALTER TABLE truss.edge DROP CONSTRAINT edge_typed_identity_row_home CASCADE',
            'ALTER TABLE truss.schema_rev DROP CONSTRAINT schema_rev_origin_is_object; ALTER TABLE truss.schema_rev ADD CONSTRAINT schema_rev_origin_is_object CHECK (true)',
            'ALTER TABLE truss.object DROP CONSTRAINT object_rev_fkey; ALTER TABLE truss.object ADD CONSTRAINT object_rev_fkey FOREIGN KEY(rev) REFERENCES truss.schema_rev(rev) ON DELETE CASCADE',
            'ALTER INDEX truss.object_type_id SET (fillfactor=80)',
        ):
            connection=self.connection
            class Port:
                @property
                def _transaction_status(self):return connection._transaction_status
                def run(self,sql):
                    if sql.startswith('SELECT pg_catalog.jsonb_build_object(') and "'namespace'" in sql:connection.run(change)
                    return connection.run(sql)
            with self.subTest(change=change),self.assertRaises(CatalogConstructionFailure) as refused:
                construct_provisional_catalog_layout(Port())
            self.assertIsInstance(refused.exception.primary_failure,ValueError)
            self.assertTrue(refused.exception.rollback_confirmed)
            self.assertEqual(connection.run("SELECT to_regnamespace('truss')::text"),[[None]])

    def test_changed_generated_content_with_same_flags_refuses(self):
        connection=self.connection;changed=[]
        class Port:
            @property
            def _transaction_status(self):return connection._transaction_status
            def run(self,sql):
                if not changed and 'GENERATED ALWAYS AS (pg_catalog.sha256(lineage_bytes))' in sql:
                    sql=sql.replace('pg_catalog.sha256(lineage_bytes)',"pg_catalog.sha256('changed'::bytea)")
                    changed.append(True)
                return connection.run(sql)
        with self.assertRaises(CatalogConstructionFailure) as refused:
            construct_provisional_catalog_layout(Port())
        self.assertEqual(changed,[True])
        self.assertIsInstance(refused.exception.primary_failure,ValueError)
        self.assertIn('definition correspondence',str(refused.exception.primary_failure))
        self.assertTrue(refused.exception.rollback_confirmed)

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
