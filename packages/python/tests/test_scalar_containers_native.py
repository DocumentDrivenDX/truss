# SPDX-License-Identifier: MIT OR Apache-2.0
"""Basic public scalar array/map workflows using original UMF item Fields."""
import json,os
from decimal import Decimal
from truss import (Ok,ObjectFound,ObjectNotFound,ModuleAccessGrant,HistoryEntity,HistoricalRecord,
    CatalogRuntimeConfiguration,adopt_psycopg_host,create_reference_assembly,QueryRefused,QueryRows,QueryAbsent)
from truss.contracts import TextValue,NullValue,SequenceValue,MapValue,MapEntry
from truss.groups import (AuthoredValue,CreateObject,RootlessOwnership,UpdateObject,StoredObjectReference,
    PropertyEquals,GroupSuccess,GroupFailed,Unchanged,CommittedReceiptReplay,UnauthorizedPerson)
from truss.imports import ImportReported,ImportCreated
import test_group_create_native as create_tests

class ScalarContainerTests(create_tests.PublicCreateGroupTests):
    for _name in tuple(n for n in dir(create_tests.PublicCreateGroupTests) if n.startswith('test_')):
        locals()[_name]=None
    source_version='0.7.0'
    def fields(self,source):
        source['umf']=self.source_version;module=source['modules'][0]
        for e in module['elements']:
            if e['kind']=='record':e['name']=e['id']
        record=next(e for e in module['elements'] if e['id']=='A');items=[]
        for name,cardinality,family,facets in (('tags','array','string',{}),('amounts','map','decimal',{'precision':18,'scale':4}),('quantities','array','integer',{'integerWidth':{'bits':64,'signed':True}})):
            module['elements'].append({'id':name,'name':name,'kind':'field','cardinality':cardinality,'nullability':'absent-allowed','itemType':{'module':'items','element':name+'-item'},'extensions':{}})
            record['members'].append({'module':'m','element':name})
            items.append({'id':name+'-item','name':name+'-item','kind':'field','cardinality':'one','nullability':'required','scalarType':family,'facets':facets,'extensions':{}})
        source['modules'].append({'id':'items','namespace':'items','extensions':{},'elements':items,'relationships':[]})
    def ready_containers(self):
        connection,host,assembly,tx=self.ready(self.fields);host.detach();connection.rollback()
        self.admin.execute('BEGIN');admin_host=adopt_psycopg_host(self.admin)
        admin_assembly=create_reference_assembly(CatalogRuntimeConfiguration(),admin_host).value;admin_tx=admin_host.adopt_transaction().value
        self.assertIsInstance(admin_assembly.configure_module_access_in_transaction(admin_tx,(ModuleAccessGrant('adoc','items','group_reader','group_writer'),)),Ok)
        admin_host.detach();self.admin.commit();return self.consumer()
    def amounts(self,reverse=False):
        entries=(MapEntry(key='a',value=TextValue(kind='decimal',text='1.23000')),MapEntry(key='b',value=TextValue(kind='decimal',text='0.0000')))
        return MapValue(entries=entries[::-1] if reverse else entries)
    def values(self,label='one'):
        return self.create(label=label,value=label).values+(AuthoredValue(name='tags',value=SequenceValue(items=(TextValue(kind='string',text='x'),TextValue(kind='string',text='x')))),AuthoredValue(name='amounts',value=self.amounts(True)),AuthoredValue(name='quantities',value=SequenceValue(items=(TextValue(kind='integer',text='9007199254740993'),))))
    def run_group(self,assembly,tx,operations,key,conditions=()):
        context=assembly.group_context_in_transaction(tx).value
        semantic=context.input(operations,MapValue(entries=()),preconditions=conditions)
        request=context.request(key);return self.apply(assembly,tx,semantic,request),semantic,request
    def test_public_accept_write_read_import_history_and_map_equality(self):
        connection,host,assembly,tx=self.ready_containers()
        operation=CreateObject(type_definition_pin=self.types[('adoc','A')].definition_pin,values=self.values(),ownership=RootlessOwnership(),alias='item')
        created,semantic,request=self.run_group(assembly,tx,(operation,),'containers');self.assertIsInstance(created,GroupSuccess);identity=created.response.semantic.results[0].identity
        no_op,_,_=self.run_group(assembly,tx,(UpdateObject(target=StoredObjectReference(identity=identity),set=(AuthoredValue(name='amounts',value=self.amounts()),),unset=(),expected_version='1'),),'same-map',(PropertyEquals(id='same',reason='mapping equality',target=identity,name='amounts',value=self.amounts(True)),))
        self.assertIsInstance(no_op,GroupSuccess);self.assertIsInstance(no_op.response.semantic.results[0],Unchanged)
        for bad in (MapValue(entries=(MapEntry(key='a',value=TextValue(kind='decimal',text='1.23001')),)),MapValue(entries=(MapEntry(key='a',value=TextValue(kind='decimal',text='1')),MapEntry(key='a',value=TextValue(kind='decimal',text='2'))))):
            failed,_,_=self.run_group(assembly,tx,(UpdateObject(target=StoredObjectReference(identity=identity),set=(AuthoredValue(name='amounts',value=bad),),unset=()),),'bad-'+str(len(bad.entries)))
            self.assertIsInstance(failed,GroupFailed)
        built=assembly.object_import_record_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',values=self.values('imported'));self.assertIsInstance(built,Ok)
        context=assembly.import_context_in_transaction(tx).value
        imported=assembly.import_in_transaction(tx,context.input((built.value,),load_id='containers',asserted_origin=MapValue(entries=())),documents=self.documents,bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        self.assertIsInstance(imported,ImportReported);self.assertIsInstance(imported.report.outcomes[0],ImportCreated)
        host.detach();connection.commit();connection,host,assembly,tx=self.consumer()
        self.assertIsInstance(self.apply(assembly,tx,semantic,request).response,CommittedReceiptReplay)
        found=assembly.get_object_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',object_id=int(identity.id)).value;self.assertIsInstance(found,ObjectFound)
        self.assertEqual(dict(found.object.values)['amounts'],self.amounts());self.assertEqual(dict(found.object.values)['tags'],operation.values[-3].value);self.assertEqual(dict(found.object.values)['quantities'],operation.values[-1].value)
        historical=assembly.reconstruct_in_transaction(tx,entity=HistoryEntity(kind='object',document_id='adoc',module_id='m',definition_id='A',id=int(identity.id)),version=1).value
        self.assertIsInstance(historical,HistoricalRecord);self.assertIn('1.23000',historical.record.decode())
        host.detach();connection.rollback();connection,host,assembly,tx=self.consumer()
        host.detach();connection.execute('SET TRANSACTION READ ONLY')
        host=adopt_psycopg_host(connection);self.addCleanup(host.detach)
        assembly=create_reference_assembly(CatalogRuntimeConfiguration(),host).value;tx=host.adopt_transaction(access_mode='read_only').value
        readonly=assembly.get_object_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',object_id=int(identity.id))
        self.assertIsInstance(readonly.value,ObjectFound);self.assertEqual(dict(readonly.value.object.values)['amounts'],self.amounts())
        query=assembly.query_in_transaction(tx,sql='SELECT a.tags, a.amounts, a.quantities FROM "A" a WHERE a."A-label" = :label',document_ids=('adoc',),parameters={'label':'one'})
        self.assertIsInstance(query,Ok);self.assertIsInstance(query.value,QueryRows,repr(query.value))
        self.assertEqual(query.value.rows,((('x','x'),{'a':Decimal('1.23000'),'b':Decimal('0.0000')},(9007199254740993,)),))
        self.assertEqual(str(query.value.rows[0][1]['a']),'1.23000')
        complete=assembly.query_in_transaction(tx,sql='SELECT a.* FROM "A" a WHERE a."A-label" = :label',document_ids=('adoc',),parameters={'label':'one'})
        self.assertIsInstance(complete.value,QueryRows,repr(complete.value))
        entity=dict(zip(complete.value.columns,complete.value.rows[0],strict=True));self.assertEqual(entity['tags'],('x','x'));self.assertEqual(entity['amounts'],query.value.rows[0][1])
        def projected():
            result=assembly.query_in_transaction(tx,sql='SELECT a.tags, a.amounts FROM "A" a WHERE a."A-label" = :label',document_ids=('adoc',),parameters={'label':'one'})
            self.assertIsInstance(result.value,QueryRows,repr(result.value));return result.value.rows[0]
        host.detach();connection.rollback();connection,host,assembly,tx=self.consumer()
        nulls,_,_=self.run_group(assembly,tx,(UpdateObject(target=StoredObjectReference(identity=identity),set=(AuthoredValue(name='tags',value=NullValue()),),unset=()),),'null-container');self.assertIsInstance(nulls,GroupSuccess)
        self.assertIsNone(dict(assembly.get_object_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',object_id=int(identity.id)).value.object.values)['tags'])
        self.assertIsNone(projected()[0])
        empty,_,_=self.run_group(assembly,tx,(UpdateObject(target=StoredObjectReference(identity=identity),set=(AuthoredValue(name='tags',value=SequenceValue(items=())),AuthoredValue(name='amounts',value=MapValue(entries=()))),unset=()),),'empty-containers');self.assertIsInstance(empty,GroupSuccess)
        values=dict(assembly.get_object_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',object_id=int(identity.id)).value.object.values);self.assertEqual(values['tags'],SequenceValue(items=()));self.assertEqual(values['amounts'],MapValue(entries=()))
        self.assertEqual(projected(),((),{}))
        absent,_,_=self.run_group(assembly,tx,(UpdateObject(target=StoredObjectReference(identity=identity),set=(),unset=('tags',)),),'absent-container');self.assertIsInstance(absent,GroupSuccess)
        self.assertNotIn('tags',dict(assembly.get_object_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',object_id=int(identity.id)).value.object.values))
        self.assertIsInstance(projected()[0],QueryAbsent)
        host.detach();connection.rollback()
        connection,host,assembly,tx=self.consumer()
        self.assertEqual(dict(assembly.get_object_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',object_id=int(identity.id)).value.object.values)['tags'],operation.values[-3].value)
        host.detach();connection.rollback()
        self.admin.execute("DELETE FROM truss.module_access WHERE document_id='adoc' AND module='items'")
        connection,host,assembly,tx=self.consumer()
        self.assertIsInstance(assembly.get_object_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',object_id=int(identity.id)).value,ObjectNotFound)
        refused,_,_=self.run_group(assembly,tx,(UpdateObject(target=StoredObjectReference(identity=identity),set=(),unset=()),),'no-item-authority');self.assertIsInstance(refused,GroupFailed);self.assertIsInstance(refused.failure,UnauthorizedPerson)

class ScalarContainer08Tests(ScalarContainerTests):
    source_version='0.8.0'
