"""Actual pending prerequisite registration via supported guarded psycopg execution.

Administrative synthetic setup; every outer transaction rolls back. No public
installation, accepted catalog, commit or ordinary-person claim.
"""
import hashlib
import json
import unittest
import os
import subprocess
import tempfile
from pathlib import Path
import psycopg
from truss import Ok, Error, adopt_psycopg_host, PsycopgProfile
from test_psycopg_host_native import PsycopgHostNativeTests, postgres_bin_for_profile
from test_catalog_staging import COMPONENTS
from test_catalog_support import selected
from truss._catalog_candidate import encode_original_catalog_candidate
from truss._catalog_report_semantics import canonical_numeric_free
ROOT=Path(__file__).resolve().parents[3]

class PrerequisitePsycopgNativeTests(unittest.TestCase):
    selected_profile=PsycopgProfile()
    additional_install_paths=()
    stage_recipe_path=None
    stage_function="runtime_stage_catalog_with_release"
    run_pg=classmethod(PsycopgHostNativeTests.run_pg.__func__)
    @classmethod
    def setUpClass(cls):
        cls.worker_fixture=None;cls.database='postgres'
        if os.environ.get('TRUSS_NATIVE_WORKER') and not getattr(cls, 'isolated_lifecycle', False):
            from native_fixture import configure_shared_psycopg_fixture
            configure_shared_psycopg_fixture(cls)
        else:
            cls.root=Path(tempfile.mkdtemp(prefix='truss-prerequisite-',dir='/private/tmp'));cls.data=cls.root/'data';cls.socket=cls.root/'socket';cls.socket.mkdir()
        cls.pgbin=postgres_bin_for_profile(cls.selected_profile)
        cls.start_attempted=False
        cls.addClassCleanup(cls.cleanup_fixture)
        if cls.worker_fixture is None:
            cls.run_pg('initdb','-D',str(cls.data),'-U','postgres','--auth=trust','--encoding=UTF8')
            cls.start_attempted=True
            cls.run_pg('pg_ctl','-D',str(cls.data),'-l',str(cls.root/'server.log'),'-w','-o',f"-h '' -k {cls.socket}",'start')
        with psycopg.connect(host=str(cls.socket),user='postgres',dbname=cls.database,autocommit=True) as connection:
            paths=['docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql',
                   'docs/helix/04-build/evidence/operation-configuration-storage.owner-export.sql']
            paths.extend(f'packages/postgresql/native/{name}.sql' for name in COMPONENTS if name!='operation-admission')
            names=('source-epoch-lock','issued-operation-admission/operation-admission','issued-operation-admission/operation-configuration-context-admission',
                   'catalog-epoch-context','operation-configuration-current','operation-configuration-immutability','catalog-admission-configuration',
                   'canonical-string-bytes','canonical-tree-bytes','catalog-report/release-selection','catalog-report/source-candidate',
                   'catalog-report/configured-metadata','catalog-report/empty-graph','catalog-report/configured-graph',
                   'catalog-report/absent-binding-index-declarations','catalog-report/fresh-lifecycle','edge-limit/verify-current-scope',
                   'catalog-stage-issued','catalog-report/resource-selection','catalog-report/archive-self-write-fence',
                   'catalog-report/archive-write-fence-current','catalog-report/configured-stage','catalog-report/report-write-candidate',
                   'catalog-report/revision-registration-candidate','catalog-report/revision-report-tree-wide-candidate','catalog-report/report-write-wide-candidate','catalog-report/revision-registration-wide-candidate','catalog-completion/configured-prerequisite-state-candidate',
                   'catalog-report/prerequisite-registration-candidate')
            paths.extend(f'packages/postgresql/native/{name}.sql' for name in names)
            paths.extend(cls.additional_install_paths)
            for path in paths: connection.execute((ROOT/path).read_text(),prepare=False)
            fixture=(ROOT/'docs/helix/04-build/evidence/design-audit/pgserver-populated-guard-fixture.sql').read_text()
            connection.execute(fixture.partition('INSERT INTO truss.row_home_operation')[0],prepare=False)
            connection.execute("INSERT INTO truss.source_epoch_current VALUES(1,'guard-fixture','guard-fixture-epoch')")
    @classmethod
    def cleanup_fixture(cls):
        if cls.worker_fixture is not None:
            cls.worker_fixture.cleanup();cls.worker_fixture=None
            return
        import shutil
        receipt={'stop':None,'status':None,'socket_absent':False}
        if cls.start_attempted:
            try:
                result=subprocess.run([str(cls.pgbin/'pg_ctl'),'-D',str(cls.data),'-w','-m','immediate','stop'],capture_output=True,text=True,timeout=30)
                receipt['stop']=result.returncode
            except Exception as error:receipt['stop_error']=repr(error)
            try:
                result=subprocess.run([str(cls.pgbin/'pg_ctl'),'-D',str(cls.data),'status'],capture_output=True,text=True,timeout=10)
                receipt['status']=result.returncode
            except Exception as error:receipt['status_error']=repr(error)
        receipt['socket_absent']=not (cls.socket/'.s.PGSQL.5432').exists()
        confirmed=not cls.start_attempted or (receipt['stop']==0 and receipt['status']==3 and receipt['socket_absent'])
        receipt['directory_preserved']=not confirmed
        folder=os.environ.get('TRUSS_PREREQUISITE_EVIDENCE_DIR')
        if folder:
            target=Path(folder);(target/'cleanup.json').write_text(json.dumps(receipt,indent=2)+'\n')
            log=cls.root/'server.log'
            if log.exists():(target/'server.log').write_bytes(log.read_bytes())
        if confirmed:shutil.rmtree(cls.root)
        else:raise RuntimeError('Owned prerequisite fixture shutdown unconfirmed; directory retained: '+str(cls.root))

    def setUp(self):
        self.connection=psycopg.connect(host=str(self.socket),user='postgres',dbname=self.database,autocommit=True,options='-c statement_timeout=10000')
        self.addCleanup(self.connection.close)
        self.host=adopt_psycopg_host(self.connection,profile=self.selected_profile,statement_timeout_ms=8000,operation_timeout_ms=15000)
        self.addCleanup(self.host.detach)
        policy=(ROOT/'packages/python/src/truss/_profiles/catalog-report-release.json').read_bytes()
        configuration=json.dumps({'interfaceVersion':'truss-catalog-report-configuration/0.1','catalogReportRelease':{'artifactIdentity':'truss.catalog-report-release/0.1.0','sha256':hashlib.sha256(policy).hexdigest()}}).encode()
        self.connection.execute("INSERT INTO truss.installation_admission(head_id,installation_id_utf8,source_epoch_utf8,configuration_generation,key_reuse,journal_mode,configuration_bytes,selected_binding_bytes,installed_inventory_bytes) VALUES(1,convert_to('guard-fixture','UTF8'),convert_to('guard-fixture-epoch','UTF8'),7,'forbid','engine',%s,convert_to('binding fixture','UTF8'),convert_to('inventory fixture','UTF8'))",(configuration,))
        self.connection.execute('BEGIN')
        self.transaction=self.host.adopt_transaction().value
        self.prepared=selected()
    def tearDown(self):
        self.host.detach(); self.connection.rollback(); self.connection.execute('DELETE FROM truss.installation_admission'); self.connection.close()
    def query(self,sql,params=None):
        return self.connection.execute(sql,params,prepare=False)
    def archive(self,identity,raw):
        self.query("INSERT INTO truss.installation_archive(installation_id,artifact_role,artifact_identity,artifact_bytes,artifact_identity_sha256) VALUES('guard-fixture','input',%s,%s,sha256(convert_to(%s,'UTF8')))",(identity,raw,identity))
    def stage(self):
        policy=(ROOT/'packages/python/src/truss/_profiles/catalog-report-release.json').read_bytes()
        profile=(ROOT/'packages/python/src/truss/_profiles/catalog-report-configuration.json').read_bytes()
        configuration=json.dumps({'interfaceVersion':'truss-catalog-report-configuration/0.1','catalogReportRelease':{'artifactIdentity':'truss.catalog-report-release/0.1.0','sha256':hashlib.sha256(policy).hexdigest()}}).encode()

        self.archive('truss.catalog-report-release/0.1.0',policy)
        seen={'truss.catalog-report-release/0.1.0'}
        paths=[item['path'] for item in json.loads(policy)['resources']]
        recipes=['catalog-report-composition-candidate','catalog-revision-registration-candidate','catalog-report-wide-composition-candidate','catalog-revision-wide-registration-candidate','catalog-prerequisite-registration-candidate']
        for name in recipes:
            path=f'packages/python/src/truss/_profiles/{name}.json'; paths.append(path)
            recipe=json.loads((ROOT/path).read_bytes())
            paths.extend(ref['path'] for ref in recipe.get('sources',{}).values())
            paths.extend(ref['path'] for ref in recipe.get('profileArtifacts',{}).values())
            if 'payloadProfile' in recipe:paths.append(recipe['payloadProfile']['path'])
        for path in paths:
            if path in seen:continue
            raw=(ROOT/path).read_bytes()
            if getattr(self,'changed_wide_profile',False) and path.endswith('catalog-revision-wide-report-composition-candidate.json'):raw+=b' '
            self.archive(path,raw);seen.add(path)
        recipe_path='packages/python/src/truss/_profiles/catalog-report-composition-candidate.json' if getattr(self,'use_old',False) else 'packages/python/src/truss/_profiles/catalog-report-wide-composition-candidate.json'
        recipe_path=self.stage_recipe_path or recipe_path
        if recipe_path not in seen:self.archive(recipe_path,(ROOT/recipe_path).read_bytes())
        composition=json.loads((ROOT/recipe_path).read_bytes())
        registration={'interfaceVersion':'truss-catalog-report-candidate-registration/0.1','scope':'administrative_rollback_only_report_write','layoutProfile':self.prepared.input()['layoutProfile'],'composition':{'identity':recipe_path,'sha256':hashlib.sha256((ROOT/recipe_path).read_bytes()).hexdigest()}}
        for field,ref in composition['profileArtifacts'].items():
            raw=(ROOT/ref['path']).read_bytes();p=json.loads(raw)
            registration[field]={'identity':p['identity'],'version':p['version'],'sha256':hashlib.sha256(raw).hexdigest()}
        self.registration=canonical_numeric_free(registration); self.identity='fixture.catalog-report-composition/0.1'
        self.archive(self.identity,self.registration)
        p=self.prepared;candidate=encode_original_catalog_candidate(p)
        pre=bytes.fromhex(self.query('SELECT truss.runtime_capture_catalog_prestate()').fetchone()[0])
        self.writer,self.ordinal,context=self.query("SELECT * FROM truss.runtime_admit_operation_with_configuration_context(0,'catalog-acceptance',decode('01','hex'),%s,%s,%s,decode('05','hex'),decode('06','hex'),convert_to('{}','UTF8'),%s,'guard-fixture','guard-fixture-epoch','guard-fixture-incarnation',%s)",(p.input_bytes,pre,candidate,(ROOT/composition['profileArtifacts']['captureProfile']['path']).read_bytes(),profile)).fetchone()
        context=bytes.fromhex(context)
        result=self.query(f"SELECT * FROM truss.{self.stage_function}(0,decode('01','hex'),%s,%s,decode('05','hex'),decode('06','hex'),%s,%s,convert_to('{{}}','UTF8'),%s,%s,%s)",(p.input_bytes,candidate,p.archive_documents_bytes,p.declarations_bytes,pre,context,profile)).fetchone()
        self.generation=json.loads(bytes.fromhex(result[3]))['effectGeneration']
    def register(self):
        def execute(cursor,observed):
            cursor.execute('SELECT * FROM truss.runtime_register_catalog_prerequisites_candidate(%s,%s,%s,%s,%s,%s,%s)',
              (self.writer,self.ordinal,self.generation,self.identity,self.registration,
               (ROOT/'packages/python/src/truss/_profiles/fresh-catalog-lifecycle.json').read_bytes(),
               (ROOT/'packages/python/src/truss/_profiles/absent-binding-index-declarations.json').read_bytes()),prepare=False,binary=False)
            self.assertEqual([d.type_code for d in cursor.description],[25]*9+[16,16])
            rows=cursor.fetchmany(2);self.assertEqual(len(rows),1);return rows[0]
        return self.host._run_operation(self.transaction,execute)
    def test_real_registration_original_bytes_and_counters(self):
        self.stage();result=self.register();self.assertIsInstance(result,Ok,str(self.host._custody.last_attempt.error))
        row=result.value;self.assertEqual(row[5:8],('1','1','3'));self.assertEqual(row[9:],(False,False))
        definition=self.query('SELECT original_definition_bytes,original_definition_sha256 FROM truss.feed_prerequisite').fetchone()
        original=self.query('SELECT convert_to(document,\'UTF8\') FROM truss.schema_doc').fetchone()[0]
        self.assertEqual(definition,(original,hashlib.sha256(original).digest()))
        config=self.query('SELECT original_configuration_bytes,original_producer_inventory_bytes FROM truss.feed_configuration_prerequisite').fetchone()
        parsed=json.loads(config[0]);self.assertEqual(parsed['generation'],'7')
        self.assertNotIn('writerXid',parsed);self.assertNotIn('operationOrdinal',parsed)
        self.assertEqual(config[1],b'inventory fixture')
        self.assertEqual(self.query('SELECT registration_counter,prerequisite_registration_counter,configuration_registration_counter,membership_generation,finalized_generation,manifest_bytes FROM truss.feed_tx').fetchone(),(1,1,1,3,None,None))
        self.assertEqual(self.query('SELECT rev FROM truss.schema_head').fetchone(),(0,))
    def test_single_use_refusal_preserves_pending_rows(self):
        self.stage();result=self.register();self.assertIsInstance(result,Ok,str(self.host._custody.last_attempt.error))
        before=self.query("SELECT encode(record_send(t),'hex') FROM truss.feed_tx t").fetchall()
        self.assertIsInstance(self.register(),Error)
        self.assertEqual(self.query("SELECT encode(record_send(t),'hex') FROM truss.feed_tx t").fetchall(),before)
    def trigger(self,table,event,body):
        self.query("CREATE FUNCTION truss.fixture_prerequisite_effect() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN "+body+" END $$; CREATE TRIGGER fixture_prerequisite_effect BEFORE "+event+' ON truss.'+table+' FOR EACH ROW EXECUTE FUNCTION truss.fixture_prerequisite_effect()')
    def assert_rolled_back(self):
        for table in ('catalog_acceptance_report','feed_tx','feed_member','feed_prerequisite','feed_configuration_prerequisite'):
            self.assertEqual(self.query('SELECT count(*) FROM truss.'+table).fetchone(),(0,))
        self.assertEqual(self.query('SELECT rev FROM truss.schema_head').fetchone(),(0,))
    def test_suppressed_or_rewritten_prerequisite_inserts_preserve_prior_host_work(self):
        self.stage();self.query("CREATE TEMP TABLE prior_work(value text); INSERT INTO prior_work VALUES('keep')")
        for table in ('feed_prerequisite','feed_configuration_prerequisite'):
            for body in ('RETURN NULL;',"NEW.original_owner_context_bytes:=decode('01','hex'); RETURN NEW;"):
                with self.subTest(table=table,body=body):
                    self.query('SAVEPOINT control');self.trigger(table,'INSERT',body)
                    result=self.register();self.assertIsInstance(result,Error)
                    self.assertIn(result.error.sql_state,('P0002','55000'))
                    self.assert_rolled_back()
                    self.assertEqual(self.query('TABLE prior_work').fetchall(),[('keep',)])
                    self.query('ROLLBACK TO control');self.query('RELEASE control')
    def test_extra_prerequisite_row_refuses_final_complete_delta(self):
        self.stage()
        self.query("""CREATE FUNCTION truss.fixture_extra_prerequisite() RETURNS trigger LANGUAGE plpgsql AS $$
          BEGIN IF NEW.prerequisite_address=1 THEN NEW.prerequisite_address:=2;
          INSERT INTO truss.feed_prerequisite SELECT NEW.*; END IF; RETURN NEW; END $$;
          CREATE TRIGGER fixture_extra_prerequisite AFTER INSERT ON truss.feed_prerequisite
          FOR EACH ROW EXECUTE FUNCTION truss.fixture_extra_prerequisite()""")
        result=self.register();self.assertIsInstance(result,Error);self.assertEqual(result.error.sql_state,'55000');self.assert_rolled_back()
    def test_late_configuration_change_refuses(self):
        self.stage()
        self.trigger('feed_configuration_prerequisite','INSERT',"UPDATE truss.installation_admission SET configuration_bytes=configuration_bytes||decode('20','hex'); RETURN NEW;")
        result=self.register();self.assertIsInstance(result,Error);self.assertEqual(result.error.sql_state,'55000');self.assert_rolled_back()
    def test_generation_artifact_stable_across_original_transactions(self):
        self.stage();self.assertIsInstance(self.register(),Ok)
        first=self.query('SELECT original_configuration_bytes FROM truss.feed_configuration_prerequisite').fetchone()[0]
        first_writer=self.writer
        self.connection.rollback();self.query('BEGIN');self.transaction=self.host.adopt_transaction().value
        self.stage();self.assertIsInstance(self.register(),Ok)
        second=self.query('SELECT original_configuration_bytes FROM truss.feed_configuration_prerequisite').fetchone()[0]
        self.assertNotEqual(self.writer,first_writer);self.assertEqual(first,second)
    def test_two_original_documents_each_have_one_exact_prerequisite(self):
        from truss import CatalogDocument
        from test_preparation import prepare,CONFIG
        from test_catalog_staging import native_document
        from truss._catalog_support import PROFILE
        import copy
        config=copy.deepcopy(CONFIG);config['supportProfile']=dict(PROFILE)
        first=json.loads(native_document('first').content);first['modules']=[]
        second=json.loads(native_document('second').content);second['modules']=[]
        docs=(CatalogDocument('first','r1',json.dumps(first).encode(),'artifact:first'),
              CatalogDocument('second','r2',json.dumps(second).encode(),'artifact:second'))
        self.prepared=prepare(docs,config)
        self.stage();result=self.register();self.assertIsInstance(result,Ok,str(self.host._custody.last_attempt.error))
        self.assertEqual(result.value[5:8],('2','1','4'))
        observed=self.query('SELECT original_artifact_identity_bytes,original_definition_bytes,original_definition_profile_bytes FROM truss.feed_prerequisite ORDER BY prerequisite_address').fetchall()
        self.assertEqual(observed,[(d.artifact_identity.encode(),d.content,canonical_numeric_free(carrier['umfProfile'])) for d,carrier in zip(docs,self.prepared.input()['documents'],strict=True)])
        import base64
        payload=json.loads(bytes.fromhex(result.value[4]))
        report=self.query('SELECT report_bytes FROM truss.catalog_acceptance_report').fetchone()[0]
        self.assertEqual(base64.b64decode(payload['report']['bytesBase64']),report)
        self.assertEqual(payload['report']['sha256'],hashlib.sha256(report).hexdigest())
        self.assertEqual(payload['input'],self.prepared.input())
        self.assertEqual(self.query('SELECT original_payload_bytes FROM truss.feed_member').fetchone()[0],bytes.fromhex(result.value[4]))
    def test_commit_barrier_still_refuses(self):
        self.stage();self.assertIsInstance(self.register(),Ok)
        with self.assertRaises(psycopg.errors.ObjectNotInPrerequisiteState) as caught:self.connection.commit()
        self.assertIn('complete runtime finalizer is not installed',str(caught.exception))
        self.assertEqual(self.query('SELECT count(*) FROM truss.feed_prerequisite').fetchone(),(0,))
    def test_after_collector_mutation_is_caught_by_final_rows(self):
        source=(ROOT/'packages/postgresql/native/catalog-completion/configured-prerequisite-state-candidate.sql').read_text()
        marker=' FOR name IN SELECT c.relname'
        injection=" IF EXISTS(SELECT 1 FROM truss.feed_configuration_prerequisite) THEN UPDATE truss.type_def SET retired_rev=1; END IF;\n"
        self.assertEqual(source.count(marker),1)
        self.query(source.replace('CREATE FUNCTION','CREATE OR REPLACE FUNCTION',1).replace(marker,injection+marker))
        self.stage();result=self.register();self.assertIsInstance(result,Error);self.assertEqual(result.error.sql_state,'55000');self.assert_rolled_back()
    def test_both_reservations_suppressed_or_rewritten_refuse_and_rollback(self):
        self.stage();self.query("CREATE TEMP TABLE reservation_prior(value text); INSERT INTO reservation_prior VALUES('keep')")
        for family in ('prerequisite_registration_counter','configuration_registration_counter'):
            for effect in ('RETURN NULL;','NEW.membership_generation:=NEW.membership_generation+1; RETURN NEW;'):
                with self.subTest(family=family,effect=effect):
                    self.query('SAVEPOINT reserve_control')
                    self.trigger('feed_tx','UPDATE',f'IF NEW.{family}>OLD.{family} THEN {effect} END IF; RETURN NEW;')
                    result=self.register();self.assertIsInstance(result,Error);self.assertIn(result.error.sql_state,('P0002','55000'));self.assert_rolled_back()
                    self.assertEqual(self.query('TABLE reservation_prior').fetchall(),[('keep',)])
                    self.query('ROLLBACK TO reserve_control');self.query('RELEASE reserve_control')
    def test_injected_resource_refusal_after_reservation_is_contained(self):
        self.stage();self.query("CREATE TEMP TABLE resource_prior(value text); INSERT INTO resource_prior VALUES('keep')")
        self.trigger('feed_prerequisite','INSERT',"RAISE EXCEPTION 'injected prerequisite resource refusal' USING ERRCODE='54000';")
        result=self.register();self.assertIsInstance(result,Error);self.assertEqual(result.error.sql_state,'54000')
        self.assert_rolled_back();self.assertEqual(self.query('TABLE resource_prior').fetchall(),[('keep',)])
    def test_owner_reservation_units_refuse_signed_int64_overflow(self):
        from psycopg import sql
        self.stage();self.assertIsInstance(self.register(),Ok)
        for family,name in [('prerequisite_registration_counter','catalog-reserve'),('configuration_registration_counter','configuration-reserve')]:
            with self.subTest(family=family):
                self.query('SAVEPOINT overflow_control')
                self.query(f'UPDATE truss.feed_tx SET {family}=9223372036854775807')
                row=self.query('SELECT source_epoch,feed_profile,membership_generation,original_context_bytes,manifest_profile_bytes FROM truss.feed_tx').fetchone()
                before=self.query("SELECT encode(record_send(t),'hex') FROM truss.feed_tx t").fetchall()
                source=(ROOT/f'packages/postgresql/native/catalog-report/prerequisite-statements/{name}.sql').read_text()
                self.query('PREPARE overflow_unit(text,text,bigint,bigint,bytea,bytea) AS '+source)
                command=sql.SQL('EXECUTE overflow_unit({})').format(sql.SQL(',').join(map(sql.Literal,(row[0],row[1],9223372036854775807,row[2],row[3],row[4]))))
                self.assertEqual(self.query(command).fetchall(),[])
                self.assertEqual(self.query("SELECT encode(record_send(t),'hex') FROM truss.feed_tx t").fetchall(),before)
                self.query('DEALLOCATE overflow_unit');self.query('ROLLBACK TO overflow_control');self.query('RELEASE overflow_control')

    def encode_revision(self,wire,report,*,old=False):
        def execute(cursor,observed):
            if old:
                cursor.execute('SELECT truss.runtime_canonical_tree_bytes(truss.runtime_catalog_report_native_tree(CAST(%s AS jsonb)))',(json.dumps(wire),),prepare=False)
            else:
                cursor.execute('SELECT truss.runtime_revision_report_tree_bytes_wide_candidate(truss.runtime_catalog_report_native_tree(CAST(%s AS jsonb)),%s)',(json.dumps(wire),report),prepare=False)
            self.assertEqual(cursor.description[0].type_code,17)
            return cursor.fetchone()[0]
        return self.host._run_operation(self.transaction,execute)
    def test_wide_report_exact_boundary_padding_and_independent_canonical_oracle(self):
        import base64
        for length in (1,2,3,49152,786430,786431,786432):
            with self.subTest(length=length):
                report=b'a'*length
                wire={'report':{'bytesBase64':base64.b64encode(report).decode(),'identity':'original','sha256':hashlib.sha256(report).hexdigest()},'origin':{'x-value':'é'}}
                actual=self.encode_revision(wire,report)
                self.assertIsInstance(actual,Ok,str(self.host._custody.last_attempt.error))
                self.assertEqual(actual.value,canonical_numeric_free(wire))
                if length<=49152:self.assertEqual(self.encode_revision(wire,report,old=True),actual)
    def test_wide_report_overflow_wrong_leaf_and_other_scalar_limits_refuse(self):
        import base64
        report=b'a'
        for wire,original in [({'report':{'bytesBase64':base64.b64encode(b'a'*786433).decode()}},b'a'*786433),
                              ({'report':{'bytesBase64':'wrong'}},report),
                              ({'report':{'bytesBase64':'YQ=='},'other':'x'*65537},report),
                              ({'report':{'bytesBase64':'YQ=='},'x'*65537:'value'},report),
                              ({'other':{'bytesBase64':'YQ=='}},report)]:
            self.assertIsInstance(self.encode_revision(wire,original),Error)
        large={'report':{'bytesBase64':'YQ=='},'many':['x'*65536]*33}
        self.assertIsInstance(self.encode_revision(large,report),Error)
    def test_old_report_profile_still_refuses_two_documents(self):
        from truss import CatalogDocument
        from test_preparation import prepare,CONFIG
        from test_catalog_staging import native_document
        from truss._catalog_support import PROFILE
        import copy
        config=copy.deepcopy(CONFIG);config['supportProfile']=dict(PROFILE)
        self.prepared=prepare((CatalogDocument('a','r1',native_document('a').content),CatalogDocument('b','r1',native_document('b').content)),config)
        self.use_old=True;self.stage()
        def execute(cursor,observed):
            cursor.execute('SELECT * FROM truss.runtime_write_catalog_report_and_register_revision_candidate(%s,%s,%s,%s,%s,%s,%s)',
              (self.writer,self.ordinal,self.generation,self.identity,self.registration,
               (ROOT/'packages/python/src/truss/_profiles/fresh-catalog-lifecycle.json').read_bytes(),
               (ROOT/'packages/python/src/truss/_profiles/absent-binding-index-declarations.json').read_bytes()),prepare=False)
            return cursor.fetchall()
        result=self.host._run_operation(self.transaction,execute)
        self.assertIsInstance(result,Error);self.assertEqual(result.error.sql_state,'54000');self.assert_rolled_back()

    def test_returning_substitution_refuses_even_after_exact_stored_restoration(self):
        self.stage();self.query('CREATE TEMP SEQUENCE observed_restore')
        self.trigger('feed_prerequisite','INSERT',"NEW.original_definition_bytes:=convert_to('substituted','UTF8'); RETURN NEW;")
        self.query("""CREATE FUNCTION truss.fixture_restore_prerequisite() RETURNS trigger LANGUAGE plpgsql AS $$
         BEGIN UPDATE truss.feed_prerequisite SET original_definition_bytes=(SELECT convert_to(document,'UTF8') FROM truss.schema_doc WHERE rev=NEW.original_revision)
          WHERE prerequisite_address=NEW.prerequisite_address;
         PERFORM nextval('pg_temp.observed_restore'); RETURN NEW; END $$;
         CREATE TRIGGER fixture_restore_prerequisite AFTER INSERT ON truss.feed_prerequisite FOR EACH ROW EXECUTE FUNCTION truss.fixture_restore_prerequisite()""")
        result=self.register();self.assertIsInstance(result,Error);self.assertEqual(result.error.sql_state,'55000')
        self.assertIn('complete prerequisite INSERT RETURNING correspondence required',str(self.host._custody.last_attempt.error))
        self.assertEqual(self.query('SELECT last_value,is_called FROM observed_restore').fetchone(),(1,True))
        self.assert_rolled_back()
    def test_late_feed_member_rewrite_refuses_final_cut(self):
        self.stage()
        self.trigger('feed_configuration_prerequisite','INSERT',"UPDATE truss.feed_member SET original_write_at='2000-01-01+00'; RETURN NEW;")
        result=self.register();self.assertIsInstance(result,Error);self.assertEqual(result.error.sql_state,'55000');self.assert_rolled_back()
    def test_changed_selected_wide_profile_refuses_without_fallback(self):
        self.changed_wide_profile=True;self.stage()
        result=self.register();self.assertIsInstance(result,Error);self.assertEqual(result.error.sql_state,'P0002');self.assert_rolled_back()
