"""Opted-in owned PG source observation, not binding/authority/release admission."""
import json,hashlib,os,unittest
from pathlib import Path
import psycopg
from truss import Ok,Error,adopt_psycopg_host
from truss._native_source_observation import capture_native_source_observation_with_cursor,HOMES,CATALOGS
from truss._owner_evidence_json import decode_owner_evidence_json
import test_group_create_native as base

@unittest.skipUnless(os.environ.get('TRUSS_NATIVE_SOURCE_OBSERVATION_QUALIFICATION')=='1','requires explicit serialized owned native source observation')
class NativeSourceObservationNativeTests(base.PublicCreateGroupTests):
    for name in tuple(n for n in dir(base.PublicCreateGroupTests) if n.startswith('test_')):locals()[name]=None
    def ready_observation(self):
        self.__class__.postmaster_pid=int((self.info.data_directory/'postmaster.pid').read_text().splitlines()[0])
        c,h,a,t=self.ready(document_ids=('adoc',));h.detach();c.rollback()
        request=json.dumps({'modules':[{'pin':{'documentId':d.document_id,'revision':d.document_revision,'umfVersion':json.loads(d.content)['umf'],'sha256':hashlib.sha256(d.content).hexdigest()},'documentJson':d.content.decode()} for d in self.documents]},separators=(',',':')).encode()
        self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin,operation_timeout_ms=60000);self.tx=self.host.adopt_transaction().value
        return request
    def observe(self,request):return self.host._run_operation(self.tx,lambda cursor,observed:capture_native_source_observation_with_cursor(cursor,request))
    def retain(self,name,value):
        folder=os.environ.get('TRUSS_NATIVE_SOURCE_OBSERVATION_EVIDENCE')
        if folder:
            p=Path(folder);p.mkdir(parents=True,exist_ok=True);(p/name).write_bytes(value)
    def test_actual_original_source_and_complete_native_metadata(self):
        request=self.ready_observation();result=self.observe(request);self.assertIsInstance(result,Ok,str(self.host._custody.last_attempt.error));captured=result.value
        inventory=decode_owner_evidence_json(captured.native_inventory);assessment=decode_owner_evidence_json(captured.accepted_assessment);report=decode_owner_evidence_json(captured.report)
        self.assertEqual(inventory['version'],'truss.native-source.inventory/0.2-candidate');self.assertEqual(assessment['version'],'truss.accepted-catalog-assessment/0.2-candidate')
        self.assertFalse(report['authority']);self.assertFalse(report['complete']);self.assertFalse(report['securityReady']);self.assertEqual(report['nativeAdmission'],'required')
        self.assertIs(captured.accepted_request,request)
        self.assertEqual(inventory['coverage'],{'relations':list(HOMES),'completeSelectedHomes':True})
        self.assertEqual([r['name'] for r in inventory['relations']],list(HOMES))
        observed=[]
        with psycopg.connect(self.info.connection_uri,autocommit=True) as writer:
            for relation in inventory['relations']:
                name=relation['name'];actual=self.admin.execute("SELECT c.oid::text,c.relnamespace::text,c.relowner::text FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss' AND c.relname=%s",(name,)).fetchone()
                self.assertEqual(actual,(relation['oid'],relation['namespaceOid'],relation['ownerOid']))
                actual_columns=self.admin.execute('SELECT attnum,attname,atttypid::text,atttypmod,attcollation::text FROM pg_attribute WHERE attrelid=%s::oid AND attnum>0 ORDER BY attnum',(relation['oid'],)).fetchall()
                self.assertEqual(actual_columns,[(x['attnum'],x['name'],x['typeOid'],x['typmod'],x['collationOid']) for x in relation['columns']])
                # Independent expected selected native71 expressions and nullability;
                # generated digest expressions are not DEFAULT declarations.
                expected_default={'edge':{'id':"nextval('truss.id_seq'::regclass)",'props':"'{}'::jsonb",'ver':'1','created_at':'clock_timestamp()','updated_at':'clock_timestamp()'},'object':{'id':"nextval('truss.id_seq'::regclass)",'props':"'{}'::jsonb",'ver':'1','created_at':'clock_timestamp()','updated_at':'clock_timestamp()'},'object_key_bucket':{'storage_row_id':"nextval('truss.key_storage_row_seq'::regclass)"}}
                expected_generated={'object_key_bucket':{'namespace_sha256':'sha256(namespace_bytes)','key_sha256':'sha256(key_bytes)'}}
                nullable={'edge':{'order_key','retained'},'object':{'retained','root_id','root_type'},'object_key_bucket':{'namespace_sha256','key_sha256'}}
                for column in relation['columns']:
                    field=column['name'];self.assertEqual(column['notNull'],field not in nullable[name]);self.assertEqual(column['identity'],'')
                    if field in expected_generated.get(name,{}):
                        self.assertEqual(column['generated'],'s');self.assertEqual(column['expression'],{'kind':'generated','source':expected_generated[name][field]})
                    elif field in expected_default[name]:
                        self.assertEqual(column['generated'],'');self.assertEqual(column['expression'],{'kind':'default','source':expected_default[name][field]})
                    else:self.assertEqual(column['generated'],'');self.assertEqual(column['expression'],{'kind':'none','source':None})

                actual_constraints=self.admin.execute('SELECT oid::text,pg_get_constraintdef(oid,false) FROM pg_constraint WHERE conrelid=%s::oid ORDER BY oid',(relation['oid'],)).fetchall()
                self.assertEqual(actual_constraints,[(x['oid'],x['definition']) for x in relation['constraints']])
                for mode in ('ROW EXCLUSIVE','ACCESS EXCLUSIVE'):
                    with self.assertRaises(psycopg.errors.LockNotAvailable):
                        with writer.transaction():writer.execute('LOCK TABLE ONLY truss.'+name+' IN '+mode+' MODE NOWAIT')
                    observed.append(name+':'+mode)
        for _,table,order in CATALOGS:
            for raw, in self.admin.execute('SELECT to_jsonb(t)::text FROM ONLY truss.'+table+' t ORDER BY '+order).fetchall():self.assertIn(raw.encode(),captured.accepted_assessment)
        for name,raw in [('accepted-request.json',request),('accepted-assessment.json',captured.accepted_assessment),('legacy-assessment.json',captured.legacy_assessment),('runtime-release.json',captured.runtime_release),('native-inventory.json',captured.native_inventory),('report.json',captured.report)]:self.retain(name,raw)
        self.retain('native-result.json',json.dumps({'status':'passed','serverVersion':self.admin.info.server_version,'serverBuild':self.admin.execute('SELECT version()').fetchone()[0],'locks':observed,'scope':'Original host/cursor, source checks and selected native metadata. No native binding/current authority/release/case admission.'},indent=2).encode())
    def test_native_rls_home_refuses_without_partial_observation(self):
        request=self.ready_observation();valid=self.observe(request);self.assertIsInstance(valid,Ok,str(self.host._custody.last_attempt.error));self.admin.execute("CREATE TEMP TABLE prior(value text);INSERT INTO prior VALUES('kept')")
        self.admin.execute('SAVEPOINT before_rls');self.admin.execute('ALTER TABLE truss.edge ENABLE ROW LEVEL SECURITY')
        refused=self.observe(request);self.assertIsInstance(refused,Error);self.assertIn('unfiltered native source home',str(self.host._custody.last_attempt.error));self.assertEqual(self.admin.execute('TABLE prior').fetchall(),[('kept',)])
        self.admin.execute('ROLLBACK TO SAVEPOINT before_rls');self.admin.execute('RELEASE SAVEPOINT before_rls')
        self.assertIsInstance(self.observe(request),Ok,str(self.host._custody.last_attempt.error))
    def test_column_rename_changes_data_and_restoration_is_not_authority(self):
        request=self.ready_observation();before=self.observe(request);self.assertIsInstance(before,Ok,str(self.host._custody.last_attempt.error))
        self.admin.execute('SAVEPOINT before_column');self.admin.execute('ALTER TABLE truss.object RENAME COLUMN props TO props_drift')
        changed=self.observe(request);self.assertIsInstance(changed,Ok,str(self.host._custody.last_attempt.error))
        self.assertNotEqual(changed.value.native_inventory,before.value.native_inventory)
        native=decode_owner_evidence_json(changed.value.native_inventory);self.assertIn('props_drift',[c['name'] for r in native['relations'] if r['name']=='object' for c in r['columns']])
        self.admin.execute('ROLLBACK TO SAVEPOINT before_column');self.admin.execute('RELEASE SAVEPOINT before_column')
        restored=self.observe(request);self.assertIsInstance(restored,Ok,str(self.host._custody.last_attempt.error));self.assertEqual(restored.value.native_inventory,before.value.native_inventory)
        self.assertFalse(decode_owner_evidence_json(restored.value.report)['authority'])
    def test_changed_original_source_refuses_and_preserves_caller_work(self):
        request=self.ready_observation();valid=self.observe(request);self.assertIsInstance(valid,Ok,str(self.host._custody.last_attempt.error));self.admin.execute("CREATE TEMP TABLE prior(value text);INSERT INTO prior VALUES('kept')")
        changed=json.loads(request);changed['modules'][0]['documentJson']+=' ';changed['modules'][0]['pin']['sha256']=hashlib.sha256(changed['modules'][0]['documentJson'].encode()).hexdigest()
        result=self.observe(json.dumps(changed).encode());self.assertIsInstance(result,Error);self.assertIn('accepted compiler source correspondence',str(self.host._custody.last_attempt.error));self.assertEqual(self.admin.execute('TABLE prior').fetchall(),[('kept',)])
