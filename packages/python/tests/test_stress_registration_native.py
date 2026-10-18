"""Every unchanged stress schema through public preparation and native registration."""
import json,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'scripts'))
from performance_workloads import schema,workloads,values
from truss import (CatalogDocument,Ok,ModuleAccessGrant,adopt_psycopg_host,
    create_reference_assembly,CatalogRuntimeConfiguration,ObjectFound,EdgeFound,QueryRows)
from truss.contracts import MapValue,TextValue
from truss.groups import (CreateObject,RootlessOwnership,GroupSuccess,RequestNone,
    CreateEdge,StoredObjectReference,NullOrderKey,KeyAbsent,RelationshipAbsent)
from truss.catalog_results import CatalogRegistration
import test_catalog_runtime_native as base
class StressRegistrationTests(base.PublicCatalogRuntimeTests):
    for _name in tuple(n for n in dir(base.PublicCatalogRuntimeTests) if n.startswith('test_')):locals()[_name]=None

    def test_thousand_type_catalog_first_distinct_type_create_batch(self):
        # Registration alone missed repeated whole-document parsing during key
        # admission. Exercise the first unchanged matrix batch after registration.
        workload=workloads()['many-types']
        source=schema(workload);document=source['id']
        raw=json.dumps(source,separators=(',',':')).encode()
        documents=(CatalogDocument(document,'matrix-v1',raw),)
        self.install();connection,host,assembly,tx=self.consumer()
        accepted=assembly.accept_in_transaction(tx,assembly.prepare_catalog(documents),request_key='many-types-create')
        self.assertIsInstance(accepted,Ok,repr(accepted)+' '+str(host._custody.last_attempt.error))
        view=assembly.catalog_view_in_transaction(tx,assembly.catalog_view_request()).value.view
        references={entry.reference.authored_identity:entry.reference for entry in view.definitions if entry.reference.kind=='type'}
        relationships={entry.reference.authored_identity:entry.reference for entry in view.definitions if entry.reference.kind=='relationship'}
        host.detach();connection.commit()
        import psycopg
        for role in ('many_types_reader','many_types_writer'):
            self.admin.execute(psycopg.sql.SQL('CREATE ROLE {} NOLOGIN').format(psycopg.sql.Identifier(role)))
            self.addCleanup(self.admin.execute,psycopg.sql.SQL('DROP ROLE {}').format(psycopg.sql.Identifier(role)))
        self.admin.execute('BEGIN');admin_host=adopt_psycopg_host(self.admin)
        admin_tx=admin_host.adopt_transaction().value
        admin_assembly=create_reference_assembly(CatalogRuntimeConfiguration(),admin_host).value
        self.assertIsInstance(admin_assembly.configure_module_access_in_transaction(admin_tx,
            (ModuleAccessGrant(document,'m','many_types_reader','many_types_writer'),)),Ok)
        admin_host.detach();self.admin.commit()
        self.admin.execute('GRANT many_types_writer TO consumer WITH SET FALSE')
        self.admin.execute(psycopg.sql.SQL('REVOKE {} FROM consumer').format(psycopg.sql.Identifier(self.installation.registrar_role)))
        connection,host,assembly,tx=self.consumer()
        operations=tuple(CreateObject(type_definition_pin=references['R'+str(i)].definition_pin,
            values=values(workload,i),ownership=RootlessOwnership(),alias='row'+str(i)) for i in range(100))
        conditions=tuple(KeyAbsent(id='fresh'+str(i),reason='new object key',
            type_definition_pin=references['R'+str(i)].definition_pin,key_id='key0',
            values=(TextValue(kind='string',text='p0-'+str(i)),)) for i in range(100))
        context=assembly.group_context_in_transaction(tx).value
        result=assembly.apply_in_transaction(tx,context.input(operations,MapValue(entries=()),
            preconditions=conditions),RequestNone(),documents=documents)
        self.assertIsInstance(result,Ok,repr(result)+' '+str(host._custody.last_attempt.error))
        self.assertIsInstance(result.value,GroupSuccess,repr(result))
        # The original 1,000-type batch must use the production application
        # schema, not merely expose an unrelated catalog-view index.
        from truss import _schema_memory
        selected=_schema_memory.record_schemas(assembly._record_schema_state['key'])
        self.assertIsNotNone(selected)
        self.assertEqual(len(selected.compiled._records),1000)
        self.assertEqual(sum(len(record.properties_by_name) for record in selected.compiled._records.values()),12000)
        print(json.dumps({'applicationSchema':{'recordTypes':1000,'properties':12000,
            'estimatedResidentBytes':_schema_memory._resident_size(selected),
            'sharedCacheRetainedBytes':_schema_memory._cache_bytes,
            'retainedBudgetBytes':_schema_memory.MAX_CACHE_BYTES}}),flush=True)
        identities=tuple(item.identity for item in result.value.response.semantic.results)
        self.assertEqual(len(identities),100)
        host.detach();connection.commit();connection,host,assembly,tx=self.consumer()
        for i,identity in enumerate(identities):
            opened=assembly.get_object_in_transaction(tx,document_id=document,module_id='m',record_id='R'+str(i),object_id=int(identity.id))
            self.assertIsInstance(opened,Ok,repr(opened)+' '+str(host._custody.last_attempt.error))
            self.assertIsInstance(opened.value,ObjectFound,repr(opened.value))
            self.assertEqual(opened.value.object.identity,identity)
            self.assertEqual(dict(opened.value.object.values)['p0'],'p0-'+str(i))
        # The same cold source-coordinate join previously made relationship
        # admission scan every source row once per unrelated relationship.
        edges=tuple(CreateEdge(relationship_definition_pin=relationships['R'+str(i)+'.link'].definition_pin,
            source=StoredObjectReference(identity=identity),target=StoredObjectReference(identity=identity),
            values=(),order_key=NullOrderKey()) for i,identity in enumerate(identities))
        unlinked=tuple(RelationshipAbsent(id='unlinked'+str(i),reason='new link',
            relationship_definition_pin=relationships['R'+str(i)+'.link'].definition_pin,
            source=identity,target=identity) for i,identity in enumerate(identities))
        context=assembly.group_context_in_transaction(tx).value
        linked=assembly.apply_in_transaction(tx,context.input(edges,MapValue(entries=()),
            preconditions=unlinked),RequestNone(),documents=documents)
        self.assertIsInstance(linked,Ok,repr(linked)+' '+str(host._custody.last_attempt.error))
        self.assertIsInstance(linked.value,GroupSuccess,repr(linked))
        edge_identities=tuple(item.identity for item in linked.value.response.semantic.results)
        self.assertEqual(len(edge_identities),100)
        host.detach();connection.commit();connection,host,assembly,tx=self.consumer()
        for i,identity in enumerate(edge_identities):
            opened=assembly.get_edge_in_transaction(tx,document_id=document,module_id='m',relationship_id='R'+str(i)+'.link',edge_id=int(identity.id))
            self.assertIsInstance(opened,Ok,repr(opened)+' '+str(host._custody.last_attempt.error))
            self.assertIsInstance(opened.value,EdgeFound,repr(opened.value))
            self.assertEqual(opened.value.edge.source,identities[i]);self.assertEqual(opened.value.edge.target,identities[i])
        # Registration and writes alone missed the compiler's smaller binding
        # JSON node limit for this original 1,000-record schema.
        listed=assembly.query_in_transaction(tx,sql='SELECT x.* FROM "R0" x LIMIT 51',
            document_ids=(document,),maximum_bytes=16777216,read_profile='complete-entity')
        self.assertIsInstance(listed,Ok,repr(listed)+' '+str(host._custody.last_attempt.error))
        self.assertIsInstance(listed.value,QueryRows,repr(listed.value))
        self.assertEqual(len(listed.value.rows),1)
        self.assertEqual(dict(zip(listed.value.columns,listed.value.rows[0],strict=True))['p0'],'p0-0')
        host.detach();connection.rollback()

