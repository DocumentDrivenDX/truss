"""Supplied-definition joins; no native custody or admission from these carriers."""
import copy,json,unittest,os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from truss._native_model_correspondence import _join as model_join
from truss._native_graph_correspondence import _join,capture_native_graph_correspondence_with_cursor
ROOT=Path(__file__).resolve().parents[3]/'docs/helix/04-build/evidence/actual-graph-requirements-20261016'
FIXTURE=Path(__file__).parent/'fixtures/native-model-correspondence'
wire=lambda x:json.dumps(x,separators=(',',':')).encode()

class GraphCorrespondenceTests(unittest.TestCase):
 def setUp(self):
  self.graph=json.loads((ROOT/'issued-graph-requirements.json').read_bytes())
  self.model_requirements=(ROOT/'issued-model-requirements.json').read_bytes()
  self.assessment=json.loads((ROOT/'retained-native-assessment.json').read_bytes())
  # Synthetic unit carrier only. Historical0.1 is not native0.2 evidence.
  self.assessment['version']='truss.accepted-catalog-assessment/0.2-candidate'
  self.inventory=json.loads((FIXTURE/'native-inventory.json').read_bytes())
  observation=SimpleNamespace(accepted_request=(ROOT/'retained-native-accepted-request.json').read_bytes(),accepted_assessment=wire(self.assessment),runtime_release=(FIXTURE/'runtime-release.json').read_bytes(),native_inventory=wire(self.inventory))
  report=model_join(observation,self.model_requirements,self.graph['preparationSha256'],lambda:None)
  self.model=SimpleNamespace(observation=observation,requirements=self.model_requirements,report=report)
 def join(self,graph=None,assessment=None,inventory=None,check=lambda:None):
  model=copy.copy(self.model);model.observation=copy.copy(model.observation)
  if assessment is not None:model.observation.accepted_assessment=wire(assessment)
  if inventory is not None:model.observation.native_inventory=wire(inventory)
  return json.loads(_join(model,wire(self.graph if graph is None else graph),check))
 def test_complete_five_graphs_and_record_members_have_native_definition_ids(self):
  r=self.join();self.assertEqual(len(r['associations']),6)
  self.assertTrue(all(r[k] is False for k in ('complete','authority','securityReady')))
  self.assertEqual([a['ordinal'] for a in r['associations']],list(range(6)))
  expected={r['rel_id']:r['rel_type_id'] for r in self.assessment['inventory']['relationships']}
  self.assertEqual({a['reference']['relationshipId']:a['relationshipTypeId'] for a in r['associations'] if a['kind']=='core-relationship'},expected)
  self.assertEqual(r['associations'][-1]['kind'],'record-members');self.assertEqual(r['nativeAdmission'],'required')
 def test_cross_context_hash_source_pin_or_authority_refuse(self):
  for key,value in [('preparationSha256','0'*64),('modelRequirementsSha256','0'*64),('sourceRequestSha256','0'*64),('sourceRequestJson','{}'),('complete',True),('authority',True),('securityReady',True),('modelPins',[])]:
   g=copy.deepcopy(self.graph);g[key]=value
   with self.subTest(key=key),self.assertRaisesRegex(ValueError,'Same actual context'):self.join(g)
 def test_native_nominal_identity_census_and_realization_refuse(self):
  for field,value in [('document_id','foreign'),('module','foreign'),('rel_id','foreign'),('rel_type_id',True),('retired_rev',1),('directed',False),('assoc_type_id',1),('lifecycle','owned'),('composition',True),('inverse','other'),('target_key','other'),('source_min',True),('target_max',1)]:
   a=copy.deepcopy(self.assessment);a['inventory']['relationships'][0][field]=value
   with self.subTest(field=field),self.assertRaises(ValueError):self.join(assessment=a)
  a=copy.deepcopy(self.assessment);a['inventory']['relationships'].append(copy.deepcopy(a['inventory']['relationships'][0]))
  with self.assertRaisesRegex(ValueError,'Exact active native'):self.join(assessment=a)
 def test_native_endpoint_alternatives_and_types_are_exact(self):
  for field in ['source_type','target_type']:
   a=copy.deepcopy(self.assessment);a['inventory']['endpoints'][0][field]=True
   with self.subTest(field=field),self.assertRaisesRegex(ValueError,'typed native'):self.join(assessment=a)
  for mutate in [lambda a:a['inventory']['endpoints'].pop(),lambda a:a['inventory']['endpoints'].append(copy.deepcopy(a['inventory']['endpoints'][0]))]:
   a=copy.deepcopy(self.assessment);mutate(a)
   with self.assertRaisesRegex(ValueError,'typed native'):self.join(assessment=a)
 def test_original_key_full_identity_and_order_refuse(self):
  for part in ['documentId','revision','module','element']:
   g=copy.deepcopy(self.graph);g['associations'][0]['endpoints'][0]['key']['fields'][0][part]='foreign'
   with self.subTest(part=part),self.assertRaisesRegex(ValueError,'ordered endpoint Key'):self.join(g)
  g=copy.deepcopy(self.graph);g['associations'][0]['targets'][0]['key']['id']='other'
  with self.assertRaisesRegex(ValueError,'declared endpoint Key'):self.join(g)
 def test_graph_namespace_revision_witness_duplicate_and_occurrence_refuse(self):
  for edit in [lambda a:a.update(revision='foreign'),lambda a:a['reference'].update(elementId='ProjectClient'),lambda a:a.update(witness={'kind':'record-key'}),lambda a:a['sources'].append(copy.deepcopy(a['sources'][0])),lambda a:a['endpoints'][0].update(declarationOrdinals=[False]),lambda a:a.update(ordinal=True)]:
   g=copy.deepcopy(self.graph);edit(g['associations'][0])
   with self.assertRaises(ValueError):self.join(g)
  g=copy.deepcopy(self.graph);extra=copy.deepcopy(g['associations'][0]);extra['ordinal']=len(g['associations']);g['associations'].append(extra)
  with self.assertRaisesRegex(ValueError,'Distinct native graph'):self.join(g)
 def test_member_foreign_property_and_key_refuse(self):
  for edit in [lambda a:a['endpoints'][0]['members'][0]['field'].update(element='foreign'),lambda a:a['endpoints'][0]['key'].update(id='foreign')]:
   g=copy.deepcopy(self.graph);edit(g['associations'][-1])
   with self.assertRaises(ValueError):self.join(g)
 def test_edge_column_drift_and_shared_deadline_refuse(self):
  i=copy.deepcopy(self.inventory);next(c for r in i['relations'] if r['name']=='edge' for c in r['columns'] if c['name']=='source_type')['typeOid']='20'
  with self.assertRaisesRegex(ValueError,'native object column'):self.join(inventory=i)
  def expired():raise TimeoutError('shared deadline')
  with self.assertRaises(TimeoutError):self.join(check=expired)

