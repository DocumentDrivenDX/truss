import copy,hashlib,importlib.util,json,unittest
from pathlib import Path
import psycopg
from psycopg.types.json import Jsonb
EVIDENCE=Path(__file__).parent
DRAFT=Path(__file__).resolve().parents[5]/'packages/postgresql/native/catalog-finalization'
ROOT=Path(__file__).resolve().parents[5]
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
codec=load('codec',ROOT/'docs/helix/04-build/evidence/manifest-codec-pg18/check.py')
oracle=load('oracle',EVIDENCE/'oracle.py')
import base64
def artifact(identity,raw):
 return {"identity":identity,"bytesBase64":base64.b64encode(raw).decode(),"sha256":hashlib.sha256(raw).hexdigest()}
class Builder(codec.Codec):
 @classmethod
 def setUpClass(cls):
  super().setUpClass()
  cls.conn.execute((ROOT/'packages/postgresql/native/canonical-tree-bytes.sql').read_text())
  cls.conn.execute((DRAFT/'native-tree-dependency.sql').read_text())
  cls.conn.execute((DRAFT/'original-manifest.owner-export.sql').read_text())
 def inputs(self):
  return {'original_input':{'documents':[{'artifact':artifact('z',b'z original'),'umfProfile':{'identity':'umf','version':'fixture','sha256':'1'*64}}, {'artifact':artifact('a',b'a original'),'umfProfile':{'identity':'umf','version':'fixture','sha256':'1'*64}}]},
   'revision':'1','xid':'9007199254740993','feed_context':{'sourceEpoch':'epoch','feedProfile':'selected','scopeIdentity':'administrative_single_original_operation_fresh_catalog_rollback_only'},
   'manifest_definition_bytes':(DRAFT/'manifest-definition-v0.4.canonical').read_bytes(),
   'payload_profile_bytes':(ROOT/'packages/python/src/truss/_profiles/catalog-revision-wide-report-composition-candidate.json').read_bytes(), 'original_payload_bytes':b'original payload',
   'original_configuration':{'generation':'7','keyReuse':'forbid','journalMode':'engine','sourceEpoch':'epoch','installationId':'installation','targetIncarnation':'original incarnation','admissionProfileBytes':b'original admission','configurationBytes':b'original configuration','bindingBytes':b'original binding','inventoryBytes':b'original inventory'},
   'original_configuration_profile_bytes':b'{"identity":"cfg","version":"fixture"}'}
 def build(self,v,raw_input=None):
  cfg=v['original_configuration']
  nativecfg={k:cfg[k] for k in ['generation','keyReuse','journalMode','sourceEpoch','installationId','targetIncarnation']}
  for k in ['admissionProfile','configuration','binding','inventory']:nativecfg[k+'Hex']=cfg[k+'Bytes'].hex()
  args=(raw_input or json.dumps(v['original_input'],ensure_ascii=False,separators=(',',':')).encode(),v['revision'],v['xid'],Jsonb(v['feed_context']),v['manifest_definition_bytes'],v['payload_profile_bytes'],v['original_payload_bytes'],json.dumps(nativecfg,separators=(',',':')).encode(),v['original_configuration_profile_bytes'])
  rows=self.conn.execute('SELECT * FROM truss.runtime_original_catalog_manifest_candidate(%s,%s,%s,%s,%s,%s,%s,%s,%s)',args).fetchall()
  self.assertEqual(len(rows),1);return tuple(bytes(x) for x in rows[0])
 def assert_original(self,v):
  expected=oracle.expected_manifest(**v);actual=self.build(v)
  self.assertEqual(actual,(expected['treeBytes'],expected['wireBytes'],bytes.fromhex(expected['semanticSha256'])))
  return actual
 def refuse_builder(self,v,state,raw_input=None):
  self.conn.execute('SAVEPOINT builder_control')
  try:
   with self.assertRaises(psycopg.Error) as caught:self.build(v,raw_input)
   self.assertEqual(caught.exception.sqlstate,state)
  finally:
   self.conn.execute('ROLLBACK TO SAVEPOINT builder_control');self.conn.execute('RELEASE SAVEPOINT builder_control')
 def test_original_complete_tree_digest_wire_and_order(self):
  v=self.inputs();before=self.assert_original(v)
  v['original_input']['documents'].reverse();self.assertEqual(self.assert_original(v),before)
  self.assertNotIn('manifestSha256',json.loads(before[0]));self.assertIn('manifestSha256',json.loads(before[1]))
  from referencing import Registry,Resource
  from jsonschema import Draft202012Validator
  directory=ROOT/'docs/helix/02-design/contracts'
  schemas=[json.loads((directory/n).read_bytes()) for n in ['feed-transaction-v0.2.schema.json','acceptance-input-v0.1.schema.json','import-report-v0.1.schema.json']]
  registry=Registry().with_resources((d['$id'],Resource.from_contents(d)) for d in schemas)
  Draft202012Validator(schemas[0],registry=registry).validate(json.loads(before[1]))
 def test_duplicate_original_dedup_and_conflict(self):
  v=self.inputs();before=self.assert_original(v)
  v['original_input']['documents'].append(copy.deepcopy(v['original_input']['documents'][0]));self.assertEqual(self.assert_original(v),before)
  v['original_input']['documents'][-1]['umfProfile']['version']='changed';self.refuse_builder(v,'55000')
  v['original_input']['documents'][-1]['umfProfile']['version']='fixture'
  v['original_input']['documents'][-1]['artifact']=artifact('z',b'conflicting original bytes');self.refuse_builder(v,'55000')
 def test_same_configuration_coordinates_changed_inventory(self):
  v=self.inputs();before=self.assert_original(v);v['original_configuration']['inventoryBytes']=b'changed inventory';after=self.assert_original(v)
  a=json.loads(before[0])['configurationPrerequisites'][0]['artifact'];b=json.loads(after[0])['configurationPrerequisites'][0]['artifact']
  self.assertEqual(a['identity'],b['identity']);self.assertNotEqual(a['sha256'],b['sha256'])
 def test_malformed_coordinates_version_epoch_and_duplicate_raw_input(self):
  v=self.inputs();v['original_payload_bytes']=b'x'*4194305;self.refuse_builder(v,'54000')
  for key,value in [('revision','01'),('revision','0'),('xid','18446744073709551616'),('xid','-1')]:
   v=self.inputs();v[key]=value;self.refuse_builder(v,'22023')
  v=self.inputs();v['feed_context']['scopeIdentity']='wrong_scope';self.refuse_builder(v,'55000')
  v=self.inputs();v['original_configuration']['sourceEpoch']='wrong';self.refuse_builder(v,'22023')
  v=self.inputs();v['manifest_definition_bytes']=v['manifest_definition_bytes'].replace(b'0.4.0-original-artifact-codec-candidate',b'0.3.0-configuration-identity-candidate');self.refuse_builder(v,'55000')
  v=self.inputs();v['payload_profile_bytes']=b'{"identity":"payload","version":"fixture"}';self.refuse_builder(v,'55000')
  for key in ['keyReuse','journalMode']:
   v=self.inputs();v['original_configuration'][key]='unsupported';self.refuse_builder(v,'22023')
  for value in [None,'profile',{}, {'identity':'umf','version':'fixture','sha256':'NOT-SHA'}]:
   v=self.inputs();v['original_input']['documents'][0]['umfProfile']=value;self.refuse_builder(v,'22023')
  v=self.inputs();v['payload_profile_bytes']=b'{"version":"fixture"}';self.refuse_builder(v,'22023')
  v=self.inputs();v['original_configuration']['installationId']='';self.refuse_builder(v,'22023')
  v=self.inputs();raw=json.dumps(v['original_input']).encode();raw=b'{"documents":[],'+raw[1:];self.refuse_builder(v,'22023',raw)
if __name__=='__main__':unittest.main(verbosity=2)
