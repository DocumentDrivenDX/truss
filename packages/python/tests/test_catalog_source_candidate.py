"""Original candidate custody and duplicate-preserving native source grammar."""
import dataclasses
import json
import unittest
from test_catalog_support import selected
from test_native_pg8000 import NativeBoundaryFixture
from test_catalog_staging import ROOT
from truss._catalog_candidate import encode_original_catalog_candidate
from truss._catalog_report_semantics import compose_original_catalog_report_semantics
from truss._catalog_support import evaluate_catalog_support


class OriginalCatalogCandidateTests(unittest.TestCase):
    def test_original_revision_free_sources_and_exact_evidence(self):
        prepared=selected()
        value=json.loads(encode_original_catalog_candidate(prepared))
        self.assertEqual(bytes.fromhex(value['declarationsUtf8Hex']),prepared.declarations_bytes)
        self.assertEqual(bytes.fromhex(value['reportEvidenceUtf8Hex']),prepared.report_evidence_bytes)
        self.assertEqual(value['preparationProvenance'],dataclasses.asdict(prepared.provenance))
        semantics=compose_original_catalog_report_semantics(prepared,evaluate_catalog_support(prepared))
        self.assertNotIn('catalogRevision',semantics)
        fields={bytes.fromhex(m['keyUtf8Hex']).decode() for m in value['hostSources']['members']}
        self.assertEqual(fields,{'umf','diagnostics','documentInterpretations','losses',
            'extensions','transformRegistrations','assertionEntries'})
    def test_copied_or_mutated_preparation_refused(self):
        prepared=selected()
        with self.assertRaises(ValueError):encode_original_catalog_candidate(dataclasses.replace(prepared))
        object.__setattr__(prepared,'report_evidence_bytes',b'{}')
        with self.assertRaises(ValueError):encode_original_catalog_candidate(prepared)


