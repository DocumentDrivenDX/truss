"""One real adopter workflow through compatible acceptance and recovery."""
import json
from dataclasses import replace
import psycopg
from truss import CatalogDocument,CatalogRegistration,Ok,ObjectFound
from truss.contracts import TextValue,MapValue
from truss.groups import (CreateEdge,Delete,NullOrderKey,StoredObjectReference,AliasObjectReference,
    AuthoredValue,UpdateObject,GroupSuccess,CommittedReceiptReplay,RequestNone,KeyAbsent)
from truss.imports import EdgeImportIdentity,EdgeImportRecord,ImportReported,ImportSkipped
import test_object_mutations_native as mutation_tests


class CompatibleCatalogTests(mutation_tests.ObjectMutationTests):
    for _name in tuple(n for n in dir(mutation_tests.ObjectMutationTests) if n.startswith('test_')):
        locals()[_name]=None

    def test_evolve_read_write_lookup_and_original_catalog_group_recovery(self):
        connection,host,assembly,tx=self.ready()
        self.admin.execute(psycopg.sql.SQL('GRANT {} TO consumer WITH SET FALSE').format(psycopg.sql.Identifier(self.installation.registrar_role)))
        original=assembly.prepare_catalog(self.documents,bun_executable='/opt/homebrew/bin/bun')
        old_report=assembly.report_in_transaction(tx,1).value.original_bytes
        created,input,request=self.run_group(assembly,tx,(self.create(),self.create(label='two',value='other',record='B',alias='b')),'before-evolution')
        self.assertIsInstance(created,GroupSuccess);a,b=(v.identity for v in created.response.semantic.results)
        old_pin=assembly.get_relationship_reference_in_transaction(tx,document_id='adoc',module_id='m',relationship_id='A-B').value.definition_pin
        linked,_,_=self.run_group(assembly,tx,(CreateEdge(relationship_definition_pin=old_pin,source=StoredObjectReference(identity=a),target=StoredObjectReference(identity=b),values=(),order_key=NullOrderKey()),))
        self.assertIsInstance(linked,GroupSuccess)
        removed,_,_=self.run_group(assembly,tx,(Delete(operation='delete_edge',target=StoredObjectReference(identity=linked.response.semantic.results[0].identity)),))
        self.assertIsInstance(removed,GroupSuccess);host.detach();connection.commit()

        connection,host,assembly,tx=self.consumer()
        source=json.loads(next(v.content for v in self.documents if v.document_id=='adoc'))
        module=source['modules'][0]
        added_record=json.loads(json.dumps(next(v for v in module['elements'] if v['id']=='B')))
        added_record['id']='AA'
        added_fields=[]
        for suffix in ('label','value'):
            field=json.loads(json.dumps(next(v for v in module['elements'] if v['id']=='B-'+suffix)))
            field['id']=field['name']='AA-'+suffix;added_fields.append(field)
        for member in added_record['members']:member['element']=member['element'].replace('B-','AA-',1)
        for key in added_record['keys']:
            for member in key['fields']:member['element']=member['element'].replace('B-','AA-',1)
        next(v for v in module['elements'] if v['id']=='A')['members'].append({'module':'m','element':'A-note'})
        module['elements'].append({'id':'A-note','name':'A-note','kind':'field','scalarType':'string','nullability':'absent-allowed','cardinality':'one','extensions':{}})
        module['elements'].extend((added_record,*added_fields))
        module['relationships'][0]['targetMultiplicity']['max']='*'
        document=CatalogDocument('adoc','r2',json.dumps(source).encode())
        prepared=assembly.prepare_catalog((document,),bun_executable='/opt/homebrew/bin/bun')
        accepted=assembly.accept_in_transaction(tx,prepared,request_key='model-r2')
        if not isinstance(accepted,Ok):self.fail(repr(accepted)+' '+str(assembly._host._custody.last_attempt.error))
        self.assertIsInstance(accepted.value,CatalogRegistration);self.assertEqual(accepted.value.revision,2)
        self.documents=tuple(document if v.document_id=='adoc' else v for v in self.documents)
        view=assembly.catalog_view_in_transaction(tx,assembly.catalog_view_request()).value.view
        self.types={(v.reference.owner.document_id,v.reference.authored_identity):v.reference for v in view.definitions if v.reference.kind=='type'}
        published=assembly.accepted_document_in_transaction(tx,document_id='adoc').value
        self.assertEqual(published.content,document.content);self.assertEqual(published.document_revision,'r2')
        modules=assembly.reader_catalog_in_transaction(tx).value.modules
        self.assertEqual(len({(v['documentId'],v['moduleId']) for v in modules}),len(modules))
        self.assertEqual(next(v['documentRevision'] for v in modules if v['documentId']=='adoc'),'r2')
        current_a=self.read(assembly,tx,a).object
        self.assertNotIn('A-note',dict(current_a.values));self.assertEqual(current_a.version,1)
        current_a_identity=replace(a,definition_pin=self.types[('adoc','A')].definition_pin)
        self.assertEqual(str(current_a.type_id),a.type_id);self.assertNotEqual(current_a_identity.definition_pin,a.definition_pin)
        self.assertEqual(self.types[('adoc','B')].definition_pin,b.definition_pin)
        context=assembly.group_context_in_transaction(tx).value
        update_b=UpdateObject(target=StoredObjectReference(identity=b),set=(AuthoredValue(name='B-label',value=TextValue(kind='string',text='updated-b')),),unset=(),expected_version='1')
        conditional=context.input((update_b,),MapValue(entries=()),preconditions=(KeyAbsent(id='free-b',reason='must remain free',type_definition_pin=b.definition_pin,key_id='a-primary',values=(TextValue(kind='string',text='unused'),TextValue(kind='string',text='unused'))),))
        updated_b=assembly.apply_in_transaction(tx,conditional,RequestNone(),documents=self.documents,bun_executable='/opt/homebrew/bin/bun')
        self.assertIsInstance(updated_b.value,GroupSuccess)
        changed,_,_=self.run_group(assembly,tx,(UpdateObject(target=StoredObjectReference(identity=current_a_identity),set=(AuthoredValue(name='A-note',value=TextValue(kind='string',text='new')),),unset=(),expected_version='1'),))
        self.assertIsInstance(changed,GroupSuccess)
        added,_,_=self.run_group(assembly,tx,(self.create(label='new-a',value='new-a'),self.create(label='new-b',value='new-b',record='B',alias='b'),self.create(label='new-aa',value='new-aa',record='AA',alias='aa')))
        self.assertIsInstance(added,GroupSuccess)
        looked=assembly.lookup_key_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',key_id='a-primary',values=('value','one'),bun_executable='/opt/homebrew/bin/bun')
        self.assertIsInstance(looked.value,ObjectFound);self.assertEqual(str(looked.value.object.id),a.id)
        recovered=assembly.apply_in_transaction(tx,input,request,documents=self.documents,bun_executable='/no-owner-producer-needed')
        self.assertIsInstance(recovered.value.response,CommittedReceiptReplay);self.assertEqual(recovered.value.response.semantic,created.response.semantic)
        current_b=replace(b,definition_pin=self.types[('adoc','B')].definition_pin)
        new_pin=assembly.get_relationship_reference_in_transaction(tx,document_id='adoc',module_id='m',relationship_id='A-B').value.definition_pin
        self.assertNotEqual(new_pin,old_pin)
        context=assembly.import_context_in_transaction(tx).value
        edge=EdgeImportRecord(identity=EdgeImportIdentity(relationship_definition_pin=new_pin,source=current_a_identity,target=current_b),payload=context.edge_payload((),NullOrderKey()),payload_profile=context.payload_profile)
        imported=assembly.import_in_transaction(tx,context.input((edge,),load_id='after-evolution',asserted_origin=MapValue(entries=())),documents=self.documents,bun_executable='/opt/homebrew/bin/bun')
        self.assertIsInstance(imported,ImportReported);self.assertIsInstance(imported.report.outcomes[0],ImportSkipped)
        self.assertEqual(imported.report.outcomes[0].reason,'reserved_identity')
        historical=assembly.accept_in_transaction(tx,original,request_key='create-model')
        self.assertEqual(historical.value.report_bytes,old_report);self.assertTrue(historical.value.replayed)
        context=assembly.group_context_in_transaction(tx).value
        default_documents=assembly.apply_in_transaction(tx,context.input((self.create(label='after-replay',value='after-replay'),),MapValue(entries=())),RequestNone(),bun_executable='/opt/homebrew/bin/bun')
        self.assertIsInstance(default_documents.value,GroupSuccess)
        host.detach();connection.commit()
        self.assertEqual(self.admin.execute('SELECT rev FROM truss.schema_head').fetchone(),(2,))
