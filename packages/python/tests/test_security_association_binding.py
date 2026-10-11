"""Original-source mapping checks; no owner semantics/native authority claim."""
from dataclasses import FrozenInstanceError
from hashlib import sha256
import json
from pathlib import Path
import unittest
from truss._security_association_binding import prepare_association_binding, AssociationBindingError

ROOT=Path(__file__).parent/'fixtures'
CORE=(ROOT/'security-association-core.json').read_bytes()
ONTOLOGY=(ROOT/'security-association-ontology.json').read_bytes()
def wire(value):return json.dumps(value,separators=(',',':')).encode()
def inputs(core=CORE,ontology=ONTOLOGY):
 c,o=json.loads(core),json.loads(ontology);elements={(c['id'],m['id'],e['id']):e for m in c['modules'] for e in m['elements']};entities={tuple(e['type'].values()):e for e in o['entities']}
 mappings=[]
 for association in o['associations']:
  roles=[]
  for endpoint in association['endpoints']:
   ref=endpoint['target'];owner=elements[tuple(ref.values())];key_id=entities[tuple(ref.values())]['keyId'];key=next(k for k in owner['keys'] if k['id']==key_id)
   roles.append({'role':endpoint['role'],'associationFields':endpoint['fields'],'target':ref,'targetKeyId':key_id,'targetFields':[{'documentId':ref['documentId'],'moduleId':f['module'],'elementId':f['element']} for f in key['fields']]})
  mappings.append({'association':association['type'],'instanceKeyId':association['keyId'],'sourceRole':roles[0]['role'],'targetRole':roles[1]['role'],'roles':roles,'storage':{'sourceMin':'0','sourceMax':'*','targetMin':'0','targetMax':'*','directed':True,'lifecycle':'independent','composition':False,'inverse':None}})
 return {'profile':'truss-binary-association-candidate/0.1.0','coreSha256':sha256(core).hexdigest(),'ontologySha256':sha256(ontology).hexdigest(),'modelRevision':o['documents'][0]['revision'],'ontologyRevision':o['revision'],'mappings':mappings}
