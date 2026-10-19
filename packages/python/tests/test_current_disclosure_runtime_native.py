# SPDX-License-Identifier: MIT OR Apache-2.0
"""Opt-in actual PG18.6 disclosure flow; original fixture binding is not admission.

This campaign requires a serialized native test window. It exercises genuine
host/caller/Subject/source/closing guards. The inherited local server uses its
existing authentication setup; do not credit SCRAM or all132 acceptance from it.
"""
import os,unittest,json,shutil
from pathlib import Path
from hashlib import sha256
from dataclasses import replace
from unittest.mock import patch
from typing import get_type_hints
from truss import (Ok,Error,CurrentQueryExecutor,CurrentDisclosureExecutor,CurrentDisclosureRows,
    CatalogDocument,ModuleAccessGrant,adopt_psycopg_host,activate_current_query_protection_in_transaction,
    prepare_current_disclosure_originals,register_current_disclosure_sources_in_transaction)
from truss.contracts import TextValue,BooleanValue,MapValue
from truss.groups import CreateObject,AuthoredValue,RootlessOwnership,RequestNone,GroupSuccess
from truss.query import QueryRefused
from truss._current_query_subjects import register_current_query_subjects_in_transaction,observe_current_query_subject_in_transaction
_NATIVE=os.environ.get('TRUSS_DISCLOSURE_NATIVE_QUALIFICATION')=='1'
if _NATIVE:
 import psycopg,weft
 import test_current_query_runtime_native as legacy
 _NativeBase=legacy.CurrentQueryRuntimeNativeTests
else:_NativeBase=unittest.TestCase