class NativeCatalogCandidateTests(NativeBoundaryFixture,unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        c=cls.Connection(**cls.kwargs)
        try:
            c.run('DROP SCHEMA IF EXISTS truss CASCADE')
            c.run('CREATE SCHEMA truss')
            for source in ('canonical-string-bytes','canonical-tree-bytes','catalog-report/source-candidate'):
                c.run((ROOT/f'packages/postgresql/native/{source}.sql').read_text())
        finally:c.close()
    def setUp(self):
        self.connection=self.Connection(**self.kwargs)
        self.prepared=selected();self.candidate=encode_original_catalog_candidate(self.prepared)
        self.connection.run('BEGIN')
    def tearDown(self):
        self.connection.run('ROLLBACK');self.connection.close()
    def collect(self,raw=None,declarations=None):
        return self.connection.run('SELECT * FROM truss.runtime_collect_catalog_source_candidate(:candidate,:declarations)',
            candidate=self.candidate if raw is None else raw,
            declarations=self.prepared.declarations_bytes if declarations is None else declarations)
    def test_exact_native_source_carrier(self):
        tree,evidence,provenance=self.collect()[0]
        self.assertEqual(tree,json.loads(self.candidate)['hostSources'])
        self.assertEqual(bytes(evidence),self.prepared.report_evidence_bytes)
        self.assertEqual(provenance,dataclasses.asdict(self.prepared.provenance))
    def test_duplicate_missing_unknown_and_substituted_sources_refused(self):
        from pg8000.exceptions import DatabaseError
        unknown=json.loads(self.candidate);unknown['hostSources']['members'][0]['keyUtf8Hex']=b'originalExecution'.hex()
        duplicate=json.loads(self.candidate);duplicate['hostSources']['members'][0]=duplicate['hostSources']['members'][1]
        missing=json.loads(self.candidate);missing['hostSources']['members'].pop()
        provenance=json.loads(self.candidate);provenance['preparationProvenance']['installation_profiles_verified']=True
        extra=json.loads(self.candidate);extra['preparationProvenance']['assumedAuthority']=True
        wrong_type=json.loads(self.candidate);wrong_type['hostSources']['members'][0]['node']={'kind':'null'}
        cases=[self.candidate.replace(b'{',b'{"interfaceVersion":"wrong",',1),
            self.candidate.replace(b'"kind":"object"',b'"kind":"object","kind":"object"',1),
            json.dumps(unknown).encode(),json.dumps(duplicate).encode(),json.dumps(missing).encode(),
            json.dumps(provenance).encode(),json.dumps(extra).encode(),json.dumps(wrong_type).encode()]
        self.connection.run('CREATE TEMP TABLE earlier_host_work(value text)')
        self.connection.run("INSERT INTO earlier_host_work VALUES('keep')")
        for raw in cases:
            self.connection.run('SAVEPOINT source')
            with self.subTest(raw=raw[:60]),self.assertRaises(DatabaseError):self.collect(raw)
            self.connection.run('ROLLBACK TO SAVEPOINT source')
            self.connection.run('RELEASE SAVEPOINT source')
        self.connection.run('SAVEPOINT source')
        with self.assertRaises(DatabaseError):self.collect(declarations=b'[]')
        self.connection.run('ROLLBACK TO SAVEPOINT source')
        self.assertEqual(self.connection.run('SELECT value FROM earlier_host_work'),[['keep']])


class ConfiguredCatalogSourceStageTests(NativeBoundaryFixture,unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        from test_catalog_staging import COMPONENTS
        c=cls.Connection(**cls.kwargs)
        try:
            c.run('DROP SCHEMA IF EXISTS truss CASCADE')
            c.run((ROOT/'docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql').read_text())
            c.run((ROOT/'docs/helix/04-build/evidence/operation-configuration-storage.owner-export.sql').read_text())
            for component in COMPONENTS:c.run((ROOT/f'packages/postgresql/native/{component}.sql').read_text())
            for source in ('issued-operation-admission/operation-admission','source-epoch-lock',
                'issued-operation-admission/operation-configuration-context-admission',
                'catalog-epoch-context','operation-configuration-current','catalog-admission-configuration',
                'canonical-string-bytes','canonical-tree-bytes','catalog-report/source-candidate',
                'catalog-report/release-selection','catalog-report/configured-metadata',
                'catalog-report/configured-graph','catalog-report/configured-stage',
                'catalog-report/empty-graph','catalog-report/fresh-lifecycle',
                'catalog-report/absent-binding-index-declarations','edge-limit/verify-current-scope','catalog-stage-issued'):
                c.run((ROOT/f'packages/postgresql/native/{source}.sql').read_text())
            fixture=(ROOT/'docs/helix/04-build/evidence/design-audit/pgserver-populated-guard-fixture.sql').read_text()
            c.run(fixture.split('INSERT INTO truss.row_home_operation')[0])
            c.run("INSERT INTO truss.source_epoch_current VALUES(1,'guard-fixture','guard-fixture-epoch')")
        finally:c.close()
    def setUp(self):
        import hashlib
        self.connection=self.Connection(**self.kwargs);self.prepared=selected()
        self.candidate=encode_original_catalog_candidate(self.prepared)
        policy=(ROOT/'packages/python/src/truss/_profiles/catalog-report-release.json').read_bytes()
        self.configuration_profile=(ROOT/'packages/python/src/truss/_profiles/catalog-report-configuration.json').read_bytes()
        configuration=json.dumps({'interfaceVersion':'truss-catalog-report-configuration/0.1',
            'catalogReportRelease':{'artifactIdentity':'truss.catalog-report-release/0.1.0',
            'sha256':hashlib.sha256(policy).hexdigest()}}).encode()
        self.connection.run("""INSERT INTO truss.installation_admission(head_id,installation_id_utf8,
            source_epoch_utf8,configuration_generation,key_reuse,journal_mode,configuration_bytes,
            selected_binding_bytes,installed_inventory_bytes) VALUES(1,convert_to('guard-fixture','UTF8'),
            convert_to('guard-fixture-epoch','UTF8'),7,'forbid','engine',:configuration,
            convert_to('binding fixture','UTF8'),convert_to('inventory fixture','UTF8'))""",configuration=configuration)
        self.connection.run('BEGIN')
        self.connection.run("""INSERT INTO truss.installation_archive(installation_id,artifact_role,
            artifact_identity,artifact_bytes,artifact_identity_sha256) VALUES('guard-fixture','input',
            'truss.catalog-report-release/0.1.0',:raw,sha256(convert_to('truss.catalog-report-release/0.1.0','UTF8')))""",raw=policy)
    def tearDown(self):
        self.connection.run('ROLLBACK');self.connection.run('DELETE FROM truss.installation_admission');self.connection.close()
    def admit(self):
        # Epoch exclusion precedes prestate's catalog head lock.
        self.connection.run("SELECT * FROM truss.runtime_lock_source_epoch('guard-fixture','guard-fixture-epoch','guard-fixture-incarnation')")
        self.prestate=bytes.fromhex(self.connection.run('SELECT truss.runtime_capture_catalog_prestate()')[0][0])
        self.context=self.connection.run("""SELECT * FROM truss.runtime_admit_operation_with_configuration_context(
            0,'catalog-acceptance',decode('01','hex'),:input,:prestate,:candidate,
            decode('05','hex'),decode('06','hex'),convert_to('{}','UTF8'),
            convert_to('original capture fixture','UTF8'),'guard-fixture','guard-fixture-epoch',
            'guard-fixture-incarnation',:configuration_profile)""",input=self.prepared.input_bytes,
            prestate=self.prestate,candidate=self.candidate,configuration_profile=self.configuration_profile)[0]
    def stage(self,origin=b'{}'):
        return self.connection.run("""SELECT * FROM truss.runtime_stage_catalog_admitted(
            0,decode('01','hex'),:input,:candidate,decode('05','hex'),decode('06','hex'),
            :documents,:declarations,:origin,:prestate,:context)""",input=self.prepared.input_bytes,
            candidate=self.candidate,documents=self.prepared.archive_documents_bytes,
            declarations=self.prepared.declarations_bytes,origin=origin,prestate=self.prestate,
            context=bytes.fromhex(self.context[2]))
    def test_original_configuration_source_envelope_stages_actual_catalog(self):
        self.admit();row=self.stage()[0]
        result=json.loads(bytes.fromhex(row[3]))
        self.assertEqual(result['counts']['types_added'],'1')
        self.assertEqual(result['counts']['properties_added'],'1')
        self.assertEqual(self.connection.run('SELECT home FROM truss.prop_def'),[['json']])
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.operation_configuration'),[[1]])
        self.assertEqual(self.connection.run('SELECT rev FROM truss.schema_head'),[[0]])
        self.assertFalse(result['accepted'])
    def test_changed_metadata_and_second_origin_refuse_before_catalog_effects(self):
        from pg8000.exceptions import DatabaseError
        self.admit()
        for source in ('configuration','origin','marker'):
            self.connection.run('SAVEPOINT stage')
            if source=='configuration':self.connection.run("UPDATE truss.installation_admission SET journal_mode='trigger'")
            if source=='marker':self.connection.run("UPDATE truss.installation_marker SET schema_name='other'")
            with self.subTest(source=source),self.assertRaises(DatabaseError):
                self.stage(b'{"other":true}' if source=='origin' else b'{}')
            self.connection.run('ROLLBACK TO SAVEPOINT stage');self.connection.run('RELEASE SAVEPOINT stage')
            self.assertEqual(self.connection.run('SELECT count(*) FROM truss.type_def'),[[0]])

    def test_late_marker_change_refuses_and_preserves_host_work(self):
        from pg8000.exceptions import DatabaseError
        self.connection.run('CREATE TEMP TABLE catalog_host_work(value text)')
        self.connection.run("INSERT INTO catalog_host_work VALUES('keep')")
        self.connection.run("""CREATE FUNCTION truss.test_late_marker_change() RETURNS trigger
            LANGUAGE plpgsql AS $$ BEGIN
            UPDATE truss.installation_marker SET layout_version='late-change'; RETURN NEW; END $$""")
        self.connection.run('CREATE TRIGGER test_late_marker AFTER INSERT ON truss.prop_def FOR EACH ROW EXECUTE FUNCTION truss.test_late_marker_change()')
        self.admit();self.connection.run('SAVEPOINT stage')
        with self.assertRaises(DatabaseError) as caught:self.stage()
        self.assertEqual(caught.exception.args[0]['C'],'55000')
        self.connection.run('ROLLBACK TO SAVEPOINT stage')
        self.assertEqual(self.connection.run('SELECT value FROM catalog_host_work'),[['keep']])
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.type_def'),[[0]])
        self.assertEqual(self.connection.run('SELECT layout_version FROM truss.installation_marker'),[['component-fixture']])

    def test_plain_candidate_cannot_bypass_configured_checks(self):
        from pg8000.exceptions import DatabaseError
        self.candidate=self.prepared.declarations_bytes
        self.connection.run('DELETE FROM truss.installation_archive')
        self.admit();self.connection.run('SAVEPOINT stage')
        with self.assertRaises(DatabaseError) as caught:self.stage(b'{"wrong":true}')
        self.assertEqual(caught.exception.args[0]['C'],'22023')
        self.connection.run('ROLLBACK TO SAVEPOINT stage')
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.type_def'),[[0]])

    def test_concurrent_release_insert_after_selection_is_fenced(self):
        import queue
        import threading
        import time
        from pg8000.exceptions import DatabaseError
        self.connection.run('CREATE SEQUENCE truss.test_release_calls')
        self.connection.run('CREATE TEMP SEQUENCE first_catalog_insert')
        self.connection.run("""CREATE FUNCTION truss.test_first_catalog_insert() RETURNS trigger
            LANGUAGE plpgsql AS $$ BEGIN PERFORM nextval('pg_temp.first_catalog_insert'); RETURN NEW; END $$""")
        self.connection.run('CREATE TRIGGER test_first_catalog_insert BEFORE INSERT ON truss.schema_rev FOR EACH ROW EXECUTE FUNCTION truss.test_first_catalog_insert()')
        self.connection.run('ALTER FUNCTION truss.runtime_select_catalog_report_release(text,text,text,text) RENAME TO test_original_release_selector')
        self.connection.run("""CREATE FUNCTION truss.runtime_select_catalog_report_release(w text,o text,g text,p text)
            RETURNS TABLE(policy_hex text,policy_sha256 text,configuration_generation text)
            LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
            DECLARE original record;
            BEGIN SELECT * INTO STRICT original FROM truss.test_original_release_selector(w,o,g,p);
            IF nextval('truss.test_release_calls')=1 THEN PERFORM pg_advisory_xact_lock(919011); END IF;
            RETURN QUERY SELECT original.policy_hex,original.policy_sha256,original.configuration_generation;
            END $$""")
        self.admit();pid=int(json.loads(bytes.fromhex(self.context[2]))['backendPid'])
        self.connection.run('SAVEPOINT stage_window')
        other=self.Connection(**self.kwargs);outcomes=queue.Queue()
        def run_stage():
            try:outcomes.put(self.stage())
            except BaseException as error:outcomes.put(error)
        worker=threading.Thread(target=run_stage,daemon=True)
        try:
            other.run('SELECT pg_advisory_lock(919011)');worker.start()
            deadline=time.monotonic()+5
            while time.monotonic()<deadline:
                waiting=other.run("SELECT EXISTS(SELECT 1 FROM pg_locks WHERE pid=:pid AND locktype='advisory' AND objid=919011 AND NOT granted)",pid=pid)[0][0]
                if waiting:break
                if not worker.is_alive():break
                time.sleep(0.02)
            self.assertTrue(waiting,'stage did not reach the controlled inter-call window')
            other.run("SET lock_timeout='100ms'")
            with self.assertRaises(DatabaseError) as blocked:
                other.run("""INSERT INTO truss.installation_archive(installation_id,artifact_role,
                artifact_identity,artifact_bytes,artifact_identity_sha256)
                VALUES('guard-fixture','input','truss.catalog-report-release/0.1.0',
                convert_to('conflicting concurrent bytes','UTF8'),
                sha256(convert_to('truss.catalog-report-release/0.1.0','UTF8')))""")
            self.assertEqual(blocked.exception.args[0]['C'],'55P03')
        finally:
            other.run('SELECT pg_advisory_unlock(919011)');other.close();worker.join(10)
        self.assertFalse(worker.is_alive())
        result=outcomes.get_nowait()
        if isinstance(result,BaseException):raise result
        self.assertFalse(json.loads(bytes.fromhex(result[0][3]))['accepted'])
        # Sequence effects survive statement rollback and prove ordering.
        self.connection.run('ROLLBACK TO SAVEPOINT stage_window')
        self.assertEqual(self.connection.run('SELECT is_called FROM pg_temp.first_catalog_insert'),[[True]])
        self.connection.run('ROLLBACK')
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.schema_rev'),[[1]])
        self.connection.run("DELETE FROM truss.installation_archive WHERE artifact_bytes=convert_to('conflicting concurrent bytes','UTF8')")
        self.connection.run('BEGIN')

    def test_same_writer_release_duplicate_after_selection_refuses_before_catalog_insert(self):
        from pg8000.exceptions import DatabaseError
        self.connection.run('CREATE TEMP SEQUENCE first_catalog_insert')
        self.connection.run("""CREATE FUNCTION truss.test_first_catalog_insert() RETURNS trigger
            LANGUAGE plpgsql AS $$ BEGIN PERFORM nextval('pg_temp.first_catalog_insert'); RETURN NEW; END $$""")
        self.connection.run('CREATE TRIGGER test_first_catalog_insert BEFORE INSERT ON truss.schema_rev FOR EACH ROW EXECUTE FUNCTION truss.test_first_catalog_insert()')
        self.connection.run('CREATE SEQUENCE truss.test_release_calls')
        self.connection.run('ALTER FUNCTION truss.runtime_select_catalog_report_release(text,text,text,text) RENAME TO test_original_release_selector')
        self.connection.run("""CREATE FUNCTION truss.runtime_select_catalog_report_release(w text,o text,g text,p text)
            RETURNS TABLE(policy_hex text,policy_sha256 text,configuration_generation text)
            LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
            DECLARE original record;
            BEGIN SELECT * INTO STRICT original FROM truss.test_original_release_selector(w,o,g,p);
            IF nextval('truss.test_release_calls')=1 THEN
              INSERT INTO truss.installation_archive(installation_id,artifact_role,artifact_identity,
                artifact_bytes,artifact_identity_sha256) VALUES('guard-fixture','input',
                'truss.catalog-report-release/0.1.0',convert_to('late same writer bytes','UTF8'),
                sha256(convert_to('truss.catalog-report-release/0.1.0','UTF8')));
            END IF;
            RETURN QUERY SELECT original.policy_hex,original.policy_sha256,original.configuration_generation;
            END $$""")
        self.admit();self.connection.run('SAVEPOINT stage')
        with self.assertRaises(DatabaseError) as caught:self.stage()
        self.assertEqual(caught.exception.args[0]['C'],'55000')
        self.connection.run('ROLLBACK TO SAVEPOINT stage')
        self.assertEqual(self.connection.run('SELECT is_called FROM pg_temp.first_catalog_insert'),[[False]])
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.type_def'),[[0]])