class BindingTests(unittest.TestCase):
 def run_binding(self,binding=None,core=CORE,ontology=ONTOLOGY):return prepare_association_binding(core,ontology,wire(inputs(core,ontology) if binding is None else binding))
 def refuse(self,change,reason):
  binding=inputs();change(binding)
  with self.assertRaisesRegex(AssociationBindingError,reason):self.run_binding(binding)
 def test_original_complete_two_association_basis(self):
  result=self.run_binding();self.assertEqual(result.core_bytes,CORE);self.assertEqual(result.ontology_bytes,ONTOLOGY);self.assertEqual([a.association[2] for a in result.associations],['Ownership','Assignment']);self.assertEqual(len(result.associations[1].all_member_fields),3);self.assertEqual(result.scope,'original_source_correspondence_only')
 def test_both_explicit_orientations_preserve_roles(self):
  binding=inputs()
  for mapping in binding['mappings']:mapping['sourceRole'],mapping['targetRole']=mapping['targetRole'],mapping['sourceRole']
  result=self.run_binding(binding);self.assertEqual(result.associations[1].source_role,'project');self.assertEqual(result.associations[1].roles[0].role,'staff')
 def test_output_has_no_mutable_mapping_containers(self):
  result=self.run_binding()
  with self.assertRaises(FrozenInstanceError):result.associations[0].source_role='changed'
  self.assertIsInstance(result.associations,tuple);self.assertIsInstance(result.associations[0].instance_key_fields,tuple)
 def test_changed_core_digest(self):self.refuse(lambda b:b.update(coreSha256='0'*64),'source_digest')
 def test_changed_ontology_digest(self):self.refuse(lambda b:b.update(ontologySha256='0'*64),'source_digest')
 def test_changed_model_revision(self):self.refuse(lambda b:b.update(modelRevision='stale'),'model_revision')
 def test_changed_ontology_revision(self):self.refuse(lambda b:b.update(ontologyRevision='stale'),'ontology_revision')
 def test_omitted_association(self):self.refuse(lambda b:b['mappings'].pop(),'association_coverage')
 def test_duplicate_association(self):self.refuse(lambda b:b['mappings'].append(b['mappings'][0]),'association_coverage')
 def test_extra_mapping(self):self.refuse(lambda b:b['mappings'][0]['association'].update(elementId='Staff'),'association_coverage')
 def test_role_alias(self):self.refuse(lambda b:b['mappings'][1].update(sourceRole='project'),'role_orientation')
 def test_omitted_role(self):self.refuse(lambda b:b['mappings'][0]['roles'].pop(),'role_coverage')
 def test_duplicate_role(self):self.refuse(lambda b:b['mappings'][0]['roles'].append(b['mappings'][0]['roles'][0]),'role_coverage')
 def test_substituted_endpoint_field(self):self.refuse(lambda b:b['mappings'][1]['roles'][0]['associationFields'][0].update(elementId='active'),'endpoint_fields')
 def test_substituted_target(self):self.refuse(lambda b:b['mappings'][1]['roles'][0]['target'].update(elementId='Project'),'endpoint_target')
 def test_substituted_target_key(self):self.refuse(lambda b:b['mappings'][1]['roles'][0].update(targetKeyId='other'),'target_key')
 def test_substituted_target_field(self):self.refuse(lambda b:b['mappings'][1]['roles'][0]['targetFields'][0].update(elementId='projectId'),'ordered_target_key')
 def test_changed_instance_key_selection(self):self.refuse(lambda b:b['mappings'][1].update(instanceKeyId='other'),'instance_key')
 def test_restrictive_storage(self):self.refuse(lambda b:b['mappings'][1]['storage'].update(targetMax='1'),'storage_subset')
 def test_no_default_storage(self):self.refuse(lambda b:b['mappings'][1]['storage'].pop('lifecycle'),'closed_binding')
 def test_no_numeric_boolean_alias(self):self.refuse(lambda b:b['mappings'][1]['storage'].update(directed=1),'storage_subset')
 def test_unknown_binding_members(self):self.refuse(lambda b:b.update(authority=True),'closed_binding')
 def test_duplicate_wire_member(self):
  original=wire(inputs()).replace(b'"profile":',b'"profile":"ignored","profile":',1)
  with self.assertRaisesRegex(AssociationBindingError,'duplicate_member'):prepare_association_binding(CORE,ONTOLOGY,original)
 def test_exact_bytes_required(self):
  with self.assertRaisesRegex(AssociationBindingError,'original_bytes'):prepare_association_binding(bytearray(CORE),ONTOLOGY,wire(inputs()))
 def test_unknown_core_content_is_archived_without_interpretation(self):
  core=json.loads(CORE);core.setdefault('extensions',{})['unknown']={'fraction':0.125,'opaque':'keep'};original=wire(core);result=self.run_binding(core=original);self.assertEqual(result.core_bytes,original)
 def test_attribute_dependent_key_cannot_be_collapsed_to_one_edge(self):
  core=json.loads(CORE);association=next(e for e in core['modules'][0]['elements'] if e['id']=='Assignment');association['keys'][0]['fields'].append({'module':'m','element':'active'});original=wire(core)
  with self.assertRaisesRegex(AssociationBindingError,'parallel_instance_storage_loss'):self.run_binding(core=original)
 def test_separate_instance_identity_cannot_be_collapsed_to_one_edge(self):
  core=json.loads(CORE);module=core['modules'][0];association=next(e for e in module['elements'] if e['id']=='Assignment');association['members'].append({'module':'m','element':'instanceId'});association['keys'][0]['fields']=[{'module':'m','element':'instanceId'}];module['elements'].append({'id':'instanceId','name':'instanceId','kind':'field','scalarType':'string','nullability':'required','cardinality':'one','extensions':{}});original=wire(core)
  with self.assertRaisesRegex(AssociationBindingError,'parallel_instance_storage_loss'):self.run_binding(core=original)
 def composite(self):
  core=json.loads(CORE);ontology=json.loads(ONTOLOGY);module=core['modules'][0]
  for owner_id,field_id in [('Staff','staffPartition'),('Assignment','assignmentPartition')]:
   owner=next(e for e in module['elements'] if e['id']==owner_id);owner['members'].append({'module':'m','element':field_id});owner['keys'][0]['fields'].insert(0,{'module':'m','element':field_id});module['elements'].append({'id':field_id,'name':field_id,'kind':'field','scalarType':'string','nullability':'required','cardinality':'one','extensions':{}})
  staff=next(e for e in ontology['entities'] if e['type']['elementId']=='Staff');staff['fields'].append({'ref':{'documentId':'domain','moduleId':'m','elementId':'staffPartition'},'protection':'unprotected'})
  assignment=next(a for a in ontology['associations'] if a['type']['elementId']=='Assignment');assignment['fields'].append({'ref':{'documentId':'domain','moduleId':'m','elementId':'assignmentPartition'},'protection':'unprotected'});assignment['endpoints'][0]['fields'].insert(0,{'documentId':'domain','moduleId':'m','elementId':'assignmentPartition'})
  return wire(core),wire(ontology)
 def test_composite_target_and_association_order_positive(self):
  core,ontology=self.composite();basis=self.run_binding(core=core,ontology=ontology);role=basis.associations[1].roles[0];self.assertEqual([f[2] for f in role.target_fields],['staffPartition','staffId']);self.assertEqual([f[2] for f in role.association_fields],['assignmentPartition','assignmentStaff'])
 def test_composite_target_order_refuses(self):
  core,ontology=self.composite();binding=inputs(core,ontology);binding['mappings'][1]['roles'][0]['targetFields'].reverse()
  with self.assertRaisesRegex(AssociationBindingError,'ordered_target_key'):self.run_binding(binding,core,ontology)
 def test_composite_association_order_refuses(self):
  core,ontology=self.composite();binding=inputs(core,ontology);binding['mappings'][1]['roles'][0]['associationFields'].reverse()
  with self.assertRaisesRegex(AssociationBindingError,'endpoint_fields'):self.run_binding(binding,core,ontology)
 def test_authored_unique_subset_of_endpoints_positive(self):
  core=json.loads(CORE);association=next(e for e in core['modules'][0]['elements'] if e['id']=='Assignment');association['keys'][0]['fields']=association['keys'][0]['fields'][:1];result=self.run_binding(core=wire(core));self.assertEqual(len(result.associations[1].instance_key_fields),1)
 def test_third_authored_role_is_unsupported(self):
  ontology=json.loads(ONTOLOGY);endpoint=dict(ontology['associations'][1]['endpoints'][0]);endpoint['role']='extra';ontology['associations'][1]['endpoints'].append(endpoint);original=wire(ontology)
  with self.assertRaisesRegex(AssociationBindingError,'binary_profile'):self.run_binding(ontology=original)
 def test_nonstring_endpoint_profile_is_unsupported(self):
  core=json.loads(CORE);next(e for e in core['modules'][0]['elements'] if e['id']=='staffId')['scalarType']='integer';original=wire(core)
  with self.assertRaisesRegex(AssociationBindingError,'endpoint_string_subset'):self.run_binding(core=original)
 def test_duplicate_original_element_refuses(self):
  core=json.loads(CORE);core['modules'][0]['elements'].append(core['modules'][0]['elements'][0]);original=wire(core)
  with self.assertRaisesRegex(AssociationBindingError,'duplicate_element'):self.run_binding(core=original)
 def test_excessive_source_depth_refuses(self):
  core=json.loads(CORE);value='end'
  for _ in range(34):value=[value]
  core.setdefault('extensions',{})['unknown']=value;original=wire(core)
  with self.assertRaisesRegex(AssociationBindingError,'source_resource'):self.run_binding(core=original)
 def test_lone_escaped_surrogate_refuses(self):
  original=CORE.replace(b'"id":"domain"',b'"id":"\\ud800"',1)
  self.assertNotEqual(original,CORE)
  with self.assertRaisesRegex(AssociationBindingError,'source_unicode'):prepare_association_binding(original,ONTOLOGY,wire(inputs()))
 def test_oversized_source_refuses(self):
  with self.assertRaisesRegex(AssociationBindingError,'original_bytes'):prepare_association_binding(b' '*1048577,ONTOLOGY,wire(inputs()))
 def test_malformed_source_shapes_refuse(self):
  core=json.loads(CORE);core['modules']=[True];original=wire(core)
  binding=inputs();binding['coreSha256']=sha256(original).hexdigest()
  with self.assertRaisesRegex(AssociationBindingError,'source_shape'):self.run_binding(binding,original,ONTOLOGY)
 def test_unknown_extreme_number_tokens_are_retained_exactly(self):
  for number in ['1e999999999999999999999','1e-999999999999999999999','9'*5000]:
   core=json.loads(CORE);core.setdefault('extensions',{})['unknown']='TOKEN';original=wire(core).replace(b'"TOKEN"',number.encode());binding=inputs();binding['coreSha256']=sha256(original).hexdigest();basis=self.run_binding(binding,original,ONTOLOGY);self.assertEqual(basis.core_bytes,original)
if __name__=='__main__':unittest.main()
