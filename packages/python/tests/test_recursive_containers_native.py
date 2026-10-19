# SPDX-License-Identifier: MIT OR Apache-2.0
"""Basic public nested-container workflow preserving exact decimal tokens."""
import json,os
from decimal import Decimal
from dataclasses import replace
from truss import Ok,ObjectFound,HistoryEntity,HistoricalRecord,QueryRows
from truss.contracts import MapValue,MapEntry,SequenceValue,TextValue
from truss.groups import AuthoredValue,GroupSuccess,GroupFailed
from truss.imports import ImportReported,ImportCreated
import test_group_create_native as base

class RecursiveContainerTests(base.PublicCreateGroupTests):
    for _name in tuple(n for n in dir(base.PublicCreateGroupTests) if n.startswith('test_')):locals()[_name]=None
    source_version='0.10.0'
    def fields(self,source):
        source['umf']=self.source_version;module=source['modules'][0]
        for element in module['elements']:
            if element['kind']=='record':element['name']=element['id']
        value=next(e for e in module['elements'] if e['id']=='A-value')
        value.pop('scalarType');value.update(cardinality='map',nullability='required',itemType={'module':'m','element':'nested-sequence'})
        module['elements'] += [
            {'id':'nested-sequence','name':'nested-sequence','kind':'field','cardinality':'array','nullability':'required','itemType':{'module':'m','element':'decimal-item'},'extensions':{}},
            {'id':'decimal-item','name':'decimal-item','kind':'field','cardinality':'one','nullability':'required','scalarType':'decimal','facets':{'precision':18,'scale':4},'extensions':{}}]
        record=next(e for e in module['elements'] if e['id']=='A')
        record['keys']=[{'id':'a-primary','name':'primary','primary':True,'fields':[{'module':'m','element':'A-label'}]}]
    def test_create_commit_read_and_reconstruct(self):
        c,h,a,t=self.ready(self.fields)
        value=MapValue(entries=(MapEntry(key='z',value=SequenceValue(items=(TextValue(kind='decimal',text='99999999999999.9999'),TextValue(kind='decimal',text='1.23000')))),MapEntry(key='empty',value=SequenceValue(items=()))))
        operation=replace(self.create(),values=(AuthoredValue(name='A-label',value=TextValue(kind='string',text='one')),AuthoredValue(name='A-value',value=value)))
        context=a.group_context_in_transaction(t).value
        created=self.apply(a,t,context.input((operation,),MapValue(entries=())),context.request('nested-create'))
        self.assertIsInstance(created,GroupSuccess)
        identity=created.response.semantic.results[0].identity
        invalid=MapValue(entries=(MapEntry(key='bad',value=SequenceValue(items=(TextValue(kind='string',text='wrong leaf'),))),))
        bad=replace(operation,values=(AuthoredValue(name='A-label',value=TextValue(kind='string',text='bad')),AuthoredValue(name='A-value',value=invalid)))
        refused=self.apply(a,t,context.input((bad,),MapValue(entries=())),context.request('invalid-nested-leaf'))
        self.assertIsInstance(refused,GroupFailed)
        h.detach();c.commit()
        c,h,a,t=self.consumer()
        found=a.get_object_in_transaction(t,document_id='adoc',module_id='m',record_id='A',object_id=int(identity.id))
        self.assertIsInstance(found.value,ObjectFound,repr(found))
        actual=dict(found.value.object.values)['A-value']
        self.assertEqual(tuple(e.key for e in actual.entries),('empty','z'))
        self.assertEqual(actual.entries[1].value.items[0].text,'99999999999999.9999')
        self.assertEqual(actual.entries[1].value.items[1].text,'1.23000')
        history=a.reconstruct_in_transaction(t,entity=HistoryEntity(kind='object',document_id='adoc',module_id='m',definition_id='A',id=int(identity.id)),version=1)
        self.assertIsInstance(history.value,HistoricalRecord,repr(history))
        query=a.query_in_transaction(t,sql='SELECT a."A-value" FROM "A" a',document_ids=('adoc',))
        self.assertIsInstance(query.value,QueryRows,repr(query))
        nested=query.value.rows[0][0]
        self.assertEqual(nested['empty'],())
        self.assertEqual(nested['z'],(Decimal('99999999999999.9999'),Decimal('1.23000')))
        self.assertEqual(str(nested['z'][1]),'1.23000')
        imported_values=(AuthoredValue(name='A-label',value=TextValue(kind='string',text='imported')),AuthoredValue(name='A-value',value=value))
        built=a.object_import_record_in_transaction(t,document_id='adoc',module_id='m',record_id='A',values=imported_values,source=MapValue(entries=(MapEntry(key='author',value=TextValue(kind='string',text='consumer')),)))
        self.assertIsInstance(built,Ok,repr(built))
        import_context=a.import_context_in_transaction(t).value
        imported=a.import_in_transaction(t,import_context.input((built.value,),load_id='nested-import',asserted_origin=MapValue(entries=())),documents=self.documents,bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        self.assertIsInstance(imported,ImportReported,repr(imported))
        self.assertIsInstance(imported.report.outcomes[0],ImportCreated)
        imported_id=int(imported.report.outcomes[0].identity.id)
        h.detach();c.commit();c,h,a,t=self.consumer()
        reread=a.get_object_in_transaction(t,document_id='adoc',module_id='m',record_id='A',object_id=imported_id)
        self.assertIsInstance(reread.value,ObjectFound,repr(reread))
        self.assertEqual(dict(reread.value.object.values)['A-value'],actual)
        h.detach();c.rollback()


class RecursiveRebindTests(base.PublicCreateGroupTests):
    for _name in tuple(n for n in dir(base.PublicCreateGroupTests) if n.startswith('test_')):locals()[_name]=None
    source_version='0.10.0'
    def fields(self,source):
        source['umf']=self.source_version
        for element in source['modules'][0]['elements']:
            if element['kind']=='record':element['name']=element['id']
    def test_register_retained_nested_field_and_history(self):
        from truss import CatalogDocument,CatalogRegistration
        c,h,a,t=self.ready(self.fields)
        nested=MapValue(entries=(MapEntry(key='amounts',value=SequenceValue(items=(TextValue(kind='decimal',text='1.23000'),))),))
        operation=replace(self.create(),values=self.create().values+(AuthoredValue(name='giftData',value=nested),))
        context=a.group_context_in_transaction(t).value
        created=self.apply(a,t,context.input((operation,),MapValue(entries=())),context.request('retain-nested'))
        self.assertIsInstance(created,GroupSuccess);identity=created.response.semantic.results[0].identity
        h.detach();c.commit();self.admin.execute('GRANT '+self.installation.registrar_role+' TO consumer WITH SET FALSE')
        original=next(d for d in self.documents if d.document_id=='adoc');source=json.loads(original.content);module=source['modules'][0]
        module['elements'] += [
            {'id':'giftData','name':'giftData','kind':'field','cardinality':'map','nullability':'required','itemType':{'module':'m','element':'giftSequence'},'extensions':{}},
            {'id':'giftSequence','name':'giftSequence','kind':'field','cardinality':'array','nullability':'required','itemType':{'module':'m','element':'giftDecimal'},'extensions':{}},
            {'id':'giftDecimal','name':'giftDecimal','kind':'field','cardinality':'one','nullability':'required','scalarType':'decimal','facets':{'precision':18,'scale':4},'extensions':{}}]
        next(e for e in module['elements'] if e['id']=='A')['members'].append({'module':'m','element':'giftData'})
        c,h,a,t=self.consumer();document=CatalogDocument('adoc','r2',json.dumps(source).encode())
        prepared=a.prepare_catalog((document,),source_version=self.source_version,bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        accepted=a.accept_in_transaction(t,prepared,request_key='bind-nested',bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        self.assertIsInstance(accepted,Ok,repr(accepted)+' '+str(h._custody.last_attempt.error));self.assertIsInstance(accepted.value,CatalogRegistration)
        self.assertEqual(json.loads(accepted.value.report_bytes)['rebindProfile'],'truss-native-catalog-rebind/0.4')
        h.detach();c.commit();c,h,a,t=self.consumer()
        found=a.get_object_in_transaction(t,document_id='adoc',module_id='m',record_id='A',object_id=int(identity.id))
        self.assertIsInstance(found.value,ObjectFound,repr(found));self.assertEqual(found.value.object.version,2)
        self.assertEqual(dict(found.value.object.values)['giftData'],nested)
        self.assertNotIn('giftData',dict(found.value.object.retained))
        history=a.reconstruct_in_transaction(t,entity=HistoryEntity(kind='object',document_id='adoc',module_id='m',definition_id='A',id=int(identity.id)),version=2)
        self.assertIsInstance(history.value,HistoricalRecord,repr(history));self.assertIn('1.23000',history.value.record.decode())
        h.detach();c.rollback()
