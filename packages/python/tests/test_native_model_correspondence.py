"""Supplied metadata unit controls; actual source/witness/backend gates separate."""
import copy,hashlib,json,os,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from truss._native_model_correspondence import _join,capture_native_model_correspondence_with_cursor

ROOT=Path(__file__).parent/'fixtures/native-model-correspondence'
wire=lambda value:json.dumps(value,separators=(',',':')).encode()

class NativeModelCorrespondenceTests(unittest.TestCase):
 def setUp(self):
  self.observation=SimpleNamespace(**{key:(ROOT/name).read_bytes() for key,name in [('accepted_request','accepted-request.json'),('accepted_assessment','accepted-assessment.json'),('runtime_release','runtime-release.json'),('native_inventory','native-inventory.json')]})
  self.requirements=(ROOT/'issued-requirements.json').read_bytes();self.issued=json.loads(self.requirements);self.assessment=json.loads(self.observation.accepted_assessment);self.inventory=json.loads(self.observation.native_inventory)
 def join(self,issued=None,assessment=None,inventory=None,**changes):
  obs=copy.copy(self.observation)
  if assessment is not None:obs.accepted_assessment=wire(assessment)
  if inventory is not None:obs.native_inventory=wire(inventory)
  for key,value in changes.items():setattr(obs,key,value)
  return _join(obs,self.requirements if issued is None else wire(issued),self.issued['preparationSha256'],lambda:None)
 def test_complete_qualified_records_fields_keys_and_data_flags(self):
  r=json.loads(self.join());self.assertFalse(r['complete']);self.assertFalse(r['authority']);self.assertFalse(r['securityReady']);self.assertEqual(r['nativeAdmission'],'required')
  expected={'Staff':(['staffId'],['staffId']),'Project':(['projectId'],['projectId']),'Resource':(['resourceId','salary','token'],['resourceId']),'Ownership':(['ownerId','ownerResource','ownerProject'],['ownerId']),'Assignment':(['assignmentId','assignmentStaff','assignmentProject','active'],['assignmentId'])}
  self.assertEqual(len(r['records']),5)
  for row in r['records']:
   name=row['record']['element'];fields,keys=expected[name]
   self.assertEqual(row['record'],{'documentId':'domain','revision':'query-value-core-r1','module':'m','element':name})
   self.assertEqual([f['field']['element'] for f in row['fields']],fields);self.assertEqual([f['element'] for f in row['selectedKey']['fields']],keys)
   self.assertEqual(row['selectedKey']['id'],'pk');self.assertEqual(row['objectHome']['columns']['props']['typeOid'],'3802')
   self.assertEqual([f['propertyId'] for f in row['fields'] if f['field']['element'] in keys],row['selectedKey']['propertyIds'])
  self.assertEqual([x['role'] for x in r['sources']],['accepted-request','accepted-assessment','runtime-release','native-inventory','issued-requirements']);self.assertEqual(r['sources'][-1]['sha256'],hashlib.sha256(self.requirements).hexdigest())
 def test_wrong_original_source_and_preparation_hash_refuse(self):
  for edit in [lambda r:r.update(preparationSha256='0'*64),lambda r:r.update(sourceRequestSha256='0'*64),lambda r:r['modelPins'][0].update(revision='other')]:
   issued=copy.deepcopy(self.issued);edit(issued)
   with self.assertRaises(ValueError):self.join(issued)
  accepted=json.loads(self.observation.accepted_request);accepted['modules'][0]['documentJson']+=' '
  with self.assertRaises(ValueError):self.join(accepted_request=wire(accepted))
 def test_duplicate_record_native_identity_and_properties_refuse(self):
  issued=copy.deepcopy(self.issued);issued['records'].append(copy.deepcopy(issued['records'][0]))
  with self.assertRaises(ValueError):self.join(issued)
  for key in ['types','properties','keys']:
   a=copy.deepcopy(self.assessment);a['inventory'][key].append(copy.deepcopy(a['inventory'][key][0]))
   with self.subTest(key=key),self.assertRaises(ValueError):self.join(assessment=a)
 def test_complete_field_and_key_identity_refuse_foreign_components(self):
  for area in ['record','field','key']:
   for component in ['documentId','revision','module','element']:
    r=copy.deepcopy(self.issued);row=r['records'][0];target=row['record'] if area=='record' else row['fields'][0]['field'] if area=='field' else row['selectedKey']['fields'][0];target[component]='foreign'
    with self.subTest(area=area,component=component),self.assertRaises(ValueError):self.join(r)
 def test_native_row_home_family_and_availability_refuse_even_no_object_rows(self):
  # There are no data-row inputs: definition/correspondence failure must not
  # be interpreted as empty coverage or absence.
  for key,value in [('home','row'),('cardinality','many'),('scalar_type','date'),('nullability','nullable')]:
   a=copy.deepcopy(self.assessment);a['inventory']['properties'][0][key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):self.join(assessment=a)
  r=copy.deepcopy(self.issued);r['records'][0]['fields'][0]['descriptors'][0]['availability']='absent-allowed'
  with self.assertRaises(ValueError):self.join(r)
 def test_native_id_and_key_census_are_exact(self):
  for key,value in [('key_num',True),('key_num',0),('prop_ids',[True]),('prop_ids',[]),('key_id','other')]:
   a=copy.deepcopy(self.assessment);a['inventory']['keys'][0][key]=value
   with self.subTest(key=key,value=value),self.assertRaises(ValueError):self.join(assessment=a)
  a=copy.deepcopy(self.assessment);a['inventory']['properties'].pop()
  with self.assertRaises(ValueError):self.join(assessment=a)
 def test_complete_member_census_rejects_extra_native_and_missing_issued_non_key(self):
  a=copy.deepcopy(self.assessment)
  resource=next(t['type_id'] for t in a['inventory']['types'] if t['element']=='Resource')
  extra=copy.deepcopy(next(p for p in a['inventory']['properties'] if p['type_id']==resource and p['element']=='salary'))
  extra['prop_id']=max(p['prop_id'] for p in a['inventory']['properties'])+1
  extra['element']='unexpectedUniqueActiveMember'
  a['inventory']['properties'].append(extra)
  with self.assertRaisesRegex(ValueError,'Complete original property membership'):
   self.join(assessment=a)
  r=copy.deepcopy(self.issued)
  record=next(row for row in r['records'] if row['record']['element']=='Resource')
  record['fields']=[f for f in record['fields'] if f['field']['element']!='salary']
  with self.assertRaisesRegex(ValueError,'Complete original property membership'):
   self.join(issued=r)
 def test_composite_order_is_not_set_order_in_supplied_metadata(self):
  # Supplied control only; it does not issue a compiler context or admit this
  # changed requirement against the unchanged original model.
  r=copy.deepcopy(self.issued);resource=next(x for x in r['records'] if x['record']['element']=='Resource');fields={f['field']['element']:f['field'] for f in resource['fields']};resource['selectedKey']['fields']=[fields['salary'],fields['resourceId']]
  a=copy.deepcopy(self.assessment);t=next(t['type_id'] for t in a['inventory']['types'] if t['element']=='Resource');p={p['element']:p['prop_id'] for p in a['inventory']['properties'] if p['type_id']==t};key=next(k for k in a['inventory']['keys'] if k['type_id']==t);key['prop_ids']=[p['salary'],p['resourceId']]
  result=json.loads(self.join(r,a));out=next(x for x in result['records'] if x['record']['element']=='Resource');self.assertEqual(out['selectedKey']['propertyIds'],[p['salary'],p['resourceId']])
  key['prop_ids'].reverse()
  with self.assertRaisesRegex(ValueError,'ordered native Key'):self.join(r,a)
 def test_changed_or_unsupported_physical_column_refuses(self):
  for name,value in [('typeOid','25'),('notNull',False),('notNull',1),('generated','s'),('name','props-drift')]:
   i=copy.deepcopy(self.inventory);col=next(c for t in i['relations'] if t['name']=='object' for c in t['columns'] if c['name']=='props');col[name]=value
   with self.subTest(name=name),self.assertRaises(ValueError):self.join(inventory=i)
 def test_distinct_decoder_byte_profiles_and_shared_strictness(self):
  from truss._owner_evidence_json import decode_owner_evidence_json,decode_issued_model_requirements_json
  for decode,limit in [(decode_owner_evidence_json,8_388_608),(decode_issued_model_requirements_json,16_000_000)]:
   with self.subTest(limit=limit):
    self.assertEqual(decode(b'0'+b' '*(limit-1)),0)
    for bad in [b'0'+b' '*limit,b'{"x":0,"x":1}',b'NaN',b'1'*513,b'"\\ud800"',b'['*130+b'0'+b']'*130]:
     with self.assertRaises(ValueError):decode(bad)
  self.assertEqual(decode_issued_model_requirements_json(b'0'+b' '*8_388_608),0)
 def test_deadline_and_requirements_capacity_refuse(self):
  def expired():raise TimeoutError('original host deadline')
  with self.assertRaises(TimeoutError):_join(self.observation,self.requirements,self.issued['preparationSha256'],expired)
  with self.assertRaises(ValueError):_join(self.observation,b' '*16_000_001,self.issued['preparationSha256'],lambda:None)

