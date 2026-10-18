"""Every unchanged stress schema through public preparation and native registration."""
import json,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'scripts'))
from performance_workloads import schema,workloads,values
from truss import (CatalogDocument,Ok,ModuleAccessGrant,adopt_psycopg_host,
    create_reference_assembly,CatalogRuntimeConfiguration,ObjectFound,EdgeFound,QueryRows)
from truss.contracts import MapValue,TextValue
from truss.groups import (CreateObject,RootlessOwnership,GroupSuccess,RequestNone,
    CreateEdge,StoredObjectReference,NullOrderKey,KeyAbsent,RelationshipAbsent,
    UpdateObject,AuthoredValue)
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

    def test_thousand_distinct_type_update_batch(self):
        """A full update batch crosses all 1,000 compiled type shapes."""
        workload=workloads()['many-types']
        source=schema(workload);document=source['id']
        raw=json.dumps(source,separators=(',',':')).encode()
        documents=(CatalogDocument(document,'matrix-v1',raw),)
        self.install();connection,host,assembly,tx=self.consumer()
        accepted=assembly.accept_in_transaction(tx,assembly.prepare_catalog(documents),request_key='many-types-update')
        self.assertIsInstance(accepted,Ok,repr(accepted)+' '+str(host._custody.last_attempt.error))
        view=assembly.catalog_view_in_transaction(tx,assembly.catalog_view_request()).value.view
        references={entry.reference.authored_identity:entry.reference for entry in view.definitions if entry.reference.kind=='type'}
        host.detach();connection.commit()
        import psycopg
        for role in ('many_types_reader','many_types_writer'):
            self.admin.execute(psycopg.sql.SQL('CREATE ROLE {} NOLOGIN').format(psycopg.sql.Identifier(role)))
            self.addCleanup(self.admin.execute,psycopg.sql.SQL('DROP ROLE {}').format(psycopg.sql.Identifier(role)))
        self.admin.execute('BEGIN');admin_host=adopt_psycopg_host(self.admin)
        admin_tx=admin_host.adopt_transaction().value
        admin_assembly=create_reference_assembly(CatalogRuntimeConfiguration(),admin_host).value
        configured=admin_assembly.configure_module_access_in_transaction(admin_tx,
            (ModuleAccessGrant(document,'m','many_types_reader','many_types_writer'),))
        self.assertIsInstance(configured,Ok,repr(configured))
        admin_host.detach();self.admin.commit()
        self.admin.execute('GRANT many_types_writer TO consumer WITH SET FALSE')
        self.admin.execute(psycopg.sql.SQL('REVOKE {} FROM consumer').format(psycopg.sql.Identifier(self.installation.registrar_role)))

        connection,host,assembly,tx=self.consumer()
        context=assembly.group_context_in_transaction(tx).value
        identities=[]
        for start in range(0,1000,100):
            creates=tuple(CreateObject(type_definition_pin=references['R'+str(i)].definition_pin,
                values=values(workload,i),ownership=RootlessOwnership(),alias='update-row'+str(i))
                for i in range(start,start+100))
            created=assembly.apply_in_transaction(tx,context.input(creates,MapValue(entries=())),
                RequestNone(),documents=documents)
            self.assertIsInstance(created,Ok,repr(created)+' '+str(host._custody.last_attempt.error))
            self.assertIsInstance(created.value,GroupSuccess,repr(created))
            identities.extend(item.identity for item in created.value.response.semantic.results)
        self.assertEqual(len(identities),1000)
        host.detach();connection.commit()

        connection,host,assembly,tx=self.consumer()
        context=assembly.group_context_in_transaction(tx).value
        updates=tuple(UpdateObject(target=StoredObjectReference(identity=identity),
            set=(AuthoredValue(name='p2',value=TextValue(kind='string',text='updated-'+str(i))),),unset=())
            for i,identity in enumerate(identities))
        result=assembly.apply_in_transaction(tx,context.input(updates,MapValue(entries=())),
            RequestNone(),documents=documents)
        self.assertIsInstance(result,Ok,repr(result)+' '+str(host._custody.last_attempt.error))
        self.assertIsInstance(result.value,GroupSuccess,repr(result))
        self.assertEqual(len(result.value.response.semantic.results),1000)
        self.assertTrue(all(item.outcome=='changed' and item.version=='2'
            for item in result.value.response.semantic.results))
        host.detach();connection.commit()

        # Prove the batch committed every distinct typed update and its exact
        # history payload, then read representative values through the public API.
        object_values=self.admin.execute('''SELECT o.id,cell.value->>'text' FROM truss.object o
            CROSS JOIN LATERAL jsonb_each(o.props) cell
            JOIN truss.prop_def p ON p.type_id=o.type_id AND p.prop_id=cell.key::int
            WHERE p.name='p2' ''').fetchall()
        expected_values={int(identity.id):'updated-'+str(i) for i,identity in enumerate(identities)}
        self.assertEqual(len(object_values),1000)
        self.assertEqual(dict(object_values),expected_values)
        journal_values=self.admin.execute('''SELECT j.entity_id,decoded.event->'after'->'value'->>'text' FROM truss.journal j
            JOIN truss.prop_def p ON p.type_id=j.entity_type AND p.prop_id=j.prop_id
            CROSS JOIN LATERAL (SELECT convert_from(decode(j.new_value->>'bytesBase64','base64'),'UTF8')::jsonb event) decoded
            WHERE j.entity_kind='o' AND j.op='update' AND p.name='p2' ''').fetchall()
        self.assertEqual(len(journal_values),1000)
        self.assertEqual(dict(journal_values),expected_values)
        connection,host,assembly,tx=self.consumer()
        for i in (0,499,999):
            opened=assembly.get_object_in_transaction(tx,document_id=document,module_id='m',
                record_id='R'+str(i),object_id=int(identities[i].id))
            self.assertIsInstance(opened,Ok,repr(opened)+' '+str(host._custody.last_attempt.error))
            self.assertIsInstance(opened.value,ObjectFound,repr(opened.value))
            self.assertEqual(dict(opened.value.object.values)['p2'],'updated-'+str(i))
        host.detach();connection.rollback()

    def test_thousand_distinct_type_single_create_group(self):
        """One atomic create group resolves graph checks for 1,000 record types."""
        workload=workloads()['many-types']
        source=schema(workload);document=source['id']
        raw=json.dumps(source,separators=(',',':')).encode()
        documents=(CatalogDocument(document,'matrix-v1',raw),)
        self.install();connection,host,assembly,tx=self.consumer()
        accepted=assembly.accept_in_transaction(tx,assembly.prepare_catalog(documents),request_key='many-types-single-create')
        self.assertIsInstance(accepted,Ok,repr(accepted)+' '+str(host._custody.last_attempt.error))
        view=assembly.catalog_view_in_transaction(tx,assembly.catalog_view_request()).value.view
        references={entry.reference.authored_identity:entry.reference for entry in view.definitions if entry.reference.kind=='type'}
        host.detach();connection.commit()
        import psycopg
        for role in ('many_types_reader','many_types_writer'):
            self.admin.execute(psycopg.sql.SQL('CREATE ROLE {} NOLOGIN').format(psycopg.sql.Identifier(role)))
            self.addCleanup(self.admin.execute,psycopg.sql.SQL('DROP ROLE {}').format(psycopg.sql.Identifier(role)))
        self.admin.execute('BEGIN');admin_host=adopt_psycopg_host(self.admin)
        admin_tx=admin_host.adopt_transaction().value
        admin_assembly=create_reference_assembly(CatalogRuntimeConfiguration(),admin_host).value
        configured=admin_assembly.configure_module_access_in_transaction(admin_tx,
            (ModuleAccessGrant(document,'m','many_types_reader','many_types_writer'),))
        self.assertIsInstance(configured,Ok,repr(configured))
        admin_host.detach();self.admin.commit()
        self.admin.execute('GRANT many_types_writer TO consumer WITH SET FALSE')
        self.admin.execute(psycopg.sql.SQL('REVOKE {} FROM consumer').format(psycopg.sql.Identifier(self.installation.registrar_role)))

        connection,host,assembly,tx=self.consumer()
        context=assembly.group_context_in_transaction(tx).value
        operations=tuple(CreateObject(type_definition_pin=references['R'+str(i)].definition_pin,
            values=values(workload,i),ownership=RootlessOwnership(),alias='single-row'+str(i)) for i in range(1000))
        result=assembly.apply_in_transaction(tx,context.input(operations,MapValue(entries=())),
            RequestNone(),documents=documents)
        self.assertIsInstance(result,Ok,repr(result)+' '+str(host._custody.last_attempt.error))
        self.assertIsInstance(result.value,GroupSuccess,repr(result))
        self.assertEqual(len(result.value.response.semantic.results),1000)
        self.assertTrue(all(item.outcome=='created' and item.version=='1'
            for item in result.value.response.semantic.results))
        connection.execute('SET CONSTRAINTS ALL IMMEDIATE')
        host.detach();connection.commit()
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone()[0],1000)
        stored=self.admin.execute('''SELECT cell.value->>'text' FROM truss.object o
            CROSS JOIN LATERAL jsonb_each(o.props) cell
            JOIN truss.prop_def p ON p.type_id=o.type_id AND p.prop_id=cell.key::int
            WHERE p.name='p0' ORDER BY o.id''').fetchall()
        self.assertEqual(stored,[(f'p0-{i}',) for i in range(1000)])

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
