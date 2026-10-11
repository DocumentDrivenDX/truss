"""Configured native stage/source composition. Administrative fixtures, no PA authority."""
import copy,hashlib,json,unittest
from test_native_pg8000 import NativeBoundaryFixture
from test_catalog_staging import ROOT,COMPONENTS
from test_catalog_support import selected
from truss._native_catalog_request import NativeCatalogStageInput,ConfiguredCatalogSelection,encode_catalog_stage
from truss._catalog_candidate import encode_original_catalog_candidate
from truss._native_catalog_report_sources import compose_captured_catalog_sources
FENCE_SOURCE=(ROOT/'packages/postgresql/native/catalog-report/archive-self-write-fence.sql').read_text()
FENCE_BODY=FENCE_SOURCE.split('AS $$',1)[1].split('$$;',1)[0]
ALTERED_FENCE_BODY='\nBEGIN RETURN NULL; END;\n'.ljust(len(FENCE_BODY.encode('utf8')))
ALTERED_FENCE_DEFINITION="CREATE OR REPLACE FUNCTION truss.runtime_fence_selected_archive_writes() RETURNS trigger LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $inner$"+ALTERED_FENCE_BODY+"$inner$"
SET_FENCE_DEFINITION="DROP TRIGGER runtime_selected_archive_write_fence ON truss.installation_archive; DROP FUNCTION truss.runtime_fence_selected_archive_writes(); "+FENCE_SOURCE.replace('RETURNS trigger','RETURNS SETOF trigger',1)
DEFAULT_ACL_FENCE_DEFINITION="DROP TRIGGER runtime_selected_archive_write_fence ON truss.installation_archive; DROP FUNCTION truss.runtime_fence_selected_archive_writes(); "+FENCE_SOURCE.replace('REVOKE ALL ON FUNCTION truss.runtime_fence_selected_archive_writes() FROM PUBLIC;','-- Deliberate default PUBLIC ACL retained.')