@unittest.skipUnless(os.environ.get('TRUSS_GRAPH_JOIN_WEFT_QUALIFICATION')=='1','explicit opt-in Graph wheel required')
class IssuedGraphFactoryTests(GraphCorrespondenceTests):
 for name in tuple(n for n in dir(GraphCorrespondenceTests) if n.startswith('test_')):locals()[name]=None
 def current(self):
  import weft
  parent=weft.prepare_application_lineage((ROOT/'original-request.json').read_text());return parent,parent.prepare_current_presence()
 def test_actual_factory_retains_original_context_parent_and_native_observation(self):
  parent,current=self.current();cursor=SimpleNamespace(_deadline=SimpleNamespace(check=lambda:None))
  self.model.current=current;self.model.parent=parent
  with patch('truss._native_graph_correspondence.capture_native_model_correspondence_with_cursor',return_value=self.model) as observed:
   result=capture_native_graph_correspondence_with_cursor(cursor,current=current,accepted_request=self.model.observation.accepted_request)
  observed.assert_called_once_with(cursor,current=current,accepted_request=self.model.observation.accepted_request)
  self.assertIs(result.model.current,current);self.assertIs(result.model.parent,parent);self.assertEqual(result.requirements,wire(self.graph));self.assertEqual(len(json.loads(result.report)['associations']),6)
 def test_imported_data_and_equal_parent_replacement_cannot_supply_factory(self):
  parent,current=self.current();other,replacement=self.current();self.model.current=replacement;self.model.parent=other
  cursor=SimpleNamespace(_deadline=SimpleNamespace(check=lambda:None))
  with patch('truss._native_graph_correspondence.capture_native_model_correspondence_with_cursor',return_value=self.model):
   with self.assertRaisesRegex(ValueError,'must remain held'):capture_native_graph_correspondence_with_cursor(cursor,current=current,accepted_request=b'{}')
  for wrong in [None,self.graph,wire(self.graph),parent]:
   with patch('truss._native_graph_correspondence.capture_native_model_correspondence_with_cursor',side_effect=AssertionError('must not capture')):
    with self.assertRaisesRegex(ValueError,'Actual opt-in Graph'):capture_native_graph_correspondence_with_cursor(cursor,current=wrong,accepted_request=b'{}')
