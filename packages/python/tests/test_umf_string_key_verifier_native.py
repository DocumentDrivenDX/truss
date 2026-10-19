# SPDX-License-Identifier: MIT OR Apache-2.0
"""Native parity/forgery controls; this private verifier enables no mutation API."""
from pathlib import Path
import unittest
import psycopg
import test_catalog_runtime_native as catalog_tests
import test_umf_key_tuples as key_tests
from truss._umf_key_tuples import KeyTupleRequest


class NativeUmfStringKeyVerifierTests(catalog_tests.PublicCatalogRuntimeTests):
    # Reuse the owned local runtime fixture, not the public catalog test methods.
    def setUp(self):
        super().setUp()
        self.admin.execute('CREATE SCHEMA truss')
        source=Path(__file__).resolve().parents[3]/'packages/postgresql/native/verify-umf-string-key-tuple.sql'
        self.admin.execute(source.read_text())

    def matches(self,encoded,values):
        return self.admin.execute('SELECT truss.verify_umf_string_key_tuple(%s,%s::text[])',(encoded,values)).fetchone()[0]

    def test_owner_bytes_match_actual_ordered_native_values(self):
        producer=key_tests.OriginalUmfKeyTupleTests()
        vectors=(('ab','c'),('a','bc'),('','é'),('','e\u0301'),('x'*128,''),('😀','z'))
        requests=tuple(KeyTupleRequest('m','A','a-primary',values) for values in vectors)
        for receipt in producer.encode(requests):
            with self.subTest(values=receipt.request.values):
                self.assertTrue(self.matches(receipt.tuple_bytes,list(receipt.request.values)))
                self.assertFalse(self.matches(receipt.tuple_bytes,list(reversed(receipt.request.values))))

    def test_rejects_nonminimal_overflow_wrong_tag_and_forged_payload(self):
        good=bytes.fromhex('554d464b3101040178')
        self.assertTrue(self.matches(good,['x']))
        invalid=(good+b'\0',good[:-1],b'bad'+good,
            bytes.fromhex('554d464b318100040178'),bytes.fromhex('554d464b310104810078'),
            bytes.fromhex('554d464b3101020178'),bytes.fromhex('554d464b3101040179'),
            bytes.fromhex('554d464b31808080808080808080'),bytes.fromhex('554d464b310104ffffff7f'))
        for value in invalid:
            with self.subTest(encoded=value.hex()):self.assertFalse(self.matches(value,['x']))
        for values in (None,[],[None],['x','y']):self.assertFalse(self.matches(good,values))
        self.assertFalse(self.matches(None,['x']))
        self.assertFalse(self.admin.execute("SELECT truss.verify_umf_string_key_tuple(%s,'[0:0]={x}'::text[])",(good,)).fetchone()[0])
        self.assertFalse(self.matches(good,[['x']]))
        self.assertFalse(self.matches(b'x'*1048577,['x']))
        self.assertFalse(self.matches(good,['x'*1048577]))
        self.admin.execute('GRANT USAGE ON SCHEMA truss TO consumer')
        self.admin.execute('SAVEPOINT ordinary')
        self.admin.execute('SET LOCAL SESSION AUTHORIZATION consumer')
        with self.assertRaises(psycopg.errors.InsufficientPrivilege) as caught:
            self.admin.execute('SELECT truss.verify_umf_string_key_tuple(%s,%s::text[])',(good,['x']))
        self.assertEqual(caught.exception.sqlstate,'42501')
        self.admin.execute('ROLLBACK TO ordinary');self.admin.execute('RELEASE ordinary')

    def test_multibyte_component_count_and_payload_length_match_owner(self):
        import json
        from truss._umf_key_tuples import encode_string_key_tuples
        fields=[{'id':f'f{i}','name':f'f{i}','kind':'field','scalarType':'string',
            'nullability':'required','cardinality':'one','extensions':{}} for i in range(128)]
        refs=[{'module':'m','element':field['id']} for field in fields]
        source={'umf':'0.10.0','id':'wide-key','vocabularies':{},'extensions':{},'modules':[
            {'id':'m','namespace':'m','extensions':{},'elements':[
                {'id':'R','kind':'record','members':refs,'keys':[{'id':'wide','name':'wide','fields':refs}],'extensions':{}},*fields]}]}
        values=('x'*16384,*('' for _ in range(127)))
        request=KeyTupleRequest('m','R','wide',values)
        receipt=encode_string_key_tuples(json.dumps(source).encode(),(request,),bun_executable='/opt/homebrew/bin/bun')[0]
        self.assertTrue(self.matches(receipt.tuple_bytes,list(values)))

    def test_inclusive_component_limit_matches_owner(self):
        import json
        from truss._umf_key_tuples import encode_string_key_tuples
        for count in (1024,1025):
            fields=[{'id':f'f{i}','name':f'f{i}','kind':'field','scalarType':'string',
                'nullability':'required','cardinality':'one','extensions':{}} for i in range(count)]
            refs=[{'module':'m','element':field['id']} for field in fields]
            source={'umf':'0.10.0','id':'limit-key','vocabularies':{},'extensions':{},'modules':[
                {'id':'m','namespace':'m','extensions':{},'elements':[
                    {'id':'R','kind':'record','members':refs,'keys':[{'id':'limit','name':'limit','fields':refs}],'extensions':{}},*fields]}]}
            values=('',)*count;request=KeyTupleRequest('m','R','limit',values)
            receipt=encode_string_key_tuples(json.dumps(source).encode(),(request,),bun_executable='/opt/homebrew/bin/bun')[0]
            with self.subTest(count=count):self.assertEqual(self.matches(receipt.tuple_bytes,list(values)),count==1024)

    def test_exact_tuple_byte_limit_with_direct_original_owner(self):
        import json
        from importlib.resources import files
        from truss.preparation import _capture
        # Direct owner invocation qualifies the native bound, without widening
        # the Python helper's smaller JSON transport ceiling.
        source=key_tests.OriginalUmfKeyTupleTests().source().decode()
        module=str(files('truss').joinpath('_umf_keys','producer.js'))
        script='const o=await import('+json.dumps(module)+');const r=JSON.parse(await Bun.stdin.text());process.stdout.write(o.encodeCoreKeyTuple(o.readJsonValue(r.sourceText,"json"),r.identity,r.values).bytesHex);'
        for total in (1048576,1048577):
            value='x'*(total-10)
            payload=json.dumps({'sourceText':source,'identity':{'module':'m','element':'A','key':'z-alt'},'values':[{'string':value}]}).encode()
            result=_capture(['/opt/homebrew/bin/bun','--eval',script],input_bytes=payload,limit=3145728,timeout=10)
            self.assertEqual(result.returncode,0)
            original=bytes.fromhex(result.stdout.decode())
            self.assertEqual(len(original),total)
            with self.subTest(bytes=total):self.assertEqual(self.matches(original,[value]),total==1048576)


# Parent test cases are deliberately not inherited as tests for this private body.
for _name in tuple(vars(catalog_tests.PublicCatalogRuntimeTests)):
    if _name.startswith('test_'):setattr(NativeUmfStringKeyVerifierTests,_name,None)

if __name__=='__main__':unittest.main()