@unittest.skipUnless(os.environ.get('TRUSS_MODEL_JOIN_WEFT_QUALIFICATION')=='1','requires explicitly selected original opt-in Weft candidate')
class IssuedModelCorrespondenceTests(NativeModelCorrespondenceTests):
 # Only these factory tests use the actual compiler context; capture is still
 # deliberately mocked, so these tests supply no native/operation authority.
 for name in tuple(n for n in dir(NativeModelCorrespondenceTests) if n.startswith('test_')):locals()[name]=None
 def current(self):
  import weft
  parent=weft.prepare_application_lineage((ROOT/'weft-original-request.json').read_text());return parent,parent.prepare_current_presence()
 def test_actual_factory_retains_same_parent_and_originals(self):
  parent,current=self.current();cursor=SimpleNamespace(_deadline=SimpleNamespace(check=lambda:None))
  with patch('truss._native_model_correspondence.capture_native_source_observation_with_cursor',return_value=self.observation) as capture:
   result=capture_native_model_correspondence_with_cursor(cursor,current=current,accepted_request=self.observation.accepted_request)
  capture.assert_called_once_with(cursor,self.observation.accepted_request);self.assertIs(result.current,current);self.assertIs(result.parent,parent);self.assertIs(result.observation,self.observation);self.assertEqual(result.requirements,self.requirements);self.assertEqual(len(json.loads(result.report)['records']),5)
 def test_report_import_wrong_receiver_cannot_supply_current(self):
  for current in [None,self.requirements,self.issued,object()]:
   with patch('truss._native_model_correspondence.capture_native_source_observation_with_cursor',side_effect=AssertionError('must refuse before native capture')):
    with self.assertRaises(ValueError):capture_native_model_correspondence_with_cursor(SimpleNamespace(),current=current,accepted_request=self.observation.accepted_request)
 def test_equal_data_contexts_keep_distinct_actual_parent_identity(self):
  parent,a=self.current();other,b=self.current();cursor=SimpleNamespace(_deadline=SimpleNamespace(check=lambda:None))
  with patch('truss._native_model_correspondence.capture_native_source_observation_with_cursor',return_value=self.observation):
   first=capture_native_model_correspondence_with_cursor(cursor,current=a,accepted_request=self.observation.accepted_request);second=capture_native_model_correspondence_with_cursor(cursor,current=b,accepted_request=self.observation.accepted_request)
  self.assertEqual(first.report,second.report);self.assertIs(first.parent,parent);self.assertIs(second.parent,other);self.assertIsNot(first.parent,second.parent)
