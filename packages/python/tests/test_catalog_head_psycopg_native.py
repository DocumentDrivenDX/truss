"""Private provisional configured head; raw commit remains refused."""
from pathlib import Path
from truss import Ok, Error
from test_catalog_prerequisites_psycopg_native import PrerequisitePsycopgNativeTests
ROOT=Path(__file__).resolve().parents[3]

class HeadPsycopgNativeTests(PrerequisitePsycopgNativeTests):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        import psycopg
        with psycopg.connect(host=str(cls.socket),user='postgres',dbname=cls.database,autocommit=True) as connection:
            connection.execute((ROOT/'packages/postgresql/native/catalog-completion/configured-state-candidate.sql').read_text(),prepare=False)

    def head(self):
        def execute(cursor, observed):
            cursor.execute('SELECT * FROM truss.runtime_register_catalog_and_head_candidate(%s,%s,%s,%s,%s,%s,%s)',
                (self.writer,self.ordinal,self.generation,self.identity,self.registration,
                 (ROOT/'packages/python/src/truss/_profiles/fresh-catalog-lifecycle.json').read_bytes(),
                 (ROOT/'packages/python/src/truss/_profiles/absent-binding-index-declarations.json').read_bytes()),prepare=False)
            rows=cursor.fetchmany(2);self.assertEqual(len(rows),1);return rows[0]
        return self.host._run_operation(self.transaction,execute)

    def install_head_trigger(self,body):
        # Install the fault producer before original operation admission.
        self.query('CREATE FUNCTION truss.fixture_head_effect() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN '+body+' END $$; CREATE TRIGGER fixture_head_effect AFTER UPDATE ON truss.schema_head FOR EACH ROW EXECUTE FUNCTION truss.fixture_head_effect()')

    def test_provisional_head_complete_generation(self):
        self.stage();before=self.query('SELECT effect_generation FROM truss.row_home_operation').fetchone()[0]
        result=self.head();self.assertIsInstance(result,Ok,str(self.host._custody.last_attempt.error))
        self.assertEqual(result.value[2],str(before+2));self.assertEqual(result.value[3],'1')
        self.assertEqual(result.value[6:],(False,False))
        self.assertEqual(self.query('SELECT rev FROM truss.schema_head').fetchone(),(1,))
        self.assertEqual(self.query('SELECT phase,readiness_generation,sealed_generation,application_generation,application_result_bytes FROM truss.row_home_operation').fetchone(),('admitted',None,None,None,None))
        self.assertEqual(self.query('SELECT finalized_generation,manifest_bytes,manifest_sha256 FROM truss.feed_tx').fetchone(),(None,None,None))

    def test_post_head_failure_preserves_prior_host_work(self):
        self.install_head_trigger("RAISE EXCEPTION 'head fault' USING ERRCODE='54000';")
        self.stage();self.query("CREATE TEMP TABLE prior_head_work(value text); INSERT INTO prior_head_work VALUES('keep')")
        before=self.query('SELECT truss.runtime_capture_configured_completion_state_candidate(%s,%s,%s)',(self.writer,self.ordinal,self.generation)).fetchone()[0]
        result=self.head();self.assertIsInstance(result,Error);self.assertEqual(result.error.sql_state,'54000')
        after=self.query('SELECT truss.runtime_capture_configured_completion_state_candidate(%s,%s,%s)',(self.writer,self.ordinal,self.generation)).fetchone()[0]
        self.assertEqual(after,before)
        self.assert_rolled_back();self.assertEqual(self.query('TABLE prior_head_work').fetchall(),[('keep',)])

    def test_same_count_configuration_substitution_after_head(self):
        self.install_head_trigger("UPDATE truss.installation_admission SET installed_inventory_bytes=convert_to('replacement','UTF8'); RETURN NULL;")
        self.stage();result=self.head();self.assertIsInstance(result,Error)
        self.assertEqual(result.error.sql_state,'55000');self.assert_rolled_back()

    def test_same_count_feed_substitution_after_head(self):
        self.install_head_trigger("UPDATE truss.feed_prerequisite SET original_owner_context_bytes=decode('01','hex'); RETURN NULL;")
        self.stage();result=self.head();self.assertIsInstance(result,Error)
        self.assertEqual(result.error.sql_state,'55000');self.assert_rolled_back()

    def test_provisional_head_cannot_commit(self):
        import psycopg
        self.stage();result=self.head();self.assertIsInstance(result,Ok,str(self.host._custody.last_attempt.error))
        with self.assertRaises(psycopg.Error) as raised:self.connection.commit()
        self.assertEqual(raised.exception.sqlstate,'55000')
        self.connection.rollback();self.assert_rolled_back()

    def test_wrong_head_returning_refuses(self):
        self.query("CREATE FUNCTION truss.fixture_head_before() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN NEW.rev:=0; RETURN NEW; END $$; CREATE TRIGGER fixture_head_before BEFORE UPDATE ON truss.schema_head FOR EACH ROW EXECUTE FUNCTION truss.fixture_head_before()")
        self.stage();result=self.head();self.assertIsInstance(result,Error)
        self.assertEqual(result.error.sql_state,'55000');self.assert_rolled_back()

    def test_missing_head_observer_refuses(self):
        self.stage()
        self.query('ALTER TABLE truss.schema_head DISABLE TRIGGER runtime_catalog_generation')
        result=self.head();self.assertIsInstance(result,Error)
        self.assertEqual(result.error.sql_state,'55000');self.assert_rolled_back()

    def test_descriptor_change_after_head_refuses(self):
        self.install_head_trigger("EXECUTE 'ALTER TABLE truss.setting ADD COLUMN unexpected text'; RETURN NULL;")
        self.stage();result=self.head();self.assertIsInstance(result,Error)
        self.assertEqual(result.error.sql_state,'55000');self.assert_rolled_back()
        self.assertEqual(self.query("SELECT count(*) FROM pg_attribute WHERE attrelid='truss.setting'::regclass AND attname='unexpected'").fetchone(),(0,))

    def test_extra_post_head_catalog_effect_refuses(self):
        self.install_head_trigger("UPDATE truss.schema_rev SET rev=rev; RETURN NULL;")
        self.stage();result=self.head();self.assertIsInstance(result,Error)
        self.assertEqual(result.error.sql_state,'55000');self.assert_rolled_back()

    def test_two_document_provisional_head(self):
        import copy,json
        from truss import CatalogDocument
        from test_preparation import prepare,CONFIG
        from test_catalog_staging import native_document
        from truss._catalog_support import PROFILE
        config=copy.deepcopy(CONFIG);config['supportProfile']=dict(PROFILE)
        first=json.loads(native_document('first').content);first['modules']=[]
        second=json.loads(native_document('second').content);second['modules']=[]
        docs=(CatalogDocument('first','r1',json.dumps(first).encode(),'artifact:first'),
              CatalogDocument('second','r2',json.dumps(second).encode(),'artifact:second'))
        self.prepared=prepare(docs,config)
        self.stage();result=self.head();self.assertIsInstance(result,Ok,str(self.host._custody.last_attempt.error))
        self.assertEqual(result.value[3],'1')
        self.assertEqual(self.query('SELECT count(*) FROM truss.feed_prerequisite').fetchone(),(2,))
        self.assertEqual(self.query('SELECT membership_generation FROM truss.feed_tx').fetchone(),(4,))

    def test_external_inheritance_child_refuses(self):
        self.query('CREATE TABLE public.outside_type_child () INHERITS (truss.type_def)')
        self.install_head_trigger('INSERT INTO public.outside_type_child SELECT * FROM ONLY truss.type_def; RETURN NULL;')
        self.stage();result=self.head();self.assertIsInstance(result,Error)
        self.assertEqual(result.error.sql_state,'0A000');self.assert_rolled_back()
        self.assertEqual(self.query('SELECT count(*) FROM public.outside_type_child').fetchone(),(0,))

    def test_changed_original_observer_body_refuses(self):
        self.stage()
        original=self.query("SELECT pg_get_functiondef('truss.runtime_observe_catalog_generation()'::regprocedure)").fetchone()[0]
        self.assertIn('BEGIN',original)
        self.query(original.replace('BEGIN','BEGIN PERFORM 1;',1))
        result=self.head();self.assertIsInstance(result,Error)
        self.assertEqual(result.error.sql_state,'55000');self.assert_rolled_back()

    def test_head_observer_resets_intermediate_readiness(self):
        self.query("CREATE FUNCTION truss.fixture_head_before() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN UPDATE truss.row_home_operation SET phase='row_sealed',readiness_generation=effect_generation,sealed_generation=effect_generation,application_generation=NULL,application_result_bytes=NULL; RETURN NEW; END $$; CREATE TRIGGER fixture_head_before BEFORE UPDATE ON truss.schema_head FOR EACH ROW EXECUTE FUNCTION truss.fixture_head_before()")
        self.stage();result=self.head();self.assertIsInstance(result,Ok,str(self.host._custody.last_attempt.error))
        self.assertEqual(self.query('SELECT phase,readiness_generation,sealed_generation,application_generation,application_result_bytes FROM truss.row_home_operation').fetchone(),('admitted',None,None,None,None))

    def test_completion_collector_refuses_external_inheritance(self):
        import psycopg
        self.stage()
        self.query('CREATE TABLE public.outside_type_child () INHERITS (truss.type_def)')
        self.query('SAVEPOINT inheritance_cut')
        with self.assertRaises(psycopg.Error) as caught:
            self.query('SELECT truss.runtime_capture_configured_completion_state_candidate(%s,%s,%s)',(self.writer,self.ordinal,self.generation))
        self.assertEqual(caught.exception.sqlstate,'0A000')
        self.query('ROLLBACK TO inheritance_cut');self.assert_rolled_back()
