# SPDX-License-Identifier: MIT OR Apache-2.0
"""Basic public composite typed keys using the original UMF tuple producers."""
import os
from truss import Ok,ObjectFound,ObjectNotFound
from truss.contracts import TextValue,BooleanValue,MapValue,NullValue
from truss.groups import CreateObject,RootlessOwnership,AuthoredValue,GroupSuccess,GroupFailed,RequestNone,UpdateObject,StoredObjectReference,KeyAbsent,CommittedReceiptReplay
from truss.imports import ImportReported,ImportCreated,ImportSkipped,ImportRejected
import test_group_create_native as groups

BUN=os.environ.get('TRUSS_BUN_EXECUTABLE','bun')

class TypedKeyTests(groups.PublicCreateGroupTests):
    for name in tuple(n for n in dir(groups.PublicCreateGroupTests) if n.startswith('test_')):locals()[name]=None
    source_version='0.7.0'

    def ready(self,*args,**kwargs):
        result=super().ready(*args,**kwargs)
        # Registration retains the broader owner preparation dependency;
        # Ordinary operations must not call any client key encoder.
        from unittest.mock import patch
        producer=patch('truss._umf_key_tuples._capture',side_effect=AssertionError('Key operation spawned Bun'))
        producer.start();self.addCleanup(producer.stop)
        for name in ('encode_key_tuples','encode_string_key_tuples','encode_literal_key_tuple'):
            encoder=patch('truss._umf_key_tuples.'+name,side_effect=AssertionError('Client key encoding'))
            encoder.start();self.addCleanup(encoder.stop)
        return result

    def fields(self,source):
        source['umf']=self.source_version;module=source['modules'][0];module['relationships']=[]
        record=next(e for e in module['elements'] if e['id']=='A')
        for element in module['elements']:
            if element['kind']=='record':element['name']=element['id']
        for name,family,facets in (('quantity','integer',{'integerWidth':{'bits':64,'signed':True}}),('amount','decimal',{'precision':18,'scale':4}),('flag','boolean',None),('blob','binary',None)):
            field={'id':name,'name':name,'kind':'field','scalarType':family,'nullability':'required','cardinality':'one','extensions':{}}
            if facets:field['facets']=facets
            module['elements'].append(field);record['members'].append({'module':'m','element':name})
        record['keys']=[{'id':'a-primary','name':'typed','primary':True,'fields':[{'module':'m','element':n} for n in ('A-label','quantity','amount','flag','blob')]}]

    def values(self,label='one',quantity='9007199254740993',amount='1.2300'):
        return self.create(label).values+(AuthoredValue(name='quantity',value=TextValue(kind='integer',text=quantity)),AuthoredValue(name='amount',value=TextValue(kind='decimal',text=amount)),AuthoredValue(name='flag',value=BooleanValue(value=True)),AuthoredValue(name='blob',value=TextValue(kind='binary',text='AP8=')))

    def key(self,label='one',quantity='9007199254740993',amount='1.23000'):
        return (label,TextValue(kind='integer',text=quantity),TextValue(kind='decimal',text=amount),BooleanValue(value=True),TextValue(kind='binary',text='AP8='))

    def lookup(self,a,t,**kwargs):
        result=a.lookup_key_in_transaction(t,document_id='adoc',module_id='m',record_id='A',key_id='a-primary',values=self.key(**kwargs),bun_executable=BUN)
        self.assertIsInstance(result,Ok,repr(result));return result.value

    def test_public_typed_composite_workflow(self):
        c,h,a,t=self.ready(self.fields)
        create=CreateObject(type_definition_pin=self.types[('adoc','A')].definition_pin,values=self.values(),ownership=RootlessOwnership())
        original,request=self.input(a,t,(create,));result=self.apply(a,t,original,request)
        self.assertIsInstance(result,GroupSuccess);identity=result.response.semantic.results[0].identity
        h.detach();c.commit();c,h,a,t=self.consumer()
        found=self.lookup(a,t);self.assertIsInstance(found,ObjectFound)
        self.assertEqual(dict(found.object.values)['amount'],TextValue(kind='decimal',text='1.2300'))
        duplicate=CreateObject(type_definition_pin=create.type_definition_pin,values=self.values(amount='1.23000'),ownership=RootlessOwnership())
        context=a.group_context_in_transaction(t).value
        self.assertIsInstance(a.apply_in_transaction(t,context.input((duplicate,),MapValue(entries=())),RequestNone(),documents=self.documents,bun_executable=BUN).value,GroupFailed)
        for name,value in (('quantity',NullValue()),('A-label',BooleanValue(value=True)),('amount',TextValue(kind='decimal',text='1.23001'))):
            invalid=CreateObject(type_definition_pin=create.type_definition_pin,values=tuple(AuthoredValue(name=v.name,value=value) if v.name==name else v for v in self.values('invalid')),ownership=RootlessOwnership())
            refused=a.apply_in_transaction(t,context.input((invalid,),MapValue(entries=())),RequestNone(),documents=self.documents,bun_executable=BUN)
            self.assertIsInstance(refused,Ok,repr(refused));self.assertIsInstance(refused.value,GroupFailed)

        condition=KeyAbsent(id='unused',reason='typed key is free',type_definition_pin=create.type_definition_pin,key_id='a-primary',values=tuple(v if not isinstance(v,str) else TextValue(kind='string',text=v) for v in self.key()))
        condition_input=context.input((CreateObject(type_definition_pin=create.type_definition_pin,values=self.values('other'),ownership=RootlessOwnership()),),MapValue(entries=()),preconditions=(condition,))
        self.assertIsInstance(a.apply_in_transaction(t,condition_input,RequestNone(),documents=self.documents,bun_executable=BUN).value,GroupFailed)
        from dataclasses import replace
        bad_condition=replace(condition,values=tuple(BooleanValue(value=True) if isinstance(v,str) else v for v in self.key()))
        invalid_condition=a.apply_in_transaction(t,context.input((duplicate,),MapValue(entries=()),preconditions=(bad_condition,)),RequestNone(),documents=self.documents,bun_executable=BUN)
        self.assertIsInstance(invalid_condition,Ok,repr(invalid_condition));self.assertIsInstance(invalid_condition.value,GroupFailed)

        update=UpdateObject(target=StoredObjectReference(identity=identity),set=(AuthoredValue(name='quantity',value=TextValue(kind='integer',text='9007199254740994')),),unset=(),expected_version='1')
        self.assertIsInstance(a.apply_in_transaction(t,context.input((update,),MapValue(entries=())),RequestNone(),documents=self.documents,bun_executable=BUN).value,GroupSuccess)
        self.assertIsInstance(self.lookup(a,t),ObjectNotFound);self.assertIsInstance(self.lookup(a,t,quantity='9007199254740994'),ObjectFound)
        self.assertIsInstance(a.apply_in_transaction(t,context.input((create,),MapValue(entries=())),RequestNone(),documents=self.documents,bun_executable=BUN).value,GroupFailed)
        reserved=a.object_import_record_in_transaction(t,document_id='adoc',module_id='m',record_id='A',values=self.values()).value
        load=a.import_context_in_transaction(t).value
        skipped=a.import_in_transaction(t,load.input((reserved,),load_id='reserved',asserted_origin=MapValue(entries=())),documents=self.documents,bun_executable=BUN)
        self.assertIsInstance(skipped,ImportReported);self.assertIsInstance(skipped.report.outcomes[0],ImportSkipped)
        built=a.object_import_record_in_transaction(t,document_id='adoc',module_id='m',record_id='A',values=self.values('imported'))
        self.assertIsInstance(built,Ok,repr(built));load=a.import_context_in_transaction(t).value
        # A raw caller cannot omit the required encoding profile to enter the
        # legacy compatibility branch (Astra's concrete regression finding).
        import json,psycopg
        from truss._group_runtime import _wire
        from truss.catalog_runtime import _release
        source=next(d.content for d in self.documents if d.document_id=='adoc')
        raw_identity=_wire(built.value.identity);del raw_identity['keyEncodingProfile'];manifest,digest,_=_release()
        c.execute('SAVEPOINT missing_key_profile')
        try:
            with self.assertRaises(psycopg.errors.InvalidParameterValue):
                c.execute('SELECT truss.import_object_identity(%s,%s,%s,%s,%s)',(json.dumps(raw_identity).encode(),source,None,manifest['releaseId'],digest))
        finally:
            c.execute('ROLLBACK TO SAVEPOINT missing_key_profile');c.execute('RELEASE SAVEPOINT missing_key_profile')
        invalid_record=a.object_import_record_in_transaction(t,document_id='adoc',module_id='m',record_id='A',values=self.values('badimport',amount='1.23001')).value
        rejected=a.import_in_transaction(t,load.input((invalid_record,),load_id='invalid',asserted_origin=MapValue(entries=())),documents=self.documents,bun_executable=BUN)
        self.assertIsInstance(rejected,ImportReported,repr(rejected));self.assertIsInstance(rejected.report.outcomes[0],ImportRejected)
        imported=a.import_in_transaction(t,load.input((built.value,),load_id='typed',asserted_origin=MapValue(entries=())),documents=self.documents,bun_executable=BUN)
        self.assertIsInstance(imported,ImportReported,repr(imported));self.assertIsInstance(imported.report.outcomes[0],ImportCreated,repr(imported))
        repeated=a.import_in_transaction(t,load.input((built.value,),load_id='typed',asserted_origin=MapValue(entries=())),documents=self.documents,bun_executable=BUN)
        self.assertIsInstance(repeated,ImportReported);self.assertIsInstance(repeated.report.outcomes[0],ImportSkipped)
        h.detach();c.commit();c,h,a,t=self.consumer()
        replay=self.apply(a,t,original,request);self.assertIsInstance(replay.response,CommittedReceiptReplay)
        self.assertEqual(replay.response.semantic,result.response.semantic)
        h.detach();c.rollback();c.execute('BEGIN READ ONLY')
        from truss import adopt_psycopg_host,create_reference_assembly,CatalogRuntimeConfiguration
        h=adopt_psycopg_host(c);self.addCleanup(h.detach);t=h.adopt_transaction(access_mode='read_only').value;a=create_reference_assembly(CatalogRuntimeConfiguration(),h).value
        self.assertIsInstance(self.lookup(a,t,quantity='9007199254740994'),ObjectFound)
        h.detach();c.rollback()

    def test_thousand_native_key_lookups_without_bun(self):
        c,h,a,t=self.ready(self.fields)
        create=CreateObject(type_definition_pin=self.types[('adoc','A')].definition_pin,values=self.values(),ownership=RootlessOwnership())
        original,request=self.input(a,t,(create,))
        self.assertIsInstance(self.apply(a,t,original,request),GroupSuccess)
        for _ in range(1000):self.assertIsInstance(self.lookup(a,t),ObjectFound)

class TypedKey08Tests(TypedKeyTests):
    source_version='0.8.0'
