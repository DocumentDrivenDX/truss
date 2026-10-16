"""Original current UMF catalog source observer; native0.8 ingress remains open."""
import copy,json,unittest,subprocess
from unittest.mock import patch
from pathlib import Path
from hashlib import sha256
from truss._core08_catalog_source import prepare_core08_catalog_source
from truss.weft import CompileRefusal
from truss.preparation import PreparedAcceptance,_require_original_preparation
FIXTURE=Path(__file__).parent/'fixtures/security-mapping-request.json'
def original():return json.loads(FIXTURE.read_text())['modules'][0]['documentJson'].encode()
def prepare(source=None,identity='domain'):
 return prepare_core08_catalog_source(original() if source is None else source,document_id=identity,document_revision='schema-1',bun_executable='/opt/homebrew/bin/bun')
class Core08CatalogSourceTests(unittest.TestCase):
 def test_genuine_security_model_complete_current_owner_observations(self):
  result=prepare();self.assertEqual(result.original_document,original());self.assertFalse(result.native_ready)
  self.assertNotIsInstance(result,PreparedAcceptance)
  with self.assertRaises(ValueError):_require_original_preparation(result)
  response=json.loads(result.original_response);model=json.loads(original());expected=[]
  expected.append(('inspectCoreSchemaProperties',{'scope':'document'}))
  for m in model['modules']:
   expected.extend([('inspectCoreSchemaProperties',{'scope':'module','module':m['id']}),('inspectCoreRelationships',{'module':m['id']})])
   for e in m['elements']:
    expected.append(('inspectCoreSchemaProperties',{'scope':'element','module':m['id'],'element':e['id']}))
    for op in ('inspectCoreElementKind','inspectCoreNullability','inspectCoreCardinality','inspectCoreFacets','inspectCoreRecordMembers','inspectCoreScalarType','inspectCoreReferenceLinks'):expected.append((op,{'module':m['id'],'element':e['id']}))
    if e['kind']=='record':expected.append(('inspectCoreKeys',{'module':m['id'],'element':e['id']}))
  self.assertEqual([(x['operation'],x['identity']) for x in response['observations']],expected)
  for x in response['observations']:self.assertEqual(x['result']['source'],model)
  salary=next(x['result'] for x in response['observations'] if x['operation']=='inspectCoreFacets' and x['identity'].get('element')=='salary')
  self.assertEqual(salary['version'],'4.0.0');self.assertEqual(salary['meaning']['interpreted'],{'integerWidth':{'bits':64,'signed':True}})
  self.assertEqual(response['sourceSha256'],sha256(original()).hexdigest())
 def test_current_schema_properties_and_opaque_bytes_are_preserved(self):
  model=json.loads(original());field=next(x for x in model['modules'][0]['elements'] if x['id']=='resourceId')
  field['title']='Résumé';field['aliases']=['識別子'];field['default']={'value':{'string':'EXACT'},'on':'missing'};field['facets']={'length':{'min':1,'max':40,'unit':'unicode-scalar'}}
  model['vocabularies']={'future':{'version':'99.0.0'}};field['extensions']['future']={'nested':['opaque',None,{'value':'🦉'}]}
  source=json.dumps(model,ensure_ascii=False,indent=3).encode();result=prepare(source);response=json.loads(result.original_response)
  self.assertEqual(result.original_document,source);self.assertEqual(response['originalDocumentJson'].encode(),source)
  facets=next(x['result'] for x in response['observations'] if x['operation']=='inspectCoreFacets' and x['identity'].get('element')=='resourceId')
  self.assertEqual(facets['meaning']['interpreted']['length'],{'min':1,'max':40,'unit':'unicode-scalar'})
  properties=next(x['result'] for x in response['observations'] if x['operation']=='inspectCoreSchemaProperties' and x['identity'].get('element')=='resourceId')
  self.assertEqual(properties['properties']['default'],{'value':{'string':'EXACT'},'on':'missing'})
 def test_legacy_invalid_or_changed_identity_refuses_without_observation_artifact(self):
  legacy=json.loads(original());legacy['umf']='0.7.0'
  for source,identity in ((json.dumps(legacy).encode(),'domain'),(b'{"umf":"0.8.0","id":"domain"}','domain'),(original(),'other'),(b'{"id":"x","id":"y"}','domain')):
   with self.subTest(source=source[:40],identity=identity),self.assertRaises(CompileRefusal):prepare(source,identity)
 def test_selected_source_replication_capacity_refuses(self):
  source=json.loads(original());source['vocabularies']={'future':{'version':'99.0.0'}};source['extensions']={'future':{'padding':'x'*200000}}
  with self.assertRaises(CompileRefusal):prepare(json.dumps(source).encode())

 def test_capture_timeout_refuses_without_partial_artifact(self):
  with patch('truss._core08_catalog_source._capture',side_effect=subprocess.TimeoutExpired(['bun','--version'],5)):
   with self.assertRaises(CompileRefusal) as refusal:prepare()
  self.assertEqual(refusal.exception.code,'core08_runtime')

 def test_invalid_identity_utf8_refuses_before_runtime_capture(self):
  with patch('truss._core08_catalog_source._capture') as capture:
   with self.assertRaises(CompileRefusal) as refusal:prepare(identity='\ud800')
  self.assertEqual(refusal.exception.code,'core08_input');capture.assert_not_called()
