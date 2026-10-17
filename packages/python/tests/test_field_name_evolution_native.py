"""One public name-only evolution workflow retaining keys and original receipts."""
import json, os
from truss import Ok, Error, CatalogDocument, CatalogRegistration, CatalogAcceptanceRefused, ObjectFound, QueryRows, HistoryEntity, HistoricalRecord
from truss.contracts import MapValue, TextValue
from truss.groups import GroupSuccess, CommittedReceiptReplay, UpdateObject, StoredObjectReference, AuthoredValue
import test_group_create_native as base

class FieldNameEvolutionTests(base.PublicCreateGroupTests):
    for _name in tuple(n for n in dir(base.PublicCreateGroupTests) if n.startswith('test_')): locals()[_name]=None
    source_version='0.7.0'
    def fields(self, source):
        source['umf']=self.source_version
        elements=source['modules'][0]['elements']
        for e in elements:
            if e['kind']=='record':e['name']=e['id']
        if any(e['id']=='A' for e in elements):
            extra=json.loads(json.dumps(next(e for e in elements if e['id']=='A-label')))
            extra.update(id='A-extra',name='extra',nullability='absent-allowed')
            elements.append(extra)
            next(e for e in elements if e['id']=='A')['members'].append({'module':'m','element':'A-extra'})
    def test_public_key_and_nonkey_rename(self):
        c,h,a,t=self.ready(self.fields); originals=self.documents
        context=a.group_context_in_transaction(t).value
        semantic=context.input((self.create('one',alias='a'),),MapValue(entries=())); request=context.request('before-name-change')
        created=self.apply(a,t,semantic,request); self.assertIsInstance(created,GroupSuccess)
        identity=created.response.semantic.results[0].identity
        h.detach();c.commit()
        objects=self.admin.execute('SELECT to_jsonb(o) FROM truss.object o ORDER BY id').fetchall()
        keys=self.admin.execute('SELECT to_jsonb(k) FROM truss.object_key_bucket k ORDER BY storage_row_id').fetchall()
        definitions=self.admin.execute('SELECT prop_id,element FROM truss.prop_def ORDER BY prop_id').fetchall()
        self.admin.execute('GRANT '+self.installation.registrar_role+' TO consumer WITH SET FALSE')
        c,h,a,t=self.consumer()
        original=json.loads(next(d.content for d in originals if d.document_id=='adoc'))
        renamed=json.loads(json.dumps(original))
        names={'A-label':'label','A-value':'value','A-extra':'note'}
        for e in renamed['modules'][0]['elements']:
            if e['id'] in names:e['name']=names[e['id']]
        document=CatalogDocument('adoc','r2',json.dumps(renamed).encode())
        prepared=a.prepare_catalog((document,),source_version=self.source_version,bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        accepted=a.accept_in_transaction(t,prepared,request_key='field-names')
        self.assertIsInstance(accepted,Ok,repr(accepted));self.assertIsInstance(accepted.value,CatalogRegistration,repr(accepted.value))
        h.detach();c.commit()
        self.assertEqual(self.admin.execute('SELECT to_jsonb(o) FROM truss.object o ORDER BY id').fetchall(),objects)
        self.assertEqual(self.admin.execute('SELECT to_jsonb(k) FROM truss.object_key_bucket k ORDER BY storage_row_id').fetchall(),keys)
        self.assertEqual(self.admin.execute('SELECT prop_id,element FROM truss.prop_def ORDER BY prop_id').fetchall(),definitions)
        self.documents=tuple(document if d.document_id=='adoc' else d for d in originals)
        c,h,a,t=self.consumer()
        found=a.get_object_in_transaction(t,document_id='adoc',module_id='m',record_id='A',object_id=int(identity.id)).value
        self.assertIsInstance(found,ObjectFound);self.assertEqual(found.object.version,1)
        lookup=a.lookup_key_in_transaction(t,document_id='adoc',module_id='m',record_id='A',key_id='a-primary',values=(TextValue(kind='string',text='value'),TextValue(kind='string',text='one')),bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        self.assertIsInstance(lookup.value,ObjectFound,repr(lookup));self.assertEqual(lookup.value.object.identity.id,identity.id)
        query=a.query_in_transaction(t,sql='SELECT a."value", a."label" FROM "A" a',document_ids=('adoc',))
        self.assertIsInstance(query.value,QueryRows,repr(query));self.assertEqual(query.value.rows,(('value','one'),))
        context=a.group_context_in_transaction(t).value
        changed=self.apply(a,t,context.input((UpdateObject(target=StoredObjectReference(identity=found.object.identity),set=(AuthoredValue(name='value',value=TextValue(kind='string',text='changed')),AuthoredValue(name='note',value=TextValue(kind='string',text='new'))),unset=()),),MapValue(entries=())),context.request('after-name-change'))
        self.assertIsInstance(changed,GroupSuccess,repr(changed));h.detach();c.commit()
        c,h,a,t=self.consumer()
        history=a.reconstruct_in_transaction(t,entity=HistoryEntity(kind='object',document_id='adoc',module_id='m',definition_id='A',id=int(identity.id)),version=2).value
        self.assertIsInstance(history,HistoricalRecord,repr(history))
        replay=a.apply_in_transaction(t,semantic,request,documents=originals,bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        self.assertIsInstance(replay.value.response,CommittedReceiptReplay,repr(replay));h.detach();c.commit()
        # An existing retained value must not become hidden by a new field name.
        c,h,a,t=self.consumer()
        context=a.group_context_in_transaction(t).value
        retained=self.apply(a,t,context.input((UpdateObject(target=StoredObjectReference(identity=found.object.identity),set=(AuthoredValue(name='occupied',value=TextValue(kind='string',text='retained')),),unset=()),),MapValue(entries=())),context.request('retain-unknown-name'))
        self.assertIsInstance(retained,GroupSuccess,repr(retained));h.detach();c.commit()
        c,h,a,t=self.consumer()
        collision=json.loads(json.dumps(renamed))
        next(e for e in collision['modules'][0]['elements'] if e['id']=='A-extra')['name']='occupied'
        prepared=a.prepare_catalog((CatalogDocument('adoc','r3',json.dumps(collision).encode()),),source_version=self.source_version,bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        refused=a.accept_in_transaction(t,prepared,request_key='retained-name-collision')
        self.assertIsInstance(refused,Ok,repr(refused));self.assertIsInstance(refused.value,CatalogAcceptanceRefused,repr(refused))
        self.assertEqual({(v.field_id,v.rule,v.affected_object_count) for v in refused.value.violations},{('A-extra','property.retained_name_collision',1)})
        h.detach();c.rollback()
        # A moved name cannot be reused by a new member in either authored order.
        for new_first in (False,True):
            c,h,a,t=self.consumer()
            reuse=json.loads(json.dumps(renamed)); elements=reuse['modules'][0]['elements']
            next(e for e in elements if e['id']=='A-value')['name']='moved'
            added=json.loads(json.dumps(next(e for e in elements if e['id']=='A-extra')))
            added.update(id='new-field',name='value');elements.append(added)
            members=next(e for e in elements if e['id']=='A')['members']
            member={'module':'m','element':'new-field'}
            if new_first:members.insert(0,member)
            else:members.append(member)
            prepared=a.prepare_catalog((CatalogDocument('adoc','r3',json.dumps(reuse).encode()),),source_version=self.source_version,bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
            refused=a.accept_in_transaction(t,prepared,request_key='occupied-prior-name-'+str(new_first))
            self.assertIsInstance(refused,Error,repr(refused));self.assertEqual(refused.error.catalog_code,'unsupported_profile')
            h.detach();c.rollback()

class FieldNameEvolution08Tests(FieldNameEvolutionTests):
    source_version='0.8.0'

    def test_unset_after_name_change_preserves_historical_property_pin(self):
        """An old image's removed field need not occur in new-revision metadata."""
        from dataclasses import replace
        c,h,a,t=self.ready(self.fields)
        operation=self.create('remove-note')
        operation=replace(operation,values=operation.values+(
            AuthoredValue(name='extra',value=TextValue(kind='string',text='old-note')),))
        context=a.group_context_in_transaction(t).value
        created=self.apply(a,t,context.input((operation,),MapValue(entries=())),context.request('create-note'))
        self.assertIsInstance(created,GroupSuccess)
        identity=created.response.semantic.results[0].identity
        h.detach();c.commit()
        self.admin.execute('GRANT '+self.installation.registrar_role+' TO consumer WITH SET FALSE')
        c,h,a,t=self.consumer()
        source=json.loads(next(d.content for d in self.documents if d.document_id=='adoc'))
        next(e for e in source['modules'][0]['elements'] if e['id']=='A-extra')['name']='note'
        document=CatalogDocument('adoc','r2',json.dumps(source).encode())
        prepared=a.prepare_catalog((document,),source_version=self.source_version,bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        accepted=a.accept_in_transaction(t,prepared,request_key='rename-note')
        self.assertIsInstance(accepted,Ok,repr(accepted));self.assertIsInstance(accepted.value,CatalogRegistration)
        h.detach();c.commit()
        self.documents=tuple(document if d.document_id=='adoc' else d for d in self.documents)
        c,h,a,t=self.consumer()
        found=a.get_object_in_transaction(t,document_id='adoc',module_id='m',record_id='A',object_id=int(identity.id)).value
        context=a.group_context_in_transaction(t).value
        changed=self.apply(a,t,context.input((UpdateObject(target=StoredObjectReference(identity=found.object.identity),set=(),unset=('note',)),),MapValue(entries=())),context.request('remove-note'))
        self.assertIsInstance(changed,GroupSuccess);h.detach();c.commit()
        c,h,a,t=self.consumer()
        entity=HistoryEntity(kind='object',document_id='adoc',module_id='m',definition_id='A',id=int(identity.id))
        before=a.reconstruct_in_transaction(t,entity=entity,version=1).value
        after=a.reconstruct_in_transaction(t,entity=entity,version=2).value
        self.assertIsInstance(before,HistoricalRecord);self.assertIsInstance(after,HistoricalRecord)
        before_properties=json.loads(before.record)['properties'];after_properties=json.loads(after.record)['properties']
        self.assertIn({'kind':'string','text':'old-note'},[p['value'] for p in before_properties])
        self.assertNotIn({'kind':'string','text':'old-note'},[p['value'] for p in after_properties])
        first=a.page_history_in_transaction(t,entity=entity).value
        changed_history=a.page_history_in_transaction(t,entity=entity,cursor=first.continuation).value
        removal=next(json.loads(e.content) for e in changed_history.events if json.loads(e.content)['operation']=='property')
        expected_pin=self.admin.execute("SELECT definition_pin FROM truss.runtime_definition('property',%s,%s,%s)",
            (int(identity.type_id),int(removal['propertyId']),int(removal['eventCatalogRevision']))).fetchone()[0]
        self.assertEqual(removal['definitionPin'],expected_pin)
        self.assertEqual(removal['after'],{'present':False})
        h.detach();c.rollback()
