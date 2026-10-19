# SPDX-License-Identifier: MIT OR Apache-2.0
"""Original semantic key producer across admitted families; no database authority.
@covers US-056-AC2
@covers US-056-AC10
"""
import json,unittest
from pathlib import Path
from truss._umf_key_tuples import encode_literal_key_tuple

FIXTURE=Path(__file__).parent/'fixtures'
def key_source(fields):
 members=[{'module':'m','element':f['id']} for f in fields]
 source={'umf':'0.10.0','id':'truss-literal-key-vector','vocabularies':{},'modules':[{'id':'m','namespace':'','elements':[
  {'id':'Staff','kind':'record','name':'Staff','members':members,'keys':[{'id':'pk','name':'Key','fields':members}],'extensions':{}},
  *[{'id':f['id'],'kind':'field','name':f['id'],'scalarType':f['scalarType'],'cardinality':'one','nullability':'required','extensions':{},
     **({'facets':{'precision':f['precision'],'scale':f['scale']}} if 'precision'in f else {})} for f in fields]]}]}
 return json.dumps(source,separators=(',',':')).encode()

class LiteralKeyTests(unittest.TestCase):
 def encode(self,source,values,identity=('m','Staff','pk')):
  return encode_literal_key_tuple(source,identity,tuple(json.dumps(v) for v in values),bun_executable='/opt/homebrew/bin/bun')
 def test_original_independent_byte_vectors_and_refusals(self):
  corpus=json.loads((FIXTURE/'umf-literal-key-vectors.json').read_bytes())
  for vector in corpus['vectors']:
   with self.subTest(vector=vector['id']):
    output=self.encode(key_source(vector['fields']),vector['values'])
    self.assertEqual(output.tuple_bytes.hex(),vector['expectedHex'])
    receipt=json.loads(output.original_receipt_bytes)
    self.assertEqual(receipt['operation'],'truss-encode-key-tuple')
    self.assertEqual(receipt['version'],'1.0.0')
    self.assertEqual(receipt['profile'],'umf-key-tuple-v1')
  for vector in corpus['refusals']:
   with self.subTest(vector=vector['id']),self.assertRaises(ValueError):self.encode(key_source(vector['fields']),vector['values'])
 def test_five_admitted_families_exact_large_values_and_leading_binary_zero(self):
  kinds=['string','boolean','integer','decimal','binary']
  source=key_source([{'id':'k'+str(i),'scalarType':kind,**({'precision':30,'scale':4} if kind=='decimal'else{})}for i,kind in enumerate(kinds)])
  values=[{'string':'Δ\uFEFF'},{'boolean':True},{'integerToken':'9007199254740993'},{'decimalToken':'9007199254740993.0000'},{'binaryHex':'0001'}]
  result=self.encode(source,values);receipt=json.loads(result.original_receipt_bytes)
  self.assertEqual(result.original_document,source)
  self.assertEqual(result.literal_texts,tuple(json.dumps(v)for v in values))
  self.assertEqual(receipt['values'],values)
  for i,v in [(0,{'string':'Δ'}),(1,{'boolean':False}),(2,{'integerToken':'9007199254740992'}),(3,{'decimalToken':'9007199254740992.0000'}),(4,{'binaryHex':'01'})]:
   changed=values.copy();changed[i]=v;self.assertNotEqual(self.encode(source,changed).tuple_bytes,result.tuple_bytes)
  with self.assertRaises(ValueError):self.encode(source,list(reversed(values)))
 def test_owner_arity_domain_facet_and_unknown_key_refusals(self):
  source=key_source([{'id':'n','scalarType':'integer'}])
  for values in [[],[{'integerToken':'1'},{'integerToken':'2'}],[{'string':'1'}],[{'integerToken':'01'}],[{'null':True}],[{'absent':True}]]:
   with self.subTest(values=values),self.assertRaises(ValueError):self.encode(source,values)
  with self.assertRaises(ValueError):self.encode(source,[{'integerToken':'1'}],('m','Staff','foreign'))
  decimal=key_source([{'id':'d','scalarType':'decimal','precision':5,'scale':2}])
  for token in ['1.201','1000.00']:
   with self.assertRaises(ValueError):self.encode(decimal,[{'decimalToken':token}])
 def test_raw_literal_text_retained_owner_parses_and_invalid_unicode_refuses(self):
  source=key_source([{'id':'s','scalarType':'string'}])
  text=' { "string" : "\\u0394" } '
  output=encode_literal_key_tuple(source,('m','Staff','pk'),(text,),bun_executable='/opt/homebrew/bin/bun')
  self.assertEqual(output.literal_texts,(text,));self.assertEqual(json.loads(output.original_receipt_bytes)['values'],[{'string':'Δ'}])
  for text in ['{','{"string":"\\uD800"}',chr(0xd800),'x'*65537]:
   with self.assertRaises(ValueError):encode_literal_key_tuple(source,('m','Staff','pk'),(text,),bun_executable='/opt/homebrew/bin/bun')