def registration_case(name,workload):
    def run(self):
        raw=json.dumps(schema(workload),separators=(',',':')).encode()
        self.install();connection,host,assembly,tx=self.consumer()
        prepared=assembly.prepare_catalog((CatalogDocument('perf-'+name,'matrix-v1',raw),))
        self.assertEqual(prepared.documents[0].document.content,raw)
        self.assertIsNone(prepared.documents[0].observation()['transition'])
        started=time.monotonic()
        accepted=assembly.accept_in_transaction(tx,prepared,request_key='matrix-'+name)
        self.assertIsInstance(accepted,Ok,repr(accepted)+' '+str(host._custody.last_attempt.error))
        self.assertIsInstance(accepted.value,CatalogRegistration,repr(accepted))
        host.detach();connection.commit()
        # Source has one custody home. Receipts and pin indexes hold references.
        self.assertEqual(self.admin.execute('SELECT octet_length(document_bytes),octet_length(declaration_bytes) FROM truss.catalog_registration_request WHERE revision=1').fetchone(),(0,0))
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.schema_change').fetchone(),(0,))
        self.assertEqual(self.admin.execute("SELECT count(*) FROM pg_attribute WHERE attrelid='truss.runtime_definition_source'::regclass AND attname='fragment' AND NOT attisdropped").fetchone(),(0,))
        homes=('schema_doc','type_def','prop_def','key_def','rel_def','runtime_definition_source','catalog_registration_request','catalog_acceptance_report')
        sizes={home:self.admin.execute('SELECT pg_total_relation_size(%s::regclass)',('truss.'+home,)).fetchone()[0] for home in homes}
        print(json.dumps({'schema':name,'sourceBytes':len(raw),'registrationSeconds':time.monotonic()-started,'storageBytesIncludingIndexesAndToast':sizes}),flush=True)
    return run
for name,workload in workloads().items():setattr(StressRegistrationTests,'test_'+name.replace('-','_'),registration_case(name,workload))
