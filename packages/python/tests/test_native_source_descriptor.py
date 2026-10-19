# SPDX-License-Identifier: MIT OR Apache-2.0
"""Independently authored supplied data; no native observation or authority."""
import unittest,json,copy
from hashlib import sha256
from truss._native_source_descriptor import prepare_native_source_descriptor

def wire(value):return json.dumps(value,separators=(',',':')).encode()

class NativeSourceDescriptorTests(unittest.TestCase):
 def setUp(self):
  self.document='{"id":"d","umf":"0.10.0","modules":[],"opaque":1.2300e-999999}'
  self.pin={'documentId':'d','revision':'r','umfVersion':'0.10.0','sha256':sha256(self.document.encode()).hexdigest()}
  self.release=b'{"releaseId":"layout-r1","unknown":{"n":1.2300e-999999,"escaped":"\\u0061"}}'
  self.request=wire({'modules':[{'pin':self.pin,'documentJson':self.document}],'unknown':{'keep':True}})
  self.assessment=wire({'version':'truss.accepted-catalog-assessment/0.1','securityReady':False,'installationId':'installation-one','releaseId':'layout-r1','releaseSha256':sha256(self.release).hexdigest(),'modelPins':[self.pin],'unknown':{'keep':'all'}})
  column={'attnum':1,'name':'id','typeOid':'2950','typmod':-1,'collationOid':'0','notNull':True,'dropped':False,'generated':'','identity':''}
  self.inventory={'version':'truss.native-source.inventory/0.1-candidate','installationId':'installation-one','database':{'systemIdentifier':'18446744073709551615','oid':'42','name':'db'},'schema':{'oid':'43','name':'truss'},'release':{'id':'layout-r1','sha256':sha256(self.release).hexdigest()},'relations':[{'oid':'44','name':'object','ownerOid':'45','columns':[column,dict(column,attnum=2,name='props',typeOid='3802')]}]}
 def prepare(self,inventory=None,**overrides):
  args=dict(accepted_request=self.request,accepted_assessment=self.assessment,runtime_release=self.release,native_inventory=wire(self.inventory if inventory is None else inventory));args.update(overrides);return prepare_native_source_descriptor(**args)
 def test_exact_originals_and_native_column_labels_remain_data(self):
  result=self.prepare();self.assertIs(result.accepted_request,self.request);self.assertIs(result.runtime_release,self.release)
  self.assertIn(b'1.2300e-999999',result.runtime_release);self.assertIn(b'\\u0061',result.runtime_release)
  report=json.loads(result.json);self.assertFalse(report['authority']);self.assertFalse(report['complete']);self.assertFalse(report['securityReady']);self.assertEqual(report['nativeAdmission'],'required')
  self.assertEqual([r['role'] for r in report['sources']],['accepted-request','accepted-assessment','runtime-release','native-inventory'])
  self.assertEqual(report['sources'][2]['sha256'],sha256(self.release).hexdigest())
 def test_changed_native_identity_changes_descriptor_but_cannot_grant(self):
  first=self.prepare();other=copy.deepcopy(self.inventory);other['relations'][0]['oid']='99';second=self.prepare(other)
  self.assertNotEqual(first.json,second.json)
  # Identical supplied IDs after hypothetical recreation are indistinguishable
  # here. The pure descriptor still cannot authenticate continuity or permit.
  clone=self.prepare(copy.deepcopy(self.inventory));self.assertEqual(first.json,clone.json);self.assertFalse(json.loads(clone.json)['authority'])
 def test_relation_and_column_duplicates_refuse(self):
  for mutate in (lambda i:i['relations'].append(copy.deepcopy(i['relations'][0])),lambda i:i['relations'][0]['columns'].append(copy.deepcopy(i['relations'][0]['columns'][0]))):
   value=copy.deepcopy(self.inventory);mutate(value)
   with self.assertRaises(ValueError):self.prepare(value)
 def test_oid_and_attnum_forms_are_exact(self):
  for bad in ('0','01','+1','1.0','4294967296',True,42,None):
   value=copy.deepcopy(self.inventory);value['relations'][0]['oid']=bad
   with self.subTest(bad=bad),self.assertRaises(ValueError):self.prepare(value)
  for bad in (True,0,-1,32768,'1'):
   value=copy.deepcopy(self.inventory);value['relations'][0]['columns'][0]['attnum']=bad
   with self.subTest(bad=bad),self.assertRaises(ValueError):self.prepare(value)
 def test_native_shape_flags_names_and_typmod_refuse(self):
  for key,bad in [('notNull',1),('dropped',0),('generated','unknown'),('identity','unknown'),('typmod',True),('typmod',2**31),('name','\0'),('name','é'*32)]:
   value=copy.deepcopy(self.inventory);value['relations'][0]['columns'][0][key]=bad
   with self.subTest(key=key,bad=bad),self.assertRaises(ValueError):self.prepare(value)
  value=copy.deepcopy(self.inventory);value['authority']=True
  with self.assertRaises(ValueError):self.prepare(value)
 def test_original_release_installation_model_correspondence_refuse(self):
  for key,bad in [('releaseId','other'),('releaseSha256','0'*64),('installationId','other'),('securityReady',True),('modelPins',[])]:
   assessment=json.loads(self.assessment);assessment[key]=bad
   with self.subTest(key=key),self.assertRaises(ValueError):self.prepare(accepted_assessment=wire(assessment))
  request=json.loads(self.request);request['modules'][0]['documentJson']+=' '
  with self.assertRaises(ValueError):self.prepare(accepted_request=wire(request))
 def test_missing_and_coerced_model_pins_refuse_even_when_sources_agree(self):
  for key,value in [('revision',''),('umfVersion',True),('documentId',None),('sha256','not-a-hash')]:
   request=json.loads(self.request);assessment=json.loads(self.assessment)
   request['modules'][0]['pin'][key]=value;assessment['modelPins'][0][key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):self.prepare(accepted_request=wire(request),accepted_assessment=wire(assessment))
  request=json.loads(self.request);assessment=json.loads(self.assessment)
  del request['modules'][0]['pin']['revision'];del assessment['modelPins'][0]['revision']
  with self.assertRaises(ValueError):self.prepare(accepted_request=wire(request),accepted_assessment=wire(assessment))
 def test_nested_model_json_refuses_with_recomputed_matching_hash(self):
  for raw in ('{"id":"d","id":"d","umf":"0.10.0"}','{','[]','{"id":"other","umf":"0.10.0"}','{"id":"d","umf":"0.7.0"}','{"id":"d","umf":"0.10.0","x":NaN}'):
   request=json.loads(self.request);assessment=json.loads(self.assessment)
   request['modules'][0]['documentJson']=raw
   digest=sha256(raw.encode()).hexdigest();request['modules'][0]['pin']['sha256']=digest;assessment['modelPins'][0]['sha256']=digest
   with self.subTest(raw=raw),self.assertRaises(ValueError):self.prepare(accepted_request=wire(request),accepted_assessment=wire(assessment))
 def test_duplicate_unknown_and_nonfinite_sources_refuse(self):
  for raw in (b'{"x":1,"x":2}',b'{"x":NaN}',b'{"x":"\\ud800"}',b'[]',b'{'):
   with self.subTest(raw=raw),self.assertRaises(ValueError):self.prepare(runtime_release=raw)
 def test_nonbytes_and_boundaries_refuse_without_coercion(self):
  class Trap:
   def __str__(self):raise AssertionError('must not coerce')
   def __len__(self):raise AssertionError('must not inspect')
  for raw in ('{}',bytearray(b'{}'),Trap(),b'',b' '*4_000_001):
   with self.assertRaises(ValueError):self.prepare(accepted_request=raw)

 def with_runtime_source(self,raw):
  assessment=json.loads(self.assessment);inventory=copy.deepcopy(self.inventory)
  digest=sha256(raw).hexdigest();assessment['releaseSha256']=digest;inventory['release']['sha256']=digest
  return self.prepare(inventory,runtime_release=raw,accepted_assessment=wire(assessment))
 def test_numeric_token_capacity_is_exact_and_preserves_raw(self):
  raw=b'{"releaseId":"layout-r1","opaque":'+b'1'*512+b'}'
  result=self.with_runtime_source(raw);self.assertIs(result.runtime_release,raw)
  with self.assertRaisesRegex(ValueError,'token capacity'):self.with_runtime_source(b'{"releaseId":"layout-r1","opaque":'+b'1'*513+b'}')
 def test_object_and_array_capacity_with_matching_source_hashes(self):
  for value in ({str(n):None for n in range(4096)},[None]*4096):
   raw=wire({'releaseId':'layout-r1','opaque':value});self.assertEqual(self.with_runtime_source(raw).runtime_release,raw)
  for value in ({str(n):None for n in range(4097)},[None]*4097):
   with self.assertRaisesRegex(ValueError,'capacity'):self.with_runtime_source(wire({'releaseId':'layout-r1','opaque':value}))
 def test_depth_boundary_does_not_truncate_or_repair(self):
  value=0
  for _ in range(127):value=[value]
  raw=wire({'releaseId':'layout-r1','opaque':value});self.assertEqual(self.with_runtime_source(raw).runtime_release,raw)
  with self.assertRaisesRegex(ValueError,'tree capacity'):self.with_runtime_source(wire({'releaseId':'layout-r1','opaque':[value]}))
 def test_node_capacity_independent_of_byte_array_and_depth_limits(self):
  inside=wire({'releaseId':'layout-r1','opaque':[['']*3900 for _ in range(256)]})
  self.assertLess(len(inside),4_000_000);self.assertEqual(self.with_runtime_source(inside).runtime_release,inside)
  outside=wire({'releaseId':'layout-r1','opaque':[['']*3900 for _ in range(257)]})
  self.assertLess(len(outside),4_000_000)
  with self.assertRaisesRegex(ValueError,'tree capacity'):self.with_runtime_source(outside)
 def test_complete_model_count_capacity_not_hash_mismatch(self):
  def inputs(count):
   modules=[]
   for n in range(count):
    body=wire({'id':'doc'+str(n),'umf':'0.10.0','modules':[]}).decode()
    modules.append({'documentJson':body,'pin':{'documentId':'doc'+str(n),'revision':'r','umfVersion':'0.10.0','sha256':sha256(body.encode()).hexdigest()}})
   request=wire({'modules':modules});assessment=json.loads(self.assessment);assessment['modelPins']=[m['pin'] for m in modules]
   return request,wire(assessment)
  request,assessment=inputs(256);self.assertEqual(self.prepare(accepted_request=request,accepted_assessment=assessment).accepted_request,request)
  request,assessment=inputs(257)
  with self.assertRaisesRegex(ValueError,'model pins'):self.prepare(accepted_request=request,accepted_assessment=assessment)

if __name__=='__main__':unittest.main()