class ConfiguredReleaseStageNativeTests(NativeBoundaryFixture,unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass();c=cls.Connection(**cls.kwargs)
        try:
            c.run('DROP SCHEMA IF EXISTS truss CASCADE')
            c.run((ROOT/'docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql').read_text())
            c.run((ROOT/'docs/helix/04-build/evidence/operation-configuration-storage.owner-export.sql').read_text())
            for name in COMPONENTS:
                if name!='operation-admission':c.run((ROOT/f'packages/postgresql/native/{name}.sql').read_text())
            for name in ('source-epoch-lock','issued-operation-admission/operation-admission',
                         'issued-operation-admission/operation-configuration-context-admission',
                         'catalog-epoch-context','operation-configuration-current','catalog-admission-configuration',
                         'canonical-string-bytes','canonical-tree-bytes','catalog-report/release-selection','catalog-report/source-candidate','catalog-report/configured-metadata','catalog-report/empty-graph',
                         'catalog-report/configured-graph','catalog-report/absent-binding-index-declarations',
                         'catalog-report/fresh-lifecycle','edge-limit/verify-current-scope',
                         'catalog-stage-issued','catalog-report/resource-selection','catalog-report/archive-self-write-fence','catalog-report/archive-write-fence-current','catalog-report/configured-stage'):
                c.run((ROOT/f'packages/postgresql/native/{name}.sql').read_text())
            fixture=(ROOT/'docs/helix/04-build/evidence/design-audit/pgserver-populated-guard-fixture.sql').read_text()
            c.run(fixture.split('INSERT INTO truss.row_home_operation')[0])
            c.run("INSERT INTO truss.source_epoch_current VALUES(1,'guard-fixture','guard-fixture-epoch')")
        finally:c.close()
    @classmethod
    def tearDownClass(cls):
        c=cls.Connection(**cls.kwargs)
        try:c.run('DROP SCHEMA truss CASCADE')
        finally:c.close()
        super().tearDownClass()
    def setUp(self):
        self.connection=self.Connection(**self.kwargs);self.prepared=selected()
        self.policy=(ROOT/'packages/python/src/truss/_profiles/catalog-report-release.json').read_bytes()
        self.profile=(ROOT/'packages/python/src/truss/_profiles/catalog-report-configuration.json').read_bytes()
        self.configuration=json.dumps({'interfaceVersion':'truss-catalog-report-configuration/0.1',
            'catalogReportRelease':{'artifactIdentity':'truss.catalog-report-release/0.1.0',
                                  'sha256':hashlib.sha256(self.policy).hexdigest()}}).encode()
        self.connection.run("""INSERT INTO truss.installation_admission(head_id,installation_id_utf8,
            source_epoch_utf8,configuration_generation,key_reuse,journal_mode,configuration_bytes,
            selected_binding_bytes,installed_inventory_bytes) VALUES(1,convert_to('guard-fixture','UTF8'),
            convert_to('guard-fixture-epoch','UTF8'),7,'forbid','engine',:configuration,
            convert_to('binding fixture','UTF8'),convert_to('inventory fixture','UTF8'))""",configuration=self.configuration)
        self.connection.run('BEGIN')
    def tearDown(self):
        self.connection.run('ROLLBACK');self.connection.run('DELETE FROM truss.installation_admission');self.connection.close()
    def archive(self):
        self.connection.run("""INSERT INTO truss.installation_archive(installation_id,artifact_role,
            artifact_identity,artifact_bytes,artifact_identity_sha256) VALUES('guard-fixture','input',
            'truss.catalog-report-release/0.1.0',:raw,sha256(convert_to('truss.catalog-report-release/0.1.0','UTF8')))""",raw=self.policy)
        for item in json.loads(self.policy)['resources']:
            self.connection.run("""INSERT INTO truss.installation_archive(installation_id,artifact_role,
                artifact_identity,artifact_bytes,artifact_identity_sha256) VALUES('guard-fixture','input',
                :identity,:raw,sha256(convert_to(:identity,'UTF8')))""",identity=item['path'],raw=(ROOT/item['path']).read_bytes())
    def admit(self):
        p=self.prepared;pre=self.connection.run('SELECT truss.runtime_capture_catalog_prestate()')[0][0]
        writer,ordinal,context=self.connection.run("""SELECT * FROM truss.runtime_admit_operation_with_configuration_context(
            0,'catalog-acceptance',decode('01','hex'),:input,decode(:pre,'hex'),:candidate,
            decode('05','hex'),decode('06','hex'),convert_to('{}','UTF8'),
            convert_to('original capture fixture','UTF8'),'guard-fixture','guard-fixture-epoch',
            'guard-fixture-incarnation',:profile)""",input=p.input_bytes,pre=pre,candidate=encode_original_catalog_candidate(p),profile=self.profile)[0]
        self.context=bytes.fromhex(context);self.prestate=bytes.fromhex(pre);return writer,ordinal
    def invoke(self):
        p=self.prepared
        rows=self.connection.run("""SELECT * FROM truss.runtime_stage_catalog_with_release(0,
            decode('01','hex'),:input,:candidate,decode('05','hex'),decode('06','hex'),
            :documents,:declarations,convert_to('{}','UTF8'),:pre,:context,:profile)""",
            input=p.input_bytes,candidate=encode_original_catalog_candidate(p),declarations=p.declarations_bytes,documents=p.archive_documents_bytes,
            pre=self.prestate,context=self.context,profile=self.profile)
        self.result=json.loads(bytes.fromhex(rows[0][3]));return rows[0]
    def compose(self,result=None,context=None,profile=None):
        value=NativeCatalogStageInput(self.prepared,b'{}',b'\x01',b'\x05',b'\x06',
            ConfiguredCatalogSelection('guard-fixture','guard-fixture-epoch','guard-fixture-incarnation',
                b'original capture fixture',self.profile if profile is None else profile))
        encoded=encode_catalog_stage(value,'0')
        return compose_captured_catalog_sources(encoded,self.result if result is None else result,
            self.context if context is None else context)
    def test_one_configured_native_stage_retains_release_and_metadata(self):
        self.archive();writer,ordinal=self.admit();row=self.invoke();snapshot=self.compose()
        result=self.result;source=result['reportSources']['catalogRelease']
        self.assertEqual((row[0],row[1]),(writer,ordinal))
        self.assertEqual(result['interfaceVersion'],'truss-native-provisional-catalog/0.4')
        resources=result['reportSources']['catalogResources']
        self.assertEqual([(r['path'],r['sha256']) for r in resources['resources']],[(r['path'],r['sha256']) for r in json.loads(self.policy)['resources']])
        observed=self.connection.run("SELECT artifact_identity,archive_row_id::text,octet_length(artifact_bytes)::text,encode(artifact_sha256,'hex'),encode(sha256(artifact_bytes),'hex') FROM truss.installation_archive WHERE artifact_identity=ANY(:paths)",paths=[r['path'] for r in json.loads(self.policy)['resources']])
        expected={row[0]:row[1:] for row in observed}
        self.assertEqual(len(expected),21)
        self.assertEqual({r['path']:[r['archiveRowId'],r['bytes'],r['sha256'],r['sha256']] for r in resources['resources']},expected)
        self.assertEqual(resources['totalBytes'],str(sum((ROOT/r['path']).stat().st_size for r in json.loads(self.policy)['resources'])))
        self.assertEqual(source['policyHex'],self.policy.hex());self.assertEqual(source['configurationGeneration'],'7')
        self.assertEqual(source['effectGeneration'],result['effectGeneration'])
        self.assertEqual(result['reportSources']['start']['metadata_source'],result['reportSources']['end']['metadata_source'])
        payload=json.loads(snapshot.snapshot_bytes);assembly=json.loads(snapshot.assembly_bytes)
        self.assertFalse(payload['configuredReleaseCandidate']['registeredAuthority'])
        self.assertEqual(len(assembly['requiredSources']),4);self.assertIsNone(assembly['completeReportBytes'])
        self.assertEqual(self.connection.run('SELECT home FROM truss.prop_def'),[['json']])
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.catalog_acceptance_report'),[[0]])
        self.assertEqual(self.connection.run('SELECT rev FROM truss.schema_head'),[[0]])
        self.connection.run('ROLLBACK')
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.type_def'),[[0]])
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.operation_configuration'),[[0]])
    def test_missing_release_refuses_before_any_catalog_effect(self):
        from pg8000.exceptions import DatabaseError
        self.admit()
        self.connection.run("CREATE TEMP SEQUENCE catalog_first_effect; CREATE FUNCTION truss.fixture_first_effect() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN PERFORM nextval('pg_temp.catalog_first_effect'); RETURN NEW; END $$; CREATE TRIGGER fixture_first_effect BEFORE INSERT ON truss.schema_rev FOR EACH ROW EXECUTE FUNCTION truss.fixture_first_effect()")
        self.connection.run('SAVEPOINT attempt')
        with self.assertRaises(DatabaseError) as caught:self.invoke()
        self.assertEqual(caught.exception.args[0]['C'],'55000')
        self.assertEqual(caught.exception.args[0]['M'],'unique original report release archive required')
        self.connection.run('ROLLBACK TO SAVEPOINT attempt')
        self.assertEqual(self.connection.run('SELECT is_called FROM pg_temp.catalog_first_effect'),[[False]])
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.type_def'),[[0]])
    def test_uncovered_or_populated_graph_still_refuses(self):
        from pg8000.exceptions import DatabaseError
        self.archive();self.admit()
        for statement in ('CREATE TABLE truss.uncovered(value text)',
                          "INSERT INTO truss.request_receipt_route_guard VALUES(decode(repeat('00',32),'hex'),decode(repeat('01',32),'hex'),0)"):
            self.connection.run('SAVEPOINT graph');self.connection.run(statement)
            with self.assertRaises(DatabaseError):self.invoke()
            self.connection.run('ROLLBACK TO SAVEPOINT graph');self.connection.run('RELEASE SAVEPOINT graph')
    def test_configured_source_substitutions_never_issue_report(self):
        self.archive();self.admit();self.invoke()
        for path,value in ((('catalogRelease','policyHex'),'00'),(('catalogRelease','configurationGeneration'),'8'),
                           (('catalogRelease','effectGeneration'),'0'),(('end','metadata_source'),'{}')):
            changed=copy.deepcopy(self.result);changed['reportSources'][path[0]][path[1]]=value
            with self.assertRaises(ValueError):self.compose(changed)
        changed=copy.deepcopy(self.result)
        for cut in ('start','end'):
            scope=json.loads(changed['reportSources'][cut]['empty_scope'])
            changed['reportSources'][cut]['empty_scope']=json.dumps({**scope,'businessRelations':scope['businessRelations']+['source_epoch_registry','source_epoch_current']})
        with self.assertRaises(ValueError):self.compose(changed)
        changed=copy.deepcopy(self.result);changed['interfaceVersion']='truss-native-provisional-catalog/0.3'
        del changed['reportSources']['catalogResources']
        with self.assertRaises(ValueError):self.compose(changed)
        changed=copy.deepcopy(self.result);changed['interfaceVersion']='truss-native-provisional-catalog/0.2'
        del changed['reportSources']['catalogRelease'];del changed['reportSources']['catalogResources']
        for cut in ('start','end'):
            del changed['reportSources'][cut]['metadata_source']
            changed['reportSources'][cut]['empty_scope']=json.dumps(json.loads(changed['reportSources'][cut]['empty_scope'])['businessRelations'])
        with self.assertRaises(ValueError):self.compose(changed)
        changed=json.loads(self.context);changed['sourceEpoch']='other'
        with self.assertRaises(ValueError):self.compose(context=json.dumps(changed).encode())
        changed=copy.deepcopy(self.result)
        for cut in ('start','end'):
            scope=json.loads(changed['reportSources'][cut]['empty_scope'])
            full=json.loads(bytes.fromhex(scope['metadataUtf8Hex']))
            full['epoch']['transition_reason']='restore';full['epoch']['predecessor_epoch']='earlier'
            scope['metadataUtf8Hex']=json.dumps(full).encode().hex()
            changed['reportSources'][cut]['empty_scope']=json.dumps(scope)
        with self.assertRaises(ValueError):self.compose(changed)
        for field,value in (('configurationGeneration','8'),('configurationSha256','ab'*32),
                            ('selectedBindingSha256','ab'*32),('installedInventorySha256','ab'*32)):
            changed=copy.deepcopy(self.result)
            for cut in ('start','end'):
                metadata=json.loads(changed['reportSources'][cut]['metadata_source']);metadata[field]=value
                changed['reportSources'][cut]['metadata_source']=json.dumps(metadata)
            if field=='configurationGeneration':changed['reportSources']['catalogRelease']['configurationGeneration']=value
            with self.assertRaises(ValueError):self.compose(changed)
        with self.assertRaises(ValueError):self.compose(profile=b'changed configuration profile')
        for mutation in ('missing','duplicate','hash','size','total','extra','row_duplicate','row_domain','release_row','order','writer','ordinal','configuration','release'):
            changed=copy.deepcopy(self.result);source=changed['reportSources']['catalogResources']
            if mutation=='missing':source['resources'].pop()
            elif mutation=='duplicate':source['resources'][1]=source['resources'][0]
            elif mutation=='hash':source['resources'][0]['sha256']='ab'*32
            elif mutation=='size':source['resources'][0]['bytes']='01'
            elif mutation=='total':source['totalBytes']='1'
            elif mutation=='row_duplicate':source['resources'][1]['archiveRowId']=source['resources'][0]['archiveRowId']
            elif mutation=='row_domain':source['resources'][0]['archiveRowId']='0'
            elif mutation=='release_row':
                scope=json.loads(changed['reportSources']['start']['empty_scope'])
                source['resources'][0]['archiveRowId']=str(json.loads(bytes.fromhex(scope['metadataUtf8Hex']))['releaseArchive'][0]['archive_row_id'])
            elif mutation=='order':source['resources'].reverse()
            elif mutation=='writer':source['writerXid']='1'
            elif mutation=='ordinal':source['operationOrdinal']='1'
            elif mutation=='configuration':source['configurationGeneration']='8'
            elif mutation=='release':source['releaseSha256']='ab'*32
            else:source['extra']='unexpected'
            with self.assertRaises(ValueError):self.compose(changed)
        for mutation in ('foreign','origin','capture','missing','extra','array'):
            changed=json.loads(self.context)
            if mutation=='foreign':changed['sourceEpoch']='other'
            elif mutation=='origin':changed['assertedOriginUtf8Hex']=b'{"different":true}'.hex()
            elif mutation=='capture':changed['assertedOriginCaptureProfileHex']=b'other profile'.hex()
            elif mutation=='missing':del changed['database']
            elif mutation=='extra':changed['extra']='unexpected'
            else:changed=[]
            raw=json.dumps(changed).encode();response=copy.deepcopy(self.result)
            for cut in ('start','end'):
                metadata=json.loads(response['reportSources'][cut]['metadata_source'])
                metadata['contextSha256']=hashlib.sha256(raw).hexdigest()
                if mutation=='foreign':metadata['sourceEpoch']='other'
                response['reportSources'][cut]['metadata_source']=json.dumps(metadata)
            with self.assertRaises(ValueError):self.compose(response,raw)
        changed=copy.deepcopy(self.result);del changed['reportSources']['catalogRelease']
        with self.assertRaises(ValueError):self.compose(changed)

    def test_resource_archive_damage_refuses_before_first_catalog_effect(self):
        from pg8000.exceptions import DatabaseError
        self.archive();self.admit()
        identity=json.loads(self.policy)['resources'][0]['path']
        self.connection.run("CREATE TEMP SEQUENCE resource_first_effect; CREATE FUNCTION truss.resource_fixture_first_effect() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN PERFORM nextval('pg_temp.resource_first_effect'); RETURN NEW; END $$; CREATE TRIGGER resource_fixture_first_effect BEFORE INSERT ON truss.schema_rev FOR EACH ROW EXECUTE FUNCTION truss.resource_fixture_first_effect()")
        cases=[("DELETE FROM truss.installation_archive WHERE artifact_identity=:identity",'55000','unique original report resource archive required'),
            ("INSERT INTO truss.installation_archive(installation_id,artifact_role,artifact_identity,artifact_bytes,artifact_identity_sha256) SELECT installation_id,artifact_role,artifact_identity,artifact_bytes,artifact_identity_sha256 FROM truss.installation_archive WHERE artifact_identity=:identity",'55000','unique original report resource archive required'),
            ("UPDATE truss.installation_archive SET artifact_bytes=decode('00','hex') WHERE artifact_identity=:identity",'55000','original report resource digest correspondence required'),
            ("UPDATE truss.installation_archive SET artifact_bytes=convert_to(repeat('x',1048577),'UTF8') WHERE artifact_identity=:identity",'54000','original report resource retained byte capacity exceeded')]
        for sql,code,message in cases:
            self.connection.run('SAVEPOINT resource_damage');self.connection.run(sql,identity=identity)
            with self.assertRaises(DatabaseError) as caught:self.invoke()
            self.assertEqual(caught.exception.args[0]['C'],code);self.assertEqual(caught.exception.args[0]['M'],message)
            self.connection.run('ROLLBACK TO SAVEPOINT resource_damage');self.connection.run('RELEASE SAVEPOINT resource_damage')
            self.assertEqual(self.connection.run('SELECT is_called FROM pg_temp.resource_first_effect'),[[False]])
            self.assertEqual(self.connection.run('SELECT count(*) FROM truss.type_def'),[[0]])

    def test_same_writer_resource_change_during_effect_refuses_and_rolls_back(self):
        from pg8000.exceptions import DatabaseError
        self.archive();self.admit();identity=json.loads(self.policy)['resources'][0]['path']
        self.connection.run("CREATE TEMP SEQUENCE resource_late_effect; CREATE FUNCTION truss.resource_fixture_late_effect() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN PERFORM nextval('pg_temp.resource_late_effect'); UPDATE truss.installation_archive SET artifact_bytes=convert_to(repeat('x',octet_length(artifact_bytes)),'UTF8') WHERE artifact_identity='packages/python/src/truss/_report_schemas/exact-value-v0.1.schema.json'; RETURN NEW; END $$; CREATE TRIGGER resource_fixture_late_effect BEFORE INSERT ON truss.schema_rev FOR EACH ROW EXECUTE FUNCTION truss.resource_fixture_late_effect()")
        self.connection.run('SAVEPOINT resource_late')
        with self.assertRaises(DatabaseError) as caught:self.invoke()
        self.assertEqual(caught.exception.args[0]['C'],'55000')
        self.assertEqual(caught.exception.args[0]['M'],'selected archive cut excludes same-backend writes')
        self.connection.run('ROLLBACK TO SAVEPOINT resource_late')
        self.assertEqual(self.connection.run('SELECT is_called FROM pg_temp.resource_late_effect'),[[True]])
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.type_def'),[[0]])
        self.assertEqual(self.connection.run('SELECT artifact_bytes FROM truss.installation_archive WHERE artifact_identity=:identity',identity=identity),[[(ROOT/identity).read_bytes()]])

    def test_same_writer_equal_byte_resource_replacement_refuses_original_row_cut(self):
        from pg8000.exceptions import DatabaseError
        self.archive();self.admit();identity=json.loads(self.policy)['resources'][0]['path']
        original=self.connection.run('SELECT archive_row_id,artifact_bytes FROM truss.installation_archive WHERE artifact_identity=:identity',identity=identity)
        self.connection.run("CREATE TEMP SEQUENCE resource_replace_effect; CREATE FUNCTION truss.resource_fixture_replace_effect() RETURNS trigger LANGUAGE plpgsql AS $$ DECLARE old_id bigint; BEGIN PERFORM nextval('pg_temp.resource_replace_effect'); SELECT archive_row_id INTO STRICT old_id FROM truss.installation_archive WHERE artifact_identity='packages/python/src/truss/_report_schemas/exact-value-v0.1.schema.json'; INSERT INTO truss.installation_archive(installation_id,artifact_role,artifact_identity,artifact_bytes,artifact_identity_sha256) SELECT installation_id,artifact_role,artifact_identity,artifact_bytes,artifact_identity_sha256 FROM truss.installation_archive WHERE archive_row_id=old_id; DELETE FROM truss.installation_archive WHERE archive_row_id=old_id; RETURN NEW; END $$; CREATE TRIGGER resource_fixture_replace_effect BEFORE INSERT ON truss.schema_rev FOR EACH ROW EXECUTE FUNCTION truss.resource_fixture_replace_effect()")
        self.connection.run('SAVEPOINT resource_replace')
        with self.assertRaises(DatabaseError) as caught:self.invoke()
        self.assertEqual(caught.exception.args[0]['C'],'55000')
        self.assertEqual(caught.exception.args[0]['M'],'selected archive cut excludes same-backend writes')
        self.connection.run('ROLLBACK TO SAVEPOINT resource_replace')
        self.assertEqual(self.connection.run('SELECT is_called FROM pg_temp.resource_replace_effect'),[[True]])
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.type_def'),[[0]])
        self.assertEqual(self.connection.run('SELECT archive_row_id,artifact_bytes FROM truss.installation_archive WHERE artifact_identity=:identity',identity=identity),original)

    def test_missing_or_changed_fence_refuses_before_first_effect(self):
        from pg8000.exceptions import DatabaseError
        self.archive();self.admit()
        self.connection.run('SET CONSTRAINTS truss.installation_archive_marker_fk IMMEDIATE')
        self.connection.run("CREATE TEMP SEQUENCE fence_first_effect; CREATE FUNCTION truss.fence_fixture_first_effect() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN PERFORM nextval('pg_temp.fence_first_effect'); RETURN NEW; END $$; CREATE TRIGGER fence_fixture_first_effect BEFORE INSERT ON truss.schema_rev FOR EACH ROW EXECUTE FUNCTION truss.fence_fixture_first_effect()")
        cases=[
            "DROP TRIGGER runtime_selected_archive_write_fence ON truss.installation_archive",
            "ALTER TABLE truss.installation_archive DISABLE TRIGGER runtime_selected_archive_write_fence",
            "ALTER TABLE truss.installation_archive ENABLE TRIGGER runtime_selected_archive_write_fence",
            "ALTER TABLE truss.installation_archive ENABLE REPLICA TRIGGER runtime_selected_archive_write_fence",
            "ALTER FUNCTION truss.runtime_fence_selected_archive_writes() SECURITY DEFINER",
            "ALTER FUNCTION truss.runtime_fence_selected_archive_writes() SET search_path=pg_temp,pg_catalog",
            "ALTER FUNCTION truss.runtime_fence_selected_archive_writes() IMMUTABLE",
            "ALTER FUNCTION truss.runtime_fence_selected_archive_writes() PARALLEL SAFE",
            "ALTER FUNCTION truss.runtime_fence_selected_archive_writes() STRICT",
            "ALTER FUNCTION truss.runtime_fence_selected_archive_writes() LEAKPROOF",
            ALTERED_FENCE_DEFINITION,
            SET_FENCE_DEFINITION,
            DEFAULT_ACL_FENCE_DEFINITION,
            "GRANT EXECUTE ON FUNCTION truss.runtime_fence_selected_archive_writes() TO PUBLIC",
            "GRANT EXECUTE ON FUNCTION truss.runtime_fence_selected_archive_writes() TO pg_read_all_stats",
            "ALTER FUNCTION truss.runtime_fence_selected_archive_writes() OWNER TO pg_read_all_stats",
            "CREATE FUNCTION truss.runtime_fence_selected_archive_writes(text) RETURNS text LANGUAGE sql AS $$ SELECT $1 $$",
            "CREATE TRIGGER extra_archive_fence BEFORE INSERT ON truss.installation_archive FOR EACH STATEMENT EXECUTE FUNCTION truss.runtime_fence_selected_archive_writes()",
            "ALTER TRIGGER runtime_selected_archive_write_fence ON truss.installation_archive RENAME TO wrong_fence",
            "DROP TRIGGER runtime_selected_archive_write_fence ON truss.installation_archive; CREATE TRIGGER runtime_selected_archive_write_fence BEFORE INSERT ON truss.installation_archive FOR EACH STATEMENT EXECUTE FUNCTION truss.runtime_fence_selected_archive_writes(); ALTER TABLE truss.installation_archive ENABLE ALWAYS TRIGGER runtime_selected_archive_write_fence",
            "DROP TRIGGER runtime_selected_archive_write_fence ON truss.installation_archive; CREATE TRIGGER runtime_selected_archive_write_fence BEFORE INSERT OR UPDATE OR DELETE OR TRUNCATE ON truss.installation_archive FOR EACH STATEMENT WHEN(false) EXECUTE FUNCTION truss.runtime_fence_selected_archive_writes(); ALTER TABLE truss.installation_archive ENABLE ALWAYS TRIGGER runtime_selected_archive_write_fence"]
        for sql in cases:
            with self.subTest(sql=sql):
                self.connection.run("SELECT setval('pg_temp.fence_first_effect',1,false)")
                self.connection.run('SAVEPOINT fence_drift')
                try:
                    self.connection.run(sql)
                    if sql==DEFAULT_ACL_FENCE_DEFINITION:
                        self.assertEqual(self.connection.run("SELECT proacl IS NULL FROM pg_proc WHERE oid=\'truss.runtime_fence_selected_archive_writes()\'::regprocedure"),[[True]])
                    with self.assertRaises(DatabaseError) as caught:self.invoke()
                    self.assertEqual(caught.exception.args[0]['C'],'55000')
                    self.assertEqual(caught.exception.args[0]['M'],'original installed archive write fence required')
                finally:
                    self.connection.run('ROLLBACK TO fence_drift');self.connection.run('RELEASE fence_drift')
                self.assertEqual(self.connection.run('SELECT is_called FROM pg_temp.fence_first_effect'),[[False]])
                self.assertEqual(self.connection.run('SELECT count(*) FROM truss.type_def'),[[0]])
                self.connection.run('SELECT truss.runtime_require_selected_archive_write_fence()')

    def test_same_writer_change_restore_is_fenced_inside_original_stage(self):
        from pg8000.exceptions import DatabaseError
        self.archive();self.admit()
        self.connection.run("CREATE TEMP SEQUENCE resource_aba_effect; CREATE FUNCTION truss.resource_fixture_aba_effect() RETURNS trigger LANGUAGE plpgsql AS $$ DECLARE original bytea; BEGIN PERFORM nextval('pg_temp.resource_aba_effect'); SELECT artifact_bytes INTO STRICT original FROM truss.installation_archive WHERE artifact_identity='packages/python/src/truss/_report_schemas/exact-value-v0.1.schema.json'; UPDATE truss.installation_archive SET artifact_bytes=decode('01','hex') WHERE artifact_identity='packages/python/src/truss/_report_schemas/exact-value-v0.1.schema.json'; UPDATE truss.installation_archive SET artifact_bytes=original WHERE artifact_identity='packages/python/src/truss/_report_schemas/exact-value-v0.1.schema.json'; RETURN NEW; END $$; CREATE TRIGGER resource_fixture_aba_effect BEFORE INSERT ON truss.schema_rev FOR EACH ROW EXECUTE FUNCTION truss.resource_fixture_aba_effect()")
        self.connection.run('SAVEPOINT aba')
        with self.assertRaises(DatabaseError) as caught:self.invoke()
        self.assertEqual(caught.exception.args[0]['M'],'selected archive cut excludes same-backend writes')
        self.connection.run('ROLLBACK TO aba');self.connection.run('RELEASE aba')
        self.assertEqual(self.connection.run('SELECT is_called FROM pg_temp.resource_aba_effect'),[[True]])
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.type_def'),[[0]])

    def test_late_fence_source_change_refuses_and_rolls_back(self):
        from pg8000.exceptions import DatabaseError
        self.archive();self.admit()
        self.connection.run("CREATE TEMP SEQUENCE fence_late_effect; CREATE FUNCTION truss.fence_fixture_late_effect() RETURNS trigger LANGUAGE plpgsql AS $outer$ BEGIN PERFORM nextval('pg_temp.fence_late_effect'); EXECUTE '"+ALTERED_FENCE_DEFINITION.replace("'","''")+"'; RETURN NEW; END $outer$; CREATE TRIGGER fence_fixture_late_effect BEFORE INSERT ON truss.schema_rev FOR EACH ROW EXECUTE FUNCTION truss.fence_fixture_late_effect()")
        self.connection.run('SAVEPOINT late_fence')
        with self.assertRaises(DatabaseError) as caught:self.invoke()
        self.assertEqual(caught.exception.args[0]['C'],'55000')
        self.assertEqual(caught.exception.args[0]['M'],'original installed archive write fence required')
        self.connection.run('ROLLBACK TO late_fence');self.connection.run('RELEASE late_fence')
        self.assertEqual(self.connection.run('SELECT is_called FROM pg_temp.fence_late_effect'),[[True]])
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.type_def'),[[0]])
        self.connection.run('SELECT truss.runtime_require_selected_archive_write_fence()')
    def test_after_core_metadata_change_refuses_at_final_release_cut(self):
        from pg8000.exceptions import DatabaseError
        self.archive();self.admit()
        self.connection.run('CREATE TEMP TABLE earlier_host_work(value int); INSERT INTO earlier_host_work VALUES(7)')
        self.connection.run("""ALTER FUNCTION truss.runtime_stage_catalog_admitted(
            bigint,bytea,bytea,bytea,bytea,bytea,bytea,bytea,bytea,bytea,bytea)
            RENAME TO fixture_stage_original;
            CREATE FUNCTION truss.runtime_stage_catalog_admitted(
            bigint,bytea,bytea,bytea,bytea,bytea,bytea,bytea,bytea,bytea,bytea)
            RETURNS TABLE(writer_xid text,ordinal text,context_hex text,provisional_result_hex text)
            LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
            DECLARE original record;
            BEGIN SELECT * INTO STRICT original FROM truss.fixture_stage_original($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11);
            UPDATE truss.installation_marker SET layout_version='after-core-change';
            RETURN QUERY SELECT original.writer_xid,original.ordinal,original.context_hex,original.provisional_result_hex;
            END $$""")
        self.connection.run('SAVEPOINT release_cut')
        with self.assertRaises(DatabaseError) as caught:self.invoke()
        self.assertEqual(caught.exception.args[0]['C'],'55000')
        self.assertEqual(caught.exception.args[0]['M'],'original configured release final cut required')
        self.connection.run('ROLLBACK TO SAVEPOINT release_cut')
        self.assertEqual(self.connection.run('SELECT value FROM earlier_host_work'),[[7]])
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.type_def'),[[0]])
