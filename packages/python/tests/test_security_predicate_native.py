"""Genuine admitted IR predicates on ordinary-writer populated native graphs.
Not protected SQL admission, caller authentication or complete writer closure.
@covers US-056-AC2
@covers US-056-AC6
"""
import json,os,subprocess,psycopg
from pathlib import Path
from truss import Ok,ModuleAccessGrant,adopt_psycopg_host,create_reference_assembly,CatalogRuntimeConfiguration
from truss.contracts import MapValue,TextValue,BooleanValue,NullValue
from truss.groups import CreateObject,AuthoredValue,RootlessOwnership,RequestNone,GroupSuccess,GroupFailed,UpdateObject,StoredObjectReference,CommittedReceiptReplay
import test_security_accepted_catalog_native as accepted
class NativePredicateTests(accepted.AcceptedCatalogMappingTests):
 for name in tuple(n for n in dir(accepted.AcceptedCatalogMappingTests) if n.startswith('test_')):locals()[name]=None
 def test_native_k3_primitives_and_unknown_existential_witnesses(self):
  from itertools import product
  self.admin.execute('SET LOCAL search_path TO pg_catalog,pg_temp')
  values=(False,None,True)
  def conjunction(a,b):return False if a is False or b is False else None if a is None or b is None else True
  def disjunction(a,b):return True if a is True or b is True else None if a is None or b is None else False
  for a,b in product(values,repeat=2):
   actual=self.admin.execute('SELECT %s::boolean AND %s::boolean,%s::boolean OR %s::boolean,NOT %s::boolean',(a,b,a,b,a)).fetchone()
   self.assertEqual(actual,(conjunction(a,b),disjunction(a,b),None if a is None else not a))
  count=0
  for size in range(5):
   for witnesses in product(values,repeat=size):
    expected=True if True in witnesses else None if None in witnesses else False
    actual=self.admin.execute('SELECT CASE WHEN bool_or(truth IS TRUE) THEN TRUE WHEN bool_or(truth IS NULL) THEN NULL::bool ELSE FALSE END FROM unnest(%s::boolean[]) AS facts(truth)',(list(witnesses),)).fetchone()[0]
    self.assertIs(actual,expected);count+=1
  self.assertEqual(count,121)
  self.assertEqual(self.admin.execute('SELECT EXISTS(SELECT 1 FROM unnest(ARRAY[NULL::boolean]) AS facts(truth) WHERE truth)').fetchone(),(False,))
 def test_original_policy_membership_predicates_match_native_population(self):
  self.population()
 def test_signed64_boundaries_through_ordinary_writer(self):
  self.population(salary=9223372036854775807,second_salary=-9223372036854775808)
 def test_signed64_overflow_refuses_entire_original_group(self):
  self.population(salary=9223372036854775808,refused=True)
 def test_signed64_underflow_refuses_entire_original_group(self):
  self.population(salary=-9223372036854775809,refused=True)
 def test_signed64_updates_refuse_overflow_and_preserve_prior_update(self):
  self.population(update=True)
 def test_nullable_and_absent_projection_from_original_writer(self):
  self.population(nullable=True)
 def test_binary_projection_round_trip_from_original_writer(self):
  self.population(nullable=True,binary_carrier=True)
 def population(self,salary=100,second_salary=200,refused=False,update=False,nullable=False,binary_carrier=False):
  binary=os.environ.get('TRUSS_PREDICATE_SPIKE_BINARY')
  if not binary:raise RuntimeError('Original Weft predicate spike binary required')
  source=None
  if nullable:
   from hashlib import sha256
   source=json.loads(accepted.mapping.FIXTURE.read_text());m=source['modules'][0];doc=json.loads(m['documentJson'])
   salary_field=next(e for e in doc['modules'][0]['elements'] if e['id']=='salary');salary_field['nullability']='absent-allowed'
   if binary_carrier:salary_field['scalarType']='binary';salary_field.pop('facets',None)
   m['documentJson']=json.dumps(doc);m['pin']['sha256']=sha256(m['documentJson'].encode()).hexdigest()
   policy=json.loads(source['policyJson']);policy['rules'][0]['disclosure'][0]['disposition']={'kind':'original'}
   source['policyJson']=json.dumps(policy);profile=json.loads(source['queryProfileJson'])
   source['sql']='SELECT a.\"resourceId\" FROM \"Resource\" a ORDER BY a.\"resourceId\"';source['parameters']={}
   profile['modelPins']=[m['pin']];profile['policySha256']=sha256(source['policyJson'].encode()).hexdigest();source['queryProfileJson']=json.dumps(profile)
  self.accepted(source=source);self.host.detach();self.admin.commit()
  self.admin.execute('CREATE ROLE predicate_reader;CREATE ROLE predicate_writer')
  for role in ('predicate_reader','predicate_writer'):self.addCleanup(self.admin.execute,'DROP OWNED BY '+role+';DROP ROLE '+role)
  self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin);self.tx=self.host.adopt_transaction().value
  assembly=create_reference_assembly(CatalogRuntimeConfiguration(),self.host).value
  self.assertIsInstance(assembly.configure_module_access_in_transaction(self.tx,(ModuleAccessGrant('domain','m','predicate_reader','predicate_writer'),)),Ok)
  self.host.detach();self.admin.commit();self.admin.execute('GRANT predicate_writer TO consumer WITH SET FALSE')
  c,h,a,t=self.consumer();view=a.catalog_view_in_transaction(t,a.catalog_view_request()).value.view
  types={d.reference.authored_identity:d.reference for d in view.definitions if d.reference.kind=='type'}
  self.admin.execute('REVOKE '+self.installation.registrar_role+' FROM consumer')
  rows=[('Staff',{'staffId':'alice'}),('Staff',{'staffId':'bob'}),('Project',{'projectId':'A'}),('Project',{'projectId':'B'}),
   ('Resource',{'resourceId':'ra','salary':salary}),('Resource',{'resourceId':'rb','salary':second_salary}),('Resource',{'resourceId':'orphan','salary':300}),
   ('Ownership',{'ownerId':'oa','ownerResource':'ra','ownerProject':'A'}),('Ownership',{'ownerId':'ob','ownerResource':'rb','ownerProject':'B'}),
   ('Assignment',{'assignmentId':'aa','assignmentStaff':'alice','assignmentProject':'A','active':True}),('Assignment',{'assignmentId':'ab','assignmentStaff':'alice','assignmentProject':'B','active':False}),('Assignment',{'assignmentId':'bb','assignmentStaff':'bob','assignmentProject':'B','active':True})]
  if nullable:
   rows[4][1]['salary']=None;rows[5][1].pop('salary')
   if binary_carrier:rows[6][1]['salary']='AQI='
  operations=[]
  for index,(record,fields) in enumerate(rows):
   values=tuple(AuthoredValue(name=k,value=NullValue() if v is None else BooleanValue(value=v) if type(v) is bool else TextValue(kind='binary' if binary_carrier and k=='salary' else 'integer' if type(v) is int else 'string',text=str(v))) for k,v in fields.items())
   operations.append(CreateObject(type_definition_pin=types[record].definition_pin,values=values,ownership=RootlessOwnership(),alias='row'+str(index)))
  context=a.group_context_in_transaction(t).value
  from truss import CatalogDocument
  request=json.loads(self.reference);documents=tuple(CatalogDocument(m['pin']['documentId'],m['pin']['revision'],m['documentJson'].encode()) for m in request['modules'])
  created=a.apply_in_transaction(t,context.input(tuple(operations),MapValue(entries=())),RequestNone(),documents=documents,bun_executable='/opt/homebrew/bin/bun')
  self.assertIsInstance(created,Ok,str(h._custody.last_attempt.error))
  if refused:
   self.assertIsInstance(created.value,GroupFailed)
   h.detach();c.commit()
   self.assertEqual(self.admin.execute("SELECT count(*) FROM truss.object").fetchone(),(0,));return
  self.assertIsInstance(created.value,GroupSuccess)
  if update:
   identity=created.value.response.semantic.results[4].identity
   c.execute("CREATE TEMP TABLE signed64_prior(value text);INSERT INTO signed64_prior VALUES('kept')")
   previous=salary
   for value,expected in [(9223372036854775807,GroupSuccess),(9223372036854775808,GroupFailed),(-9223372036854775809,GroupFailed),(-9223372036854775808,GroupSuccess)]:
    operation=UpdateObject(target=StoredObjectReference(identity=identity),set=(AuthoredValue(name='salary',value=TextValue(kind='integer',text=str(value))),),unset=())
    update_input=context.input((operation,),MapValue(entries=()))
    update_request=context.request('signed64-final-update') if value==-9223372036854775808 else RequestNone()
    changed=a.apply_in_transaction(t,update_input,update_request,documents=documents,bun_executable='/opt/homebrew/bin/bun')
    self.assertIsInstance(changed,Ok,str(h._custody.last_attempt.error));self.assertIsInstance(changed.value,expected)
    if expected is GroupSuccess:previous=value
    observed=a.get_object_in_transaction(t,document_id='domain',module_id='m',record_id='Resource',object_id=int(identity.id))
    self.assertIsInstance(observed,Ok)
    self.assertEqual(dict(observed.value.object.values)['salary'],TextValue(kind='integer',text=str(previous)))
    self.assertEqual(c.execute('TABLE signed64_prior').fetchall(),[('kept',)])
  h.detach();c.commit();self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(12,))
  if update:
   c,h,a,t=self.consumer()
   replay=a.apply_in_transaction(t,update_input,update_request,documents=documents,bun_executable='/opt/homebrew/bin/bun')
   self.assertIsInstance(replay,Ok);self.assertIsInstance(replay.value.response,CommittedReceiptReplay)
   self.assertEqual(replay.value.response.semantic,changed.value.response.semantic)
   h.detach();c.commit()
  self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin);self.tx=self.host.adopt_transaction().value
  # Only selected concurrent data exclusion, not authentication or same-txn closure.
  self.admin.execute('LOCK TABLE truss.object IN SHARE MODE NOWAIT')
  if nullable:
   owner_response=json.loads(self.original(self.reference.decode()))
   self.assertEqual(owner_response['status'],'prepared',str(owner_response))
  mapped=self.prepare_accepted();self.assertIsInstance(mapped,Ok,str(self.host._custody.last_attempt.error))
  assessment=json.loads(mapped.value.accepted_catalog_assessment);payload={'request':request,'assessment':assessment}
  rendered=subprocess.run([binary],input=json.dumps(payload).encode(),capture_output=True,timeout=30)
  self.assertEqual(rendered.returncode,0,rendered.stderr.decode());output=json.loads(rendered.stdout);self.assertFalse(output['securityReady'])
  ids={r['element']:r['type_id'] for r in assessment['inventory']['types']}
  rule=next(r for r in output['rules'] if r['id']=='membership')
  # Native PREPARE/EXECUTE uses original ordinal slots; values never enter SQL text.
  self.admin.execute('SET LOCAL search_path TO pg_catalog,pg_temp')
  self.admin.execute('SET LOCAL standard_conforming_strings TO on')
  self.admin.execute('PREPARE membership_predicate(boolean) AS SELECT s.id,r.id,('+rule['expression']+') FROM truss.object s CROSS JOIN truss.object r WHERE s.type_id='+str(ids['Staff'])+' AND r.type_id='+str(ids['Resource'])+' ORDER BY s.id,r.id')
  truths=self.admin.execute('EXECUTE membership_predicate(true)').fetchall()
  with psycopg.connect(self.info.connection_uri,autocommit=True,options='-c lock_timeout=150ms -c statement_timeout=1500') as writer:
   with self.assertRaises(psycopg.errors.LockNotAvailable):writer.execute('UPDATE truss.object SET props=props')
  self.assertEqual([row[2] for row in truths],[True,False,False,False,True,False])
  selected=next(e for e in output['eligibility'] if e['action']=='read' and e['target']['elementId']=='Resource')
  projections=','.join('('+r['expression']+') AS '+r['truthColumn'] for r in output['rules'] if r['target']['elementId']=='Resource')
  self.admin.execute('PREPARE eligibility_predicate(boolean) AS SELECT sid,rid,('+selected['decisionExpression']+') FROM (SELECT s.id AS sid,r.id AS rid,'+projections+' FROM truss.object s CROSS JOIN truss.object r WHERE s.type_id='+str(ids['Staff'])+' AND r.type_id='+str(ids['Resource'])+') q ORDER BY sid,rid')
  eligibility=self.admin.execute('EXECUTE eligibility_predicate(true)').fetchall()
  self.assertEqual([r[2] for r in eligibility],['permit','deny','deny','deny','permit','deny'])
  salary_state=next(d['stateExpression'] for d in selected['disclosure'] if d['field']['elementId']=='salary')
  identity_state=next(d['stateExpression'] for d in selected['disclosure'] if d['field']['elementId']=='resourceId')
  if nullable:
   projection=next(d['cellExpression'] for d in selected['disclosure'] if d['field']['elementId']=='salary')
   projected=[r[0] for r in self.admin.execute('SELECT ('+projection+') FROM truss.object r CROSS JOIN (SELECT TRUE::boolean q0,TRUE::boolean q1) q WHERE r.type_id='+str(ids['Resource'])+' ORDER BY r.id').fetchall()]
   self.assertEqual(projected,[{'outcomeId':'original','disposition':'original','value':None},{'outcomeId':'absent','disposition':'absent'},{'outcomeId':'original','disposition':'original','value':{'binaryHex':'0102'} if binary_carrier else {'integerToken':'300'}}])
   directory=os.environ.get('TRUSS_PREDICATE_EVIDENCE_DIR')
   if directory:
    root=Path(directory)/('binary' if binary_carrier else 'nullable');root.mkdir(parents=True,exist_ok=True)
    for name,value in (('nullable-request',request),('nullable-assessment',assessment),('nullable-rendered',output),('nullable-projected',projected)):(root/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n')
   return
  for active,expected in ((True,'withheld'),(False,'not-applicable'),(None,'not-applicable')):
   self.assertEqual(self.admin.execute('SELECT ('+salary_state+'),('+identity_state+') FROM (SELECT %s::boolean AS q0,TRUE AS q1) q',(active,)).fetchone(),(expected,'original' if active is True else 'not-applicable'))
  for element,expected_disposition in (('salary','withheld'),('resourceId','original')):
   projection=next(d['cellExpression'] for d in selected['disclosure'] if d['field']['elementId']==element)
   projected=self.admin.execute('SELECT ('+projection+') FROM truss.object r CROSS JOIN (SELECT TRUE::boolean q0,TRUE::boolean q1) q WHERE r.type_id='+str(ids['Resource'])+' ORDER BY r.id').fetchall()
   self.assertEqual(len(projected),3)
   for (cell,) in projected:
    self.assertEqual(cell['disposition'],expected_disposition)
    self.assertEqual(set(cell),{'outcomeId','disposition'} if expected_disposition=='withheld' else {'outcomeId','disposition','value'})
  # Exercise emitted composition with original reader/require truth positions.
  from itertools import product
  for permit,required in product((False,None,True),repeat=2):
   observed=self.admin.execute('SELECT ('+selected['decisionExpression']+') FROM (SELECT %s::boolean AS q0,%s::boolean AS q1) q',(permit,required)).fetchone()[0]
   expected='indeterminate' if permit is None or required is None else 'permit' if permit and required else 'deny'
   self.assertEqual(observed,expected)


  # Separate selected-group composition controls, not fact/authentication tests.
  from copy import deepcopy
  for reverse in (False,True):
   variant=deepcopy(request);policy_variant=json.loads(variant['policyJson'])
   template=deepcopy(policy_variant['rules'][0]);policy_variant['rules']=[]
   for effect in ('permit','require','forbid'):
    rule_variant=deepcopy(template);rule_variant['id']=effect;rule_variant['effect']=effect
    rule_variant.pop('disclosure',None);policy_variant['rules'].append(rule_variant)
   if reverse:policy_variant['rules'].reverse()
   variant['policyJson']=json.dumps(policy_variant)
   composed=subprocess.run([binary],input=json.dumps({'request':variant,'assessment':assessment}).encode(),capture_output=True,timeout=30)
   self.assertEqual(composed.returncode,0,composed.stderr.decode());packet=json.loads(composed.stdout)
   decision_expression=next(e['decisionExpression'] for e in packet['eligibility'] if e['action']=='read')
   columns={r['id']:r['truthColumn'] for r in packet['rules']}
   for permit,required,forbidden in product((False,None,True),repeat=3):
    actual=self.admin.execute('SELECT ('+decision_expression+') FROM (SELECT %s::boolean AS '+columns['permit']+',%s::boolean AS '+columns['require']+',%s::boolean AS '+columns['forbid']+') q',(permit,required,forbidden)).fetchone()[0]
    expected='indeterminate' if None in (permit,required,forbidden) else 'permit' if permit and required and not forbidden else 'deny'
    self.assertEqual(actual,expected)
  # Native emitted original/withheld precedence and row gating, both rule orders.
  for reverse in (False,True):
   variant=deepcopy(request);policy_variant=json.loads(variant['policyJson']);base=deepcopy(policy_variant['rules'][0])
   original=deepcopy(base);original['id']='original';original['disclosure'][0]['disposition']={'kind':'original'}
   withheld=deepcopy(base);withheld['id']='withheld'
   policy_variant['rules']=[original,withheld]
   if reverse:policy_variant['rules'].reverse()
   variant['policyJson']=json.dumps(policy_variant)
   rendered_states=subprocess.run([binary],input=json.dumps({'request':variant,'assessment':assessment}).encode(),capture_output=True,timeout=30)
   self.assertEqual(rendered_states.returncode,0,rendered_states.stderr.decode());state_packet=json.loads(rendered_states.stdout)
   state_group=next(e for e in state_packet['eligibility'] if e['action']=='read')
   expression=next(d['stateExpression'] for d in state_group['disclosure'] if d['field']['elementId']=='salary')
   columns={r['id']:r['truthColumn'] for r in state_packet['rules']}
   for original_truth,withheld_truth in product((False,None,True),repeat=2):
    actual=self.admin.execute('SELECT ('+expression+') FROM (SELECT %s::boolean AS '+columns['original']+',%s::boolean AS '+columns['withheld']+') q',(original_truth,withheld_truth)).fetchone()[0]
    expected='not-applicable' if original_truth is None or withheld_truth is None or not(original_truth or withheld_truth) else 'withheld' if withheld_truth else 'original'
    self.assertEqual(actual,expected)
  # Transform equivalence uses the original composer, including numeric -0.
  for left,right,conflicting in (('0','-0',False),('1','2',True)):
   variant=deepcopy(request);policy_variant=json.loads(variant['policyJson']);base=deepcopy(policy_variant['rules'][0])
   rules=[]
   for name,token in (('left',left),('right',right)):
    transformed_rule=deepcopy(base);transformed_rule['id']=name
    transformed_rule['disclosure'][0]['disposition']={'kind':'transformed','transform':'constant','version':'0.1.0','field':{'documentId':'domain','moduleId':'m','elementId':'salary'},'value':{'integerToken':token}}
    rules.append(transformed_rule)
   base['id']='withheld';rules.append(base);policy_variant['rules']=rules;variant['policyJson']=json.dumps(policy_variant)
   transport=subprocess.run([binary],input=json.dumps({'request':variant,'assessment':assessment}).encode(),capture_output=True,timeout=30)
   self.assertEqual(transport.returncode,0,transport.stderr.decode());transformed_packet=json.loads(transport.stdout)
   group=next(e for e in transformed_packet['eligibility'] if e['action']=='read')
   field=next(d for d in group['disclosure'] if d['field']['elementId']=='salary')
   self.assertEqual(len(field['transformations']),2)
   self.assertEqual(transformed_packet['parameterTypes'],['jsonb','jsonb'])
   self.admin.execute('PREPARE transformed_cell(jsonb,jsonb) AS SELECT ('+field['cellExpression']+') FROM truss.object r CROSS JOIN (SELECT TRUE::boolean q0,FALSE::boolean q1,FALSE::boolean q2) q WHERE r.type_id='+str(ids['Resource'])+' ORDER BY r.id LIMIT 1')
   arguments=','.join(psycopg.sql.Literal(json.dumps(v)).as_string(self.admin)+'::jsonb' for v in transformed_packet['parameters'])
   projected=self.admin.execute('EXECUTE transformed_cell('+arguments+')').fetchone()[0]
   self.assertEqual(projected,{'outcomeId':'transform0','disposition':'transformed','value':{'integerToken':left}})
   self.admin.execute('DEALLOCATE transformed_cell')
   expected_ids=['transform0','transform1' if conflicting else 'transform0']
   self.assertEqual([t['outcomeId'] for t in field['transformations']],expected_ids)
   self.assertEqual([t['ruleId'] for t in field['transformations']],['left','right'])
   self.admin.execute('PREPARE second_transformed_cell(jsonb,jsonb) AS SELECT ('+field['cellExpression']+') FROM truss.object r CROSS JOIN (SELECT FALSE::boolean q0,TRUE::boolean q1,FALSE::boolean q2) q WHERE r.type_id='+str(ids['Resource'])+' ORDER BY r.id LIMIT 1')
   projected_second=self.admin.execute('EXECUTE second_transformed_cell('+arguments+')').fetchone()[0]
   self.assertEqual(projected_second,{'outcomeId':expected_ids[1],'disposition':'transformed','value':{'integerToken':right}})
   self.admin.execute('DEALLOCATE second_transformed_cell')


   for a,b,w in product((False,None,True),repeat=3):
    state,choice=self.admin.execute('SELECT ('+field['stateExpression']+'),('+field['transformationChoiceExpression']+') FROM (SELECT %s::boolean q0,%s::boolean q1,%s::boolean q2) q',(a,b,w)).fetchone()
    expected='not-applicable' if None in (a,b,w) or not(a or b or w) else 'withheld' if w else 'conflict' if a and b and conflicting else 'transformed'
    self.assertEqual(state,expected)
    self.assertEqual(choice,(0 if a else 1) if state=='transformed' else None)
  # Convert captured native cells, not authored expected rows, to original facts.
  def ref(element):return {'documentId':'domain','moduleId':'m','elementId':element}
  facts=[];by_id={};inventory=assessment['inventory']
  for oid,tid,props in self.admin.execute('SELECT id,type_id,props FROM truss.object ORDER BY id').fetchall():
   typ=next(t['element'] for t in inventory['types'] if t['type_id']==tid)
   properties={str(p['prop_id']):p['element'] for p in inventory['properties'] if p['type_id']==tid}
   def literal(cell):
    if cell['kind']=='boolean':return {'boolean':cell['value']}
    return {('integerToken' if cell['kind']=='integer' else 'string'):cell['text']}
   fields=[{'field':ref(properties[k]),'value':literal(v)} for k,v in props.items()]
   key=next(k for k in inventory['keys'] if k['type_id']==tid and k['key_id']=='pk')
   fact={'type':ref(typ),'key':[literal(props[str(k)]) for k in key['prop_ids']],'fields':fields,'absent':[]}
   facts.append(fact);by_id[oid]=fact
  policy=json.loads(request['policyJson']);ontology=json.loads(request['ontologyJson'])
  coverage=[{'type':ref(t['element']),'complete':True,'fields':[ref(p['element']) for p in inventory['properties'] if p['type_id']==t['type_id']]} for t in inventory['types']]
  comparisons=[]
  for sid,rid,truth in truths:
   cut={'trusted':True,'generation':'fixture','expectedGeneration':'fixture','policyId':policy['id'],'policyRevision':policy['revision'],'ontologyDocumentId':ontology['documentId'],'ontologyRevision':ontology['revision'],'subjects':[by_id[sid]],'facts':facts,'coverage':coverage,'context':[],'maxFacts':100,'maxSteps':100000}
   simulation=subprocess.run([binary],input=json.dumps(dict(payload,cut=cut,evaluationRequest={'action':'read','resources':[by_id[rid]],'output':[]})).encode(),capture_output=True,timeout=30)
   self.assertEqual(simulation.returncode,0,simulation.stderr.decode())
   decisions=json.loads(simulation.stdout)['simulationDecisions']
   self.assertEqual(decisions,['permit'] if truth is True else [])
   decision='permit' if decisions else 'filtered' 
   self.assertEqual(decision,'permit' if truth is True else 'filtered')
   disclosure_run=subprocess.run([binary],input=json.dumps(dict(payload,cut=cut,evaluationRequest={'action':'read','resources':[by_id[rid]],'output':[ref('salary')]})).encode(),capture_output=True,timeout=30)
   self.assertEqual(disclosure_run.returncode,0,disclosure_run.stderr.decode())
   disclosed=json.loads(disclosure_run.stdout)['simulationDisclosures']
   self.assertEqual(disclosed,[[[ref('salary'),'withheld']]] if truth is True else [])
   comparisons.append({'subject':sid,'resource':rid,'nativeTruth':truth,'originalDecision':decision})
  directory=os.environ.get('TRUSS_PREDICATE_EVIDENCE_DIR')
  if directory:
   root=Path(directory);root.mkdir(parents=True,exist_ok=True)
   for name,value in (('request',request),('assessment',assessment),('rendered',output),('native-truths',truths),('native-eligibility',eligibility),('original-simulator-comparisons',comparisons)):(root/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n')
