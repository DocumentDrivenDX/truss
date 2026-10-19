# SPDX-License-Identifier: MIT OR Apache-2.0
"""Public exact mixed scalar values without float or timestamp projection."""
from dataclasses import replace
from truss import Ok,Error,ObjectFound,adopt_psycopg_host,create_reference_assembly,CatalogRuntimeConfiguration
from truss.contracts import TextValue,BooleanValue
from truss.groups import AuthoredValue,GroupSuccess,GroupFailed,CommittedReceiptReplay,RequestNone,InvalidGroupInput
import test_group_create_native as group_tests

class ExactScalarTests(group_tests.PublicCreateGroupTests):
    for _name in tuple(n for n in dir(group_tests.PublicCreateGroupTests) if n.startswith('test_')):
        locals()[_name]=None

    def source(self,document):
        module=document['modules'][0];record=next(e for e in module['elements'] if e['id']=='A')
        for name,family in (('n','integer'),('d','decimal'),('flag','boolean'),('at','timestamp'),('blob','binary')):
            identity='A-'+name
            module['elements'].append({'id':identity,'kind':'field','name':name,'scalarType':family,'cardinality':'one','nullability':'required','extensions':{}})
            record['members'].append({'module':'m','element':identity})

    def operation(self,**overrides):
        values={'n':TextValue(kind='integer',text='9'*2500),'d':TextValue(kind='decimal',text='-0.00012300e+999999999999999999999999999'),
                'flag':BooleanValue(value=True),'at':TextValue(kind='timestamp',text='2024-02-29t23:59:59.12345678901234567890-00:00'),
                'blob':TextValue(kind='binary',text='AP8='),'retained-number':TextValue(kind='decimal',text='1.2300')}
        values.update(overrides)
        operation=self.create()
        return replace(operation,values=operation.values+tuple(AuthoredValue(name=name,value=value) for name,value in values.items()))

    def test_create_commit_readonly_key_read_and_original_receipt(self):
        connection,host,assembly,tx=self.ready(self.source)
        operation=self.operation();input,request=self.input(assembly,tx,operations=(operation,))
        result=self.apply(assembly,tx,input,request);self.assertIsInstance(result,GroupSuccess)
        identity=int(result.response.semantic.results[0].identity.id)
        self.assertEqual(result.response.semantic.results[0].events[0].history_profile,'truss-native-owned-create/0.1')
        host.detach();connection.commit();connection,host,assembly,tx=self.consumer()
        replay=self.apply(assembly,tx,input,request)
        self.assertIsInstance(replay.response,CommittedReceiptReplay);self.assertEqual(replay.response.semantic,result.response.semantic)
        host.detach();connection.rollback();connection.execute('BEGIN READ ONLY')
        host=adopt_psycopg_host(connection);self.consumer_connections.append((connection,host))
        assembly=create_reference_assembly(CatalogRuntimeConfiguration(),host).value;tx=host.adopt_transaction(access_mode='read_only').value
        read=assembly.get_object_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',object_id=identity)
        self.assertIsInstance(read.value,ObjectFound)
        actual=dict(read.value.object.values)
        self.assertIs(type(actual['flag']),bool)
        for field in operation.values:
            if field.name=='retained-number':self.assertEqual(dict(read.value.object.retained)[field.name],field.value)
            elif field.name not in ('A-label','A-value'):
                self.assertEqual(actual[field.name],True if field.name=='flag' else field.value)
        key=assembly.lookup_key_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',key_id='a-primary',values=('value','one'),bun_executable='/opt/homebrew/bin/bun')
        self.assertIsInstance(key.value,ObjectFound);self.assertEqual(key.value.object,read.value.object)
        host.detach();connection.rollback()

    def test_invalid_tokens_family_mismatch_and_caller_rollback_have_no_effects(self):
        connection,host,assembly,tx=self.ready(self.source)
        connection.execute("CREATE TEMP TABLE scalar_prior(value text);INSERT INTO scalar_prior VALUES('kept')")
        for name,value in (('n',TextValue(kind='integer',text='00')),('n',TextValue(kind='integer',text='1\n')),('d',TextValue(kind='decimal',text='NaN')),
            ('flag',TextValue(kind='integer',text='1')),('at',TextValue(kind='timestamp',text='2023-02-29T00:00:00Z')),
            ('at',TextValue(kind='timestamp',text='2024-01-01T00:00:60Z')),('blob',TextValue(kind='binary',text='AB=='))):
            input,_=self.input(assembly,tx,operations=(self.operation(**{name:value}),))
            refused=assembly.apply_in_transaction(tx,input,RequestNone(),documents=self.documents,bun_executable='/opt/homebrew/bin/bun')
            self.assertIsInstance(refused,Ok);self.assertIsInstance(refused.value,GroupFailed)
            self.assertIsInstance(refused.value.failure,InvalidGroupInput)
            import base64,json
            self.assertEqual(json.loads(base64.b64decode(refused.value.failure.diagnostic.bytes_base64)),
                {'code':'invalid_input','nativeState':'22023','operationIndex':'0','outcome':'failed'})
        self.assertEqual(connection.execute('SELECT count(*) FROM scalar_prior').fetchone(),(1,))
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(0,))
        input,_=self.input(assembly,tx,operations=(self.operation(blob=TextValue(kind='binary',text='')),))
        applied=assembly.apply_in_transaction(tx,input,RequestNone(),documents=self.documents,bun_executable='/opt/homebrew/bin/bun')
        self.assertIsInstance(applied.value,GroupSuccess)
        host.detach();connection.rollback()
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(0,))
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.journal').fetchone(),(0,))

    def test_first_invocation_with_nonstandard_string_literals_refuses_bad_separators(self):
        connection,host,assembly,tx=self.ready(self.source)
        connection.execute('SET LOCAL standard_conforming_strings=off')
        for name,value in (('d',TextValue(kind='decimal',text='1x2')),
                           ('at',TextValue(kind='timestamp',text='2024-01-01T00:00:00x123Z'))):
            input,_=self.input(assembly,tx,operations=(self.operation(**{name:value}),))
            refused=assembly.apply_in_transaction(tx,input,RequestNone(),documents=self.documents,bun_executable='/opt/homebrew/bin/bun')
            self.assertIsInstance(refused,Ok);self.assertIsInstance(refused.value,GroupFailed)
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(0,))
        host.detach();connection.rollback()
