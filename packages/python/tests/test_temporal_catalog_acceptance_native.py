# SPDX-License-Identifier: MIT OR Apache-2.0
"""TN06/07 public-issued2.1 acceptance and transport fault controls.

Only the driver-bound request parameters are faulted. The preparation remains
genuine and unchanged; native inverse validation must refuse before publication.
"""
import copy
from hashlib import sha256
import json

import psycopg
from truss import CatalogDocument, Error, Ok
import temporal_native_fixture as fixture


class TemporalCatalogAcceptanceTests(fixture.TemporalNativeFixture):
    def registration_snapshot(self, connection):
        if not getattr(self,'_registration_observer_ready',False):
            # Observe this caller's pending transaction without granting the
            # person raw private-table privileges (which admission forbids).
            # Same fixed read-only fixture pattern as group-validation tests.
            tables=('schema_head','schema_doc','type_def','prop_def','key_def','rel_def',
                    'catalog_registration_request','catalog_unchanged_request',
                    'runtime_type_schema','journal','object','request_receipt')
            pairs=["'"+table+"',(SELECT coalesce(jsonb_agg(v ORDER BY v::text),'[]'::jsonb)::text "
                   "FROM (SELECT to_jsonb(t) v FROM truss."+table+" t) s)" for table in tables]
            self.admin.execute('CREATE FUNCTION public.temporal_registration_observation() RETURNS jsonb '
                'LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $$ SELECT jsonb_build_object('
                +','.join(pairs)+') $$')
            self.addCleanup(self.admin.execute,'DROP FUNCTION IF EXISTS public.temporal_registration_observation()')
            self._registration_observer_ready=True
        return connection.execute('SELECT public.temporal_registration_observation()').fetchone()[0]

    def fresh_preparation(self, assembly):
        # Deliberately different original bytes/revision, with unchanged meaning.
        # This prevents an existing unchanged-request shortcut from hiding faults.
        self.next_document = CatalogDocument('adoc','r2',self.document.content+b'\n')
        return assembly.temporal_values().prepare_catalog((self.next_document,))

    def faulted_accept(self, host, assembly, tx, prepared, mutation):
        original_cursor = host._cursor
        observations = []
        class FaultCursor:
            def __init__(self, inner): self.inner=inner
            def __getattr__(self, name): return getattr(self.inner,name)
            def __enter__(self): self.inner.__enter__();return self
            def __exit__(self,*args): return self.inner.__exit__(*args)
            def execute(self,query,parameters=None,**kwargs):
                if isinstance(query,str) and query.startswith('SELECT * FROM truss.person_catalog_accept_with_keys('):
                    original = tuple(parameters)
                    values = list(original)
                    documents,declarations,summary = (json.loads(values[index]) for index in (1,2,3))
                    packet = summary['documentValidations'][0]['inspection']
                    local = next(f for r in declarations[0]['records'] for f in r['fields'] if 'nativeDescriptor' in f)
                    owner = json.loads(packet['resultJson'])
                    if mutation=='descriptor': del local['nativeDescriptor']
                    elif mutation=='pointer': local['nativeDescriptor']['nativeTemporal']['source']['fieldViewPointer']='/modules/0'
                    elif mutation=='foreign': local['nativeDescriptor']['nativeTemporal']['source']['documentId']='foreign'
                    elif mutation=='hash': local['nativeDescriptor']['nativeTemporal']['source']['sha256']='0'*64
                    elif mutation=='duplicate': declarations[0]['records'][0]['fields'].append(copy.deepcopy(local))
                    elif mutation=='empty': declarations=[]
                    elif mutation=='owner-field': owner['records'][0]['fields'].pop()
                    elif mutation=='owner-record': owner['records'].pop()
                    elif mutation=='summary': summary['sourceFormat']='truss-registration-summary/2.0'
                    elif mutation=='archive': documents[0]['validation']['storageFormat']='truss-catalog-source/2.0'
                    elif mutation in ('support','compact-downgrade'):
                        from truss.catalog_runtime import _configuration
                        input=json.loads(values[0]);input['supportProfile']=_configuration()['supportProfile']
                        values[0]=json.dumps(input,ensure_ascii=True,separators=(',',':')).encode()
                        if mutation=='compact-downgrade':
                            summary['sourceFormat']='truss-registration-summary/2.0'
                            for entry in summary['documentValidations']:entry.pop('inspection')
                    else: raise AssertionError(mutation)
                    if mutation.startswith('owner-'):
                        packet['resultJson']=json.dumps(owner,ensure_ascii=True,separators=(',',':'))
                        packet['resultSha256']=sha256(packet['resultJson'].encode()).hexdigest()
                        documents[0]['validation']['inspection']=copy.deepcopy(packet)
                    for index,value in zip((1,2,3),(documents,declarations,summary),strict=True):
                        values[index]=json.dumps(value,ensure_ascii=True,separators=(',',':')).encode()
                    if mutation=='compact-downgrade':values[2]=b''
                    observations.append({'originalSha256':[sha256(v).hexdigest() for v in original[:5]],
                                         'faultedSha256':[sha256(v).hexdigest() for v in values[:5]]})
                    parameters=tuple(values)
                return self.inner.execute(query,parameters,**kwargs)
        host._cursor=lambda:FaultCursor(original_cursor())
        try:
            result=assembly.temporal_values().accept_in_transaction(tx,prepared,request_key='fault-'+mutation)
        finally:
            host._cursor=original_cursor
        self.assertEqual(len(observations),1,'Fault must reach exactly one actual native acceptance call')
        return result,observations[0]

    def test_public_accept_atomically_refuses_stripped_temporal_owner_declarations(self):
        c,h,a,tx=self.ready_temporal()
        self.admin.execute(psycopg.sql.SQL('GRANT {} TO consumer WITH SET FALSE').format(psycopg.sql.Identifier(self.installation.registrar_role)))
        prepared=self.fresh_preparation(a)
        original=(prepared.input_bytes,prepared.archive_documents_bytes,prepared.declarations_bytes,prepared.report_evidence_bytes)
        before=self.registration_snapshot(c)
        receipts=[]
        for mutation in ('descriptor','pointer','foreign','hash','duplicate','empty','owner-field','owner-record','summary','archive'):
            with self.subTest(mutation=mutation):
                result,receipt=self.faulted_accept(h,a,tx,prepared,mutation)
                self.assertIsInstance(result,Error,repr(result))
                self.assertEqual(result.error.sql_state,'22023',repr(result))
                self.assertEqual(self.registration_snapshot(c),before)
                self.assertEqual((prepared.input_bytes,prepared.archive_documents_bytes,prepared.declarations_bytes,prepared.report_evidence_bytes),original)
                receipts.append({'mutation':mutation,'sqlState':result.error.sql_state,**receipt})
        print('temporal-native-acceptance-faults '+json.dumps(receipts,sort_keys=True))
        h.detach();c.rollback()

    def test_mixed_legacy_support_and_temporal_summary_refuses_before_effects(self):
        c,h,a,tx=self.ready_temporal()
        self.admin.execute(psycopg.sql.SQL('GRANT {} TO consumer WITH SET FALSE').format(psycopg.sql.Identifier(self.installation.registrar_role)))
        prepared=self.fresh_preparation(a);before=self.registration_snapshot(c)
        result,_=self.faulted_accept(h,a,tx,prepared,'support')
        self.assertIsInstance(result,Error,repr(result));self.assertEqual(result.error.sql_state,'22023')
        self.assertEqual(self.registration_snapshot(c),before)
        h.detach();c.rollback()

    def test_legacy_timestamp_family_refuses_temporal_reinterpretation_atomically(self):
        def original_instant(source):
            field=source['modules'][0]['extensions']['umf.access']['views'][0]['fields'][4]
            self.assertEqual(field['field']['element'],'A-local')
            field['temporal']='instant'
        c,h,a,tx=self.ready_temporal(original_instant)
        family=self.admin.execute("SELECT scalar_type,native_temporal FROM truss.prop_def WHERE element='A-local'").fetchone()
        self.assertEqual(family,('timestamp',None))
        self.admin.execute(psycopg.sql.SQL('GRANT {} TO consumer WITH SET FALSE').format(psycopg.sql.Identifier(self.installation.registrar_role)))
        source=json.loads(self.document.content)
        source['modules'][0]['extensions']['umf.access']['views'][0]['fields'][4]['temporal']='local'
        next_document=CatalogDocument('adoc','r2',json.dumps(source,ensure_ascii=True).encode())
        prepared=a.temporal_values().prepare_catalog((next_document,))
        before=self.registration_snapshot(c)
        rejected=a.temporal_values().accept_in_transaction(tx,prepared,request_key='no-timestamp-reinterpretation')
        self.assertIsInstance(rejected,Error,repr(rejected));self.assertEqual(rejected.error.sql_state,'0A000')
        self.assertEqual(self.registration_snapshot(c),before)
        self.assertEqual(self.admin.execute("SELECT scalar_type,native_temporal FROM truss.prop_def WHERE element='A-local'").fetchone(),family)
        h.detach();c.rollback()

    def test_mixed_temporal_archive_refuses_legacy_compact_reconstruction(self):
        c,h,a,tx=self.ready_temporal()
        self.admin.execute(psycopg.sql.SQL('GRANT {} TO consumer WITH SET FALSE').format(psycopg.sql.Identifier(self.installation.registrar_role)))
        prepared=self.fresh_preparation(a);before=self.registration_snapshot(c)
        result,_=self.faulted_accept(h,a,tx,prepared,'compact-downgrade')
        self.assertIsInstance(result,Error,repr(result));self.assertEqual(result.error.sql_state,'22023')
        self.assertEqual(self.registration_snapshot(c),before)
        h.detach();c.rollback()

    def test_temporal_replay_preserves_original_preparation_and_report_bytes(self):
        c,h,a,tx=self.ready_temporal()
        self.admin.execute(psycopg.sql.SQL('GRANT {} TO consumer WITH SET FALSE').format(psycopg.sql.Identifier(self.installation.registrar_role)))
        # Replay the actual first public acceptance after closing its transaction.
        selected=a.temporal_values()
        replay=selected.accept_in_transaction(tx,self.prepared,request_key='temporal-model')
        self.assertIsInstance(replay,Ok,repr(replay));self.assertTrue(replay.value.replayed)
        stored=self.admin.execute("SELECT input_bytes,document_bytes,declaration_bytes,source_bytes FROM truss.catalog_registration_request WHERE request_key='temporal-model'").fetchone()
        self.assertEqual(tuple(bytes(v) for v in stored[:3]),(self.prepared.input_bytes,self.prepared.archive_documents_bytes,self.prepared.declarations_bytes))
        source=json.loads(bytes(stored[3]));self.assertEqual(source['sourceFormat'],'truss-registration-summary/2.1')
        archived=json.loads(bytes(stored[1]));declarations=json.loads(bytes(stored[2]))
        self.assertEqual(archived[0]['originalText'].encode(),self.document.content)
        self.assertEqual(archived[0]['validation']['inspection'],source['documentValidations'][0]['inspection'])
        local=next(f for r in declarations[0]['records'] for f in r['fields'] if 'nativeDescriptor' in f)
        self.assertEqual(local['declaration']['scalarType'],'timestamp')
        self.assertEqual(local['nativeDescriptor']['nativeScalarType'],'localTimestamp')
        report=replay.value.report_bytes
        h.detach();c.commit()
        c,h,a,tx=self.consumer()
        again=a.temporal_values().accept_in_transaction(tx,self.prepared,request_key='temporal-model')
        self.assertIsInstance(again,Ok,repr(again));self.assertTrue(again.value.replayed)
        self.assertEqual(again.value.report_bytes,report)
        self.assertEqual(self.admin.execute("SELECT input_bytes,document_bytes,declaration_bytes,source_bytes FROM truss.catalog_registration_request WHERE request_key='temporal-model'").fetchone(),stored)
        h.detach();c.rollback()
