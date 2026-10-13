"""Small adopter workflows for public caller-owned imports."""
import base64,json
from dataclasses import replace
from hashlib import sha256
from truss import (Ok,HistoryEntity,ImportSourceFound,ImportSourceAbsent,adopt_psycopg_host,create_reference_assembly,CatalogRuntimeConfiguration)
from truss.contracts import MapValue,MapEntry,TextValue,NullValue,ExactArtifact
from truss.groups import GroupSuccess,Delete,StoredObjectReference,NullOrderKey
from truss.imports import ImportReported,ImportCreated,ImportSkipped,ImportRejected,EdgeImportRecord
import test_object_mutations_native as mutation_tests

class ImportRuntimeTests(mutation_tests.ObjectMutationTests):
    for _name in tuple(n for n in dir(mutation_tests.ObjectMutationTests) if n.startswith('test_')):
        locals()[_name]=None

    def assert_retained_source(self,identity,*,kind,definition,load,source,not_imported=None):
        connection,host,assembly,tx=self.consumer();host.detach();connection.execute('SET TRANSACTION READ ONLY')
        host=adopt_psycopg_host(connection);self.addCleanup(host.detach)
        assembly=create_reference_assembly(CatalogRuntimeConfiguration(),host).value
        tx=host.adopt_transaction(access_mode='read_only').value
        reader=assembly.direct_reads(assembly.direct_read_selection).capability
        result=reader.lookup_import_source_in_transaction(tx,entity=HistoryEntity(kind=kind,document_id='adoc',module_id='m',definition_id=definition,id=int(identity.id)))
        if not isinstance(result,Ok):self.fail(repr(result)+' '+str(host._custody.last_attempt.error))
        self.assertIsInstance(result.value,ImportSourceFound)
        self.assertEqual(result.value.load_id,load)
        self.assertEqual(json.loads(result.value.content)['source'],source)
        self.assertEqual(sha256(result.value.content).hexdigest(),result.value.sha256)
        if not_imported is not None:
            absent=reader.lookup_import_source_in_transaction(tx,entity=HistoryEntity(kind='object',document_id='adoc',module_id='m',definition_id='A',id=int(not_imported.id)))
            self.assertIsInstance(absent,Ok);self.assertIsInstance(absent.value,ImportSourceAbsent)
        host.detach();self.assertIsNone(connection.execute('SELECT pg_current_xact_id_if_assigned()').fetchone()[0]);connection.rollback()

    def artifact(self,raw):
        digest=sha256(raw).hexdigest();return ExactArtifact(identity=digest,sha256=digest,bytes_base64=base64.b64encode(raw).decode())

    def record(self,assembly,tx,label='one',record='A',source=None):
        result=assembly.object_import_record_in_transaction(tx,document_id='adoc',module_id='m',record_id=record,
            values=self.create(label=label,value=label,record=record).values,source=source)
        if not isinstance(result,Ok):self.fail(repr(result)+' '+str(assembly._host._custody.last_attempt.error))
        return result.value

    def execute(self,assembly,tx,context,records,load='load'):
        input=context.input(records,load_id=load,asserted_origin=MapValue(entries=(MapEntry(key='x-initiated-by',value=TextValue(kind='string',text='adapter')),)))
        result=assembly.import_in_transaction(tx,input,documents=self.documents,bun_executable='/opt/homebrew/bin/bun')
        if not isinstance(result,ImportReported):self.fail(repr(result)+' '+str(assembly._host._custody.last_attempt.error))
        return result.report

    def test_create_skip_invalid_replacement_reject_source_commit_and_retry(self):
        connection,host,assembly,tx=self.ready();context=assembly.import_context_in_transaction(tx).value
        source=MapValue(entries=(MapEntry(key='author',value=NullValue()),MapEntry(key='at',value=TextValue(kind='string',text='2020-01-01')),MapEntry(key='system',value=TextValue(kind='string',text='old'))))
        first=self.record(assembly,tx,source=source);duplicate=replace(first,payload=self.artifact(b'not a valid payload'))
        bad=self.record(assembly,tx,label='bad');bad=replace(bad,payload=context.object_payload(()))
        report=self.execute(assembly,tx,context,(first,duplicate,bad));self.assertEqual([type(v) for v in report.outcomes],[ImportCreated,ImportSkipped,ImportRejected])
        self.assertEqual((report.counts.created_pending,report.counts.skipped,report.counts.rejected),('1','1','1'))
        identity=report.outcomes[0].identity;host.detach();connection.commit()
        self.assertEqual(self.admin.execute('SELECT load_id,source FROM truss.record_source').fetchone(),('load',{'author':None,'at':'2020-01-01','system':'old'}))
        event=json.loads(self.admin.execute("SELECT convert_from(decode(new_value->>'bytesBase64','base64'),'UTF8') FROM truss.journal LIMIT 1").fetchone()[0])
        self.assertEqual(event['origin']['databaseRole'],'consumer');self.assertIn({'key':'x-initiated-by','value':{'kind':'string','text':'adapter'}},event['origin']['asserted']['entries'])
        connection,host,assembly,tx=self.consumer();context=assembly.import_context_in_transaction(tx).value
        replay=self.execute(assembly,tx,context,(duplicate,),load='replacement');self.assertIsInstance(replay.outcomes[0],ImportSkipped)
        deleted,_,_=self.run_group(assembly,tx,(Delete(operation='delete_object',target=StoredObjectReference(identity=identity)),));self.assertIsInstance(deleted,GroupSuccess)
        reserved=self.execute(assembly,tx,context,(duplicate,));self.assertEqual(reserved.outcomes[0].reason,'reserved_identity')
        host.detach();connection.commit();self.assertEqual(self.admin.execute('SELECT load_id FROM truss.record_source').fetchall(),[('load',)])
        self.assert_retained_source(identity,kind='object',definition='A',load='load',source={'author':None,'at':'2020-01-01','system':'old'})

    def test_objects_before_edges_rollback_and_deleted_edge_reservation(self):
        connection,host,assembly,tx=self.ready();created,_,_=self.run_group(assembly,tx,(self.create(),self.create(label='two',value='two',record='B',alias='b')))
        a,b=(r.identity for r in created.response.semantic.results)
        pin=assembly.get_relationship_reference_in_transaction(tx,document_id='adoc',module_id='m',relationship_id='A-B').value.definition_pin
        host.detach();connection.commit();connection,host,assembly,tx=self.consumer();context=assembly.import_context_in_transaction(tx).value
        imports=assembly.imports(assembly.import_selection,documents=self.documents,bun_executable='/opt/homebrew/bin/bun').capability
        built=imports.edge_import_record_in_transaction(tx,document_id='adoc',module_id='m',relationship_id='A-B',
            source_endpoint=a,target_endpoint=b,values=(),order_key=NullOrderKey())
        self.assertIsInstance(built,Ok);edge=built.value
        self.assertIsInstance(edge,EdgeImportRecord);self.assertEqual(edge.identity.relationship_definition_pin,pin)
        self.assertIs(edge.identity.source,a);self.assertIs(edge.identity.target,b)
        object_record=self.record(assembly,tx,label='third',record='B')
        report=self.execute(assembly,tx,context,(edge,object_record));self.assertTrue(all(isinstance(v,ImportCreated) for v in report.outcomes))
        self.assertGreater(int(report.outcomes[0].identity.id),int(report.outcomes[1].identity.id))
        host.detach();connection.rollback();self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.edge').fetchone(),(0,));self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.record_source').fetchone(),(0,))
        connection,host,assembly,tx=self.consumer();context=assembly.import_context_in_transaction(tx).value
        created=self.execute(assembly,tx,context,(edge,));identity=created.outcomes[0].identity
        deleted,_,_=self.run_group(assembly,tx,(Delete(operation='delete_edge',target=StoredObjectReference(identity=identity)),));self.assertIsInstance(deleted,GroupSuccess)
        bad=replace(edge,payload=self.artifact(b'invalid replacement'))
        reserved=self.execute(assembly,tx,context,(bad,));self.assertEqual(reserved.outcomes[0].reason,'reserved_identity')
        host.detach();connection.commit();self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.record_source').fetchone(),(1,))
        self.assert_retained_source(identity,kind='edge',definition='A-B',load='load',source={},not_imported=a)