@unittest.skipUnless(_NATIVE,'requires serialized explicit native qualification window')
class CurrentDisclosureRuntimeNativeTests(_NativeBase):
    for name in tuple(n for n in dir(_NativeBase) if n.startswith('test_')):
        locals()[name]=None

    def source_inputs(self):
        raw=(Path(__file__).parent/'fixtures/current-disclosure/native-weft-request.json').read_bytes()
        prepared=weft.prepare_application_lineage(raw.decode()).prepare_current_presence()
        self.assertEqual(json.loads(prepared.native_request_json())['version'],'weft.current-presence.native-input/0.1-candidate')
        request=json.loads(raw);opaque=request['opaqueSources'];source={r['role']:json.loads(r['utf8']) for r in opaque}
        closure={'pins':[{'documentId':m['pin']['documentId'],'revision':m['pin']['revision']} for m in request['modules']],
                 'documents':[{'revision':m['pin']['revision'],'document':json.loads(m['documentJson'])} for m in request['modules']]}
        initialize=json.dumps({'kind':'initialize','requestId':'initialize','sources':{
            'policy':source['policy'],'catalog':source['catalog'],'ontology':source['ontology'],'closure':closure,
            'associationBindings':[],'extensionSelection':None}},separators=(',',':')).encode()
        self.originals=prepare_current_disclosure_originals(json.dumps(opaque,separators=(',',':')).encode())
        return initialize,self.originals

    def setup_disclosure_subject(self):
        bun = os.environ.get('TRUSS_BUN_EXECUTABLE',shutil.which('bun') or 'bun')
        self.install()
        initialize,query_originals = self.source_inputs()
        closure = json.loads(initialize)['sources']['closure']
        modules, documents = [], []
        for entry in closure['documents']:
            doc = entry['document'];raw = json.dumps(doc,separators=(',',':'),ensure_ascii=False)
            revision = next(p['revision'] for p in closure['pins'] if p['documentId']==doc['id'])
            modules.append({'pin':{'documentId':doc['id'],'revision':revision,'umfVersion':doc['umf'],'sha256':sha256(raw.encode()).hexdigest()},'documentJson':raw})
            documents.append(CatalogDocument(doc['id'],revision,raw.encode()))
        c,h,a,t = self.consumer()
        prepared = a.prepare_catalog(tuple(documents),source_version='0.10.0',bun_executable=bun)
        self.assertIsInstance(a.accept_in_transaction(t,prepared,request_key='subject-model'),Ok,str(h._custody.last_attempt.error))
        h.detach();c.commit()
        self.admin.execute('CREATE ROLE subject_reader;CREATE ROLE subject_writer;CREATE ROLE subject_outsider LOGIN')
        for role in ('subject_reader','subject_writer','subject_outsider'):
            self.addCleanup(self.admin.execute,'DROP OWNED BY '+role+';DROP ROLE '+role)
        self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin,operation_timeout_ms=30000);self.tx=self.host.adopt_transaction().value
        from truss import create_reference_assembly,CatalogRuntimeConfiguration
        a = create_reference_assembly(CatalogRuntimeConfiguration(),self.host).value
        self.assertIsInstance(a.configure_module_access_in_transaction(self.tx,(ModuleAccessGrant('domain','m','subject_reader','subject_writer'),)),Ok)
        self.host.detach();self.admin.commit();self.admin.execute('GRANT subject_writer TO consumer WITH SET FALSE')
        c,h,a,t = self.consumer()
        view = a.catalog_view_in_transaction(t,a.catalog_view_request()).value.view
        subject = next(d.reference for d in view.definitions if d.reference.kind=='type' and d.reference.authored_identity=='Staff')
        context = a.group_context_in_transaction(t).value
        result = a.apply_in_transaction(t,context.input((CreateObject(type_definition_pin=subject.definition_pin,
            values=(AuthoredValue(name='staffId',value=TextValue(kind='string',text='alice')),),
            ownership=RootlessOwnership(),alias='subject'),),MapValue(entries=())),RequestNone(),documents=tuple(documents),bun_executable=bun)
        self.assertIsInstance(result,Ok,str(h._custody.last_attempt.error));self.assertIsInstance(result.value,GroupSuccess)
        h.detach();c.commit()
        self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin,operation_timeout_ms=30000);self.tx=self.host.adopt_transaction().value
        stored = register_current_disclosure_sources_in_transaction(self.host,self.tx,initialize_bytes=initialize,
            accepted_request_bytes=json.dumps({'modules':modules},separators=(',',':')).encode(),disclosure_originals=query_originals)
        self.assertIsInstance(stored,Ok,str(self.host._custody.last_attempt.error))
        missing = register_current_query_subjects_in_transaction(self.host,self.tx,bindings=(('consumer','missing'),))
        self.assertIsInstance(missing,Error)
        enrolled = register_current_query_subjects_in_transaction(self.host,self.tx,bindings=(('consumer','alice'),))
        self.assertIsInstance(enrolled,Ok,str(self.host._custody.last_attempt.error))
        self.host.detach();self.admin.commit()
        c,h,a,t = self.consumer()
        observed = observe_current_query_subject_in_transaction(h,t,enrolled.value,bun_executable=bun)
        self.assertIsInstance(observed,Ok,str(h._custody.last_attempt.error))
        self.current_subject_observation=observed.value
        self.current_subject_registration=enrolled.value
        self.current_source_documents=tuple(documents)
        self.assertEqual(observed.value.key,'alice')
        for changed in (replace(enrolled.value,identity=('m','Project','pk')),
                        replace(enrolled.value,original_document=enrolled.value.original_document+b' ')):
            with self.subTest(codec=changed.identity),patch('truss._current_query_subjects.encode_string_key_tuples') as encoder:
                refused = observe_current_query_subject_in_transaction(h,t,changed,bun_executable=bun)
                self.assertIsInstance(refused,Error)
                encoder.assert_not_called()
        self.assertEqual(observed.value.source_receipt,stored.value.source_receipt)
        self.assertEqual(observed.value.role_oid,c.execute('SELECT usesysid::text FROM pg_stat_activity WHERE pid=pg_backend_pid()').fetchone()[0])
        receipt = json.loads(observed.value.original_key_receipt)
        self.assertEqual(receipt['values'],[{'string':'alice'}]);self.assertEqual(bytes.fromhex(receipt['bytesHex']),observed.value.tuple_bytes)
        self.assertEqual(c.execute("SELECT has_table_privilege('truss.catalog_subject_map','SELECT'),has_table_privilege('truss.object','SELECT')").fetchone(),(False,False))
        parameters=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);parameters['user']='subject_outsider'
        with psycopg.connect(**parameters,autocommit=True) as outsider:
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                outsider.execute('SELECT * FROM truss.current_query_subject_current()')

    def create_query_graph(self, *, active=True, resources=True, exercise_activation_refusals=False):
        self.setup_disclosure_subject()
        bun=os.environ.get('TRUSS_BUN_EXECUTABLE',shutil.which('bun') or 'bun')
        for connection,host in self.consumer_connections:
            host.detach();connection.rollback();connection.close()
        c,h,a,t=self.consumer()
        self.assertIs(get_type_hints(a.query_current_in_transaction)['executor'],CurrentQueryExecutor)
        view=a.catalog_view_in_transaction(t,a.catalog_view_request()).value.view
        types={d.reference.authored_identity:d.reference for d in view.definitions if d.reference.kind=='type'}
        inputs=[('Project',{'projectId':'p1'}),
                ('Resource',{'resourceId':'r1','salary':9007199254740993,'token':'opaque-one'}),
                ('Resource',{'resourceId':'r2','salary':9007199254740993,'token':'opaque-two'}),
                ('Ownership',{'ownerId':'o1','ownerResource':'r1','ownerProject':'p1'}),
                ('Assignment',{'assignmentId':'a1','assignmentStaff':'alice','assignmentProject':'p1','active':active})]
        if not resources:inputs=[item for item in inputs if item[0] not in ('Resource','Ownership')]
        operations=[]
        for index,(record,fields) in enumerate(inputs):
            values=tuple(AuthoredValue(name=name,value=BooleanValue(value=value) if type(value) is bool else TextValue(kind='integer' if type(value) is int else 'string',text=str(value))) for name,value in fields.items())
            operations.append(CreateObject(type_definition_pin=types[record].definition_pin,values=values,ownership=RootlessOwnership(),alias='query'+str(index)))
        context=a.group_context_in_transaction(t).value
        result=a.apply_in_transaction(t,context.input(tuple(operations),MapValue(entries=())),RequestNone(),documents=self.current_source_documents,bun_executable=bun)
        self.assertIsInstance(result,Ok,str(h._custody.last_attempt.error));self.assertIsInstance(result.value,GroupSuccess)
        h.detach();c.commit()
        # Retain a real pre-activation binding: cached facade inputs must not
        # preserve ordinary data access after the committed lockdown.
        from truss.catalog_runtime import _release
        manifest,digest,_=_release()
        c,h,a,t=self.consumer()
        self.legacy_binding=json.loads(bytes(c.execute('SELECT truss.query_binding(%s::jsonb,%s,%s,%s,%s,%s)',
            (json.dumps(['domain']),10000,10000,16777216,manifest['releaseId'],digest)).fetchone()[0]))
        for connection,host in self.consumer_connections:
            if not connection.closed:
                host.detach();connection.rollback();connection.close()
        self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin,operation_timeout_ms=30000)
        self.tx=self.host.adopt_transaction().value
        if exercise_activation_refusals:
            owner=self.current_subject_registration.owner_oid
            owner_name=self.admin.execute('SELECT rolname FROM pg_roles WHERE oid=%s',(owner,)).fetchone()[0]
            from psycopg import sql as pgsql
            # A pre-existing external definer is a real alternate entry point even
            # if no ordinary role has direct SELECT on the original object table.
            self.admin.execute("CREATE FUNCTION public.preexisting_raw_resource() RETURNS jsonb LANGUAGE sql SECURITY DEFINER AS 'SELECT jsonb_agg(props) FROM truss.object'")
            self.admin.execute(pgsql.SQL('ALTER FUNCTION public.preexisting_raw_resource() OWNER TO {}').format(pgsql.Identifier(owner_name)))
            refused=activate_current_query_protection_in_transaction(self.host,self.tx,subject_registration=self.current_subject_registration)
            self.assertIsInstance(refused,Error)
            self.assertIn('externally delegated',str(self.host._custody.last_attempt.error))
            self.admin.execute('REVOKE ALL ON FUNCTION public.preexisting_raw_resource() FROM PUBLIC')
            refused=activate_current_query_protection_in_transaction(self.host,self.tx,subject_registration=self.current_subject_registration)
            self.assertIsInstance(refused,Error)
            self.assertIn('externally delegated',str(self.host._custody.last_attempt.error))
            self.admin.execute('DROP FUNCTION public.preexisting_raw_resource()')
            self.admin.execute('CREATE VIEW public.preexisting_resource_view AS SELECT props FROM truss.object')
            self.admin.execute('CREATE VIEW public.preexisting_resource_outer AS SELECT props FROM public.preexisting_resource_view')
            self.admin.execute('GRANT SELECT(props) ON public.preexisting_resource_outer TO subject_outsider')
            refused=activate_current_query_protection_in_transaction(self.host,self.tx,subject_registration=self.current_subject_registration)
            self.assertIsInstance(refused,Error)
            self.assertIn('externally delegated',str(self.host._custody.last_attempt.error))
            self.admin.execute('DROP VIEW public.preexisting_resource_outer')
            self.admin.execute('DROP VIEW public.preexisting_resource_view')
            self.admin.execute('ALTER ROLE subject_outsider BYPASSRLS')
            refused=activate_current_query_protection_in_transaction(self.host,self.tx,subject_registration=self.current_subject_registration)
            self.assertIsInstance(refused,Error)
            self.assertIn('externally delegated',str(self.host._custody.last_attempt.error))
            self.admin.execute('ALTER ROLE subject_outsider NOBYPASSRLS')
            self.admin.execute('CREATE TABLE public.preexisting_feed_carrier(xid xid8)')
            self.admin.execute('ALTER TABLE public.preexisting_feed_carrier OWNER TO subject_outsider')
            self.admin.execute("CREATE TRIGGER external_feed_capture AFTER INSERT ON public.preexisting_feed_carrier FOR EACH ROW EXECUTE FUNCTION truss.runtime_capture_feed_configuration('xid')")
            self.admin.execute('ALTER TABLE public.preexisting_feed_carrier DISABLE TRIGGER external_feed_capture')
            refused=activate_current_query_protection_in_transaction(self.host,self.tx,subject_registration=self.current_subject_registration)
            self.assertIsInstance(refused,Error)
            self.assertIn('External routine attachments',str(self.host._custody.last_attempt.error))
            self.admin.execute('DROP TABLE public.preexisting_feed_carrier')
        activated=activate_current_query_protection_in_transaction(self.host,self.tx,subject_registration=self.current_subject_registration)
        self.assertIsInstance(activated,Ok,str(self.host._custody.last_attempt.error))
        self.host.detach();self.admin.commit()
        return bun

    def assert_native_disclosure(self,*,active=True,resources=True):
        bun=self.create_query_graph(active=active,resources=resources)
        self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin,operation_timeout_ms=30000)
        self.tx=self.host.adopt_transaction().value
        executor=CurrentDisclosureExecutor(self.host,self.tx,self.current_subject_registration,bun_executable=bun)
        c,h,a,t=self.consumer()
        result=a.query_current_disclosure_in_transaction(t,executor=executor,sql='SELECT r.salary FROM Resource r',document_ids=('domain',))
        self.assertIsInstance(result,Ok,str(self.host._custody.last_attempt.error))
        self.assertIsInstance(result.value,CurrentDisclosureRows,str(self.host._custody.last_attempt.error))
        batch=json.loads(result.value.batch_json)
        self.assertEqual(result.value.columns,('salary',));self.assertEqual(result.value.field_indexes,(0,))
        self.assertEqual(batch['version'],'umf.security.disclosure/0.2.0')
        self.assertEqual(len(batch['rows']),1 if active and resources else 0)
        if batch['rows']:
            self.assertNotIn('9007199254740993',result.value.batch_json.decode())
            self.assertIn('[private]',result.value.batch_json.decode())
        self.assertEqual(c.execute("SELECT has_table_privilege('truss.object','SELECT')").fetchone(),(False,))
        self.assertEqual(self.admin.execute("SELECT count(*) FROM pg_class WHERE relnamespace=pg_my_temp_schema() AND relname LIKE 'truss_presence_%'").fetchone(),(0,))
        return result

    def test_native_masked_disclosure(self):self.assert_native_disclosure()
    def test_native_all_denied_disclosure(self):self.assert_native_disclosure(active=False)
    def test_native_empty_disclosure(self):self.assert_native_disclosure(resources=False)

    def test_native_changed_source_before_closing_guard_refuses_public_data(self):
        import truss._current_disclosure_evaluation as evaluator
        original=evaluator.evaluate_and_stage_current_disclosure;observed=[]
        def drift(cursor,*args,**kwargs):
            held=original(cursor,*args,**kwargs);held.require_original_parent();observed.append('inspected')
            cursor.execute("UPDATE truss.installation_archive SET artifact_bytes=artifact_bytes||decode('20','hex') WHERE artifact_identity='current-query:initialize'",prepare=False)
            return held
        bun=self.create_query_graph()
        self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin,operation_timeout_ms=30000);self.tx=self.host.adopt_transaction().value
        executor=CurrentDisclosureExecutor(self.host,self.tx,self.current_subject_registration,bun_executable=bun)
        c,h,a,t=self.consumer()
        with patch.object(evaluator,'evaluate_and_stage_current_disclosure',side_effect=drift):
            result=a.query_current_disclosure_in_transaction(t,executor=executor,sql='SELECT r.salary FROM Resource r',document_ids=('domain',))
        self.assertEqual(observed,['inspected'])
        self.assertTrue(isinstance(result,Error) or isinstance(result,Ok) and isinstance(result.value,QueryRefused))
        self.assertEqual(self.admin.execute("SELECT count(*) FROM pg_class WHERE relnamespace=pg_my_temp_schema() AND relname LIKE 'truss_presence_%'").fetchone(),(0,))

    def test_native_post_transport_whole_batch_refusal_never_releases(self):
        import truss._current_disclosure_evaluation as evaluator
        original=evaluator.stage_current_disclosure;observed=[]
        def replace_header(*args,**kwargs):
            staged=original(*args,**kwargs);observed.append('native-checked')
            batch=json.loads(staged.reconstructed_batch);batch['policy']['revision']='tampered-after-native-check'
            return replace(staged,reconstructed_batch=json.dumps(batch,separators=(',',':')).encode())
        bun=self.create_query_graph()
        self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin,operation_timeout_ms=30000);self.tx=self.host.adopt_transaction().value
        executor=CurrentDisclosureExecutor(self.host,self.tx,self.current_subject_registration,bun_executable=bun)
        c,h,a,t=self.consumer()
        with patch.object(evaluator,'stage_current_disclosure',side_effect=replace_header):
            result=a.query_current_disclosure_in_transaction(t,executor=executor,sql='SELECT r.salary FROM Resource r',document_ids=('domain',))
        self.assertEqual(observed,['native-checked'])
        self.assertIsInstance(result,Ok,str(self.host._custody.last_attempt.error))
        self.assertIsInstance(result.value,QueryRefused)
        self.assertEqual(result.value.code,'unsupported_query')
        self.assertEqual(self.admin.execute("SELECT count(*) FROM pg_class WHERE relnamespace=pg_my_temp_schema() AND relname LIKE 'truss_presence_%'").fetchone(),(0,))
