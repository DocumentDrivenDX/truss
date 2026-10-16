"""Database derivation matches UMF and preserves source constraints without clients."""
import base64
from dataclasses import replace
import json
import os
from pathlib import Path
from unittest.mock import patch
import psycopg
from truss import Ok,Error,ObjectFound,ObjectReadInvalid
from truss.contracts import TextValue,BooleanValue,MapValue
from truss.groups import CreateObject,RootlessOwnership,AuthoredValue,GroupSuccess,GroupFailed,RequestNone
from truss._umf_key_tuples import KeyTupleRequest,encode_key_tuples
from test_umf_literal_key_tuples import key_source
import test_typed_keys_native as typed


class DatabaseKeyDerivationTests(typed.TypedKeyTests):
    for name in tuple(n for n in dir(typed.TypedKeyTests) if n.startswith('test_')):locals()[name]=None
    source_version='0.8.0'

    def test_cross_document_key_predicate_requires_exact_source(self):
        from truss import ModuleAccessGrant,adopt_psycopg_host,create_reference_assembly,CatalogRuntimeConfiguration
        from truss.groups import KeyAbsent
        c,h,a,t=self.ready(self.fields)
        self.admin.execute('BEGIN')
        ah=adopt_psycopg_host(self.admin);at=ah.adopt_transaction().value
        aa=create_reference_assembly(CatalogRuntimeConfiguration(),ah).value
        self.assertIsInstance(aa.configure_module_access_in_transaction(at,(ModuleAccessGrant('zdoc','m','group_reader','group_writer'),)),Ok)
        ah.detach();self.admin.commit()
        context=a.group_context_in_transaction(t).value
        create=CreateObject(type_definition_pin=self.types[('adoc','A')].definition_pin,values=self.values(),ownership=RootlessOwnership())
        condition=KeyAbsent(id='other-document',reason='free',type_definition_pin=self.types[('zdoc','A')].definition_pin,key_id='a-primary',values=(TextValue(kind='string',text='one'),)+self.key()[1:])
        original=context.input((create,),MapValue(entries=()),preconditions=(condition,))
        for documents in (tuple(d for d in self.documents if d.document_id!='zdoc'),
                          tuple(replace(d,content=d.content+b' ') if d.document_id=='zdoc' else d for d in self.documents)):
            refused=a.apply_in_transaction(t,original,RequestNone(),documents=documents,bun_executable='/missing/bun')
            self.assertTrue(isinstance(refused,Error) or isinstance(refused.value,GroupFailed),repr(refused))
            self.assertEqual(c.execute('SELECT 42').fetchone(),(42,))
        accepted=a.apply_in_transaction(t,original,RequestNone(),documents=self.documents,bun_executable='/missing/bun')
        self.assertIsInstance(accepted.value,GroupSuccess,repr(accepted)+' '+str(h._custody.last_attempt.error))
        h.detach();c.rollback()

    def test_native_scalar_vectors_match_original_producers(self):
        self.install()
        corpus=json.loads((Path(__file__).parent/'fixtures/umf-literal-key-vectors.json').read_bytes())
        for core in ('0.7.0','0.8.0'):
            for vector in corpus['vectors']:
                fields=[{**f,**({'precision':18} if f['scalarType']=='decimal' else {})} for f in vector['fields']]
                source=json.loads(key_source(fields));source['umf']=core
                cells=[];facets=[];values=[]
                for f,literal in zip(fields,vector['values']):
                    kind=f['scalarType'];value=next(iter(literal.values()))
                    if kind=='boolean':cell={'kind':kind,'value':value};wrapped=BooleanValue(value=value)
                    elif kind=='binary':
                        value=base64.b64encode(bytes.fromhex(value)).decode();cell={'kind':kind,'text':value};wrapped=TextValue(kind=kind,text=value)
                    else:cell={'kind':kind,'text':value};wrapped=TextValue(kind=kind,text=value)
                    cells.append(cell);values.append(wrapped);facets.append({'precision':18,'scale':f['scale']} if kind=='decimal' else {})
                oracle=encode_key_tuples(json.dumps(source).encode(),(KeyTupleRequest('m','Staff','pk',tuple(values)),),bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))[0]
                actual=self.admin.execute('SELECT truss.encode_umf_scalar_key_tuple(%s::jsonb,%s::jsonb)',(json.dumps(cells),json.dumps(facets))).fetchone()[0]
                self.assertEqual(bytes(actual),oracle.tuple_bytes,(core,vector['id']))
                self.assertEqual(bytes(actual).hex(),vector['expectedHex'])
        # Multi-byte count and payload framing, exact Unicode sequence and empty binary.
        for cells in ([{'kind':'boolean','value':False}]*128,[{'kind':'string','text':'雪'*128},{'kind':'binary','text':''}]):
            facets=[{}]*len(cells)
            frame=bytes(self.admin.execute('SELECT truss.encode_umf_scalar_key_tuple(%s::jsonb,%s::jsonb)',(json.dumps(cells),json.dumps(facets))).fetchone()[0])
            self.assertTrue(self.admin.execute('SELECT truss.verify_umf_scalar_key_tuple(%s,%s::jsonb,%s::jsonb)',(frame,json.dumps(cells),json.dumps(facets))).fetchone()[0])
            self.assertFalse(self.admin.execute('SELECT truss.verify_umf_scalar_key_tuple(%s,%s::jsonb,%s::jsonb)',(frame+b'\0',json.dumps(cells),json.dumps(facets))).fetchone()[0])
        self.assertEqual(self.admin.execute("SELECT encode(truss.umf_key_uleb128(128),'hex')").fetchone()[0],'8001')

    def test_allowed_values_defaults_and_no_weft_or_client_encoder(self):
        def constrained(source):
            self.fields(source)
            allowed={'A-label':[{'string':'one'}],'quantity':[{'integerToken':'9007199254740993e0'}],
                     'amount':[{'decimalToken':'1.23000'}],'flag':[{'boolean':False}], 'blob':[{'binaryHex':'00FF'}]}
            for field in source['modules'][0]['elements']:
                if field['id'] in allowed:field['allowedValues']=allowed[field['id']]
                if field['id']=='quantity':field['default']={'on':'missing','value':{'integerToken':'9007199254740993'}}
        c,h,a,t=self.ready(constrained)
        context=a.group_context_in_transaction(t).value
        values=tuple(replace(v,value=BooleanValue(value=False)) if v.name=='flag' else v for v in self.values())
        create=CreateObject(type_definition_pin=self.types[('adoc','A')].definition_pin,values=values,ownership=RootlessOwnership())
        with patch.dict('sys.modules',{'weft':None}):
            applied=a.apply_in_transaction(t,context.input((create,),MapValue(entries=())),RequestNone(),documents=self.documents,bun_executable='/missing/bun')
            self.assertIsInstance(applied.value,GroupSuccess,repr(applied)+' '+str(h._custody.last_attempt.error))
            key=list(self.key());key[3]=BooleanValue(value=False)
            found=a.lookup_key_in_transaction(t,document_id='adoc',module_id='m',record_id='A',key_id='a-primary',values=tuple(key),bun_executable='/missing/bun')
            self.assertIsInstance(found.value,ObjectFound,repr(found))
            for name,value in [('A-label',TextValue(kind='string',text='other')),('quantity',TextValue(kind='integer',text='2')),('amount',TextValue(kind='decimal',text='1.24')),('flag',BooleanValue(value=True)),('blob',TextValue(kind='binary',text='AAE='))]:
                bad=replace(create,values=tuple(replace(v,value=value) if v.name==name else v for v in values))
                refused=a.apply_in_transaction(t,context.input((bad,),MapValue(entries=())),RequestNone(),documents=self.documents)
                self.assertIsInstance(refused.value,GroupFailed,(name,refused))
            missing=replace(create,values=tuple(v for v in values if v.name!='quantity'))
            self.assertIsInstance(a.apply_in_transaction(t,context.input((missing,),MapValue(entries=())),RequestNone(),documents=self.documents).value,GroupFailed)
        h.detach();c.commit()
        contexts=self.admin.execute("SELECT convert_from(original_context_bytes,'UTF8')::jsonb FROM truss.object_key_bucket").fetchall()
        self.assertTrue(contexts)
        for (context,) in contexts:
            self.assertEqual(context['profile'],'truss-created-key-context/0.2')
            self.assertNotIn('ownerReceiptBase64',context)

    def test_native_refusals_and_helpers_are_owner_only(self):
        self.install()
        invalid=[([{'kind':'integer','text':'01'}],[{}]),([{'kind':'null'}],[{}]),
                 ([{'kind':'decimal','text':'1.201'}],[{'precision':18,'scale':2}]),
                 ([{'kind':'decimal','text':'1.2'}],[{'precision':2,'scale':3}])]
        for cells,facets in invalid:
            with self.assertRaises(psycopg.Error):
                self.admin.execute('SELECT truss.encode_umf_scalar_key_tuple(%s::jsonb,%s::jsonb)',(json.dumps(cells),json.dumps(facets)))
        encoded=self.admin.execute('SELECT truss.encode_umf_scalar_key_tuple(%s::jsonb,%s::jsonb)',
            (json.dumps([{'kind':'decimal','text':'1.2'}]),json.dumps([{'precision':5,'scale':2}]))).fetchone()[0]
        self.assertTrue(bytes(encoded))
        self.assertFalse(self.admin.execute("SELECT has_function_privilege('consumer','truss.encode_umf_scalar_key_tuple(jsonb,jsonb)','EXECUTE')").fetchone()[0])
