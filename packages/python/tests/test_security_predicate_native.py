"""Genuine admitted IR predicates on ordinary-writer populated native graphs.
Not protected SQL admission, caller authentication or complete writer closure.
@covers US-056-AC2
@covers US-056-AC6
"""
import json,os,subprocess,psycopg
from pathlib import Path
from truss import Ok,ModuleAccessGrant,adopt_psycopg_host,create_reference_assembly,CatalogRuntimeConfiguration
from truss.contracts import MapValue,TextValue,BooleanValue
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
 def population(self,salary=100,second_salary=200,refused=False,update=False):
  binary=os.environ.get('TRUSS_PREDICATE_SPIKE_BINARY')
  if not binary:raise RuntimeError('Original Weft predicate spike binary required')
  self.accepted();self.host.detach();self.admin.commit()
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
  operations=[]
  for index,(record,fields) in enumerate(rows):
   values=tuple(AuthoredValue(name=k,value=BooleanValue(value=v) if type(v) is bool else TextValue(kind='integer' if type(v) is int else 'string',text=str(v))) for k,v in fields.items())
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
   comparisons.append({'subject':sid,'resource':rid,'nativeTruth':truth,'originalDecision':decision})
  directory=os.environ.get('TRUSS_PREDICATE_EVIDENCE_DIR')
  if directory:
   root=Path(directory);root.mkdir(parents=True,exist_ok=True)
   for name,value in (('request',request),('assessment',assessment),('rendered',output),('native-truths',truths),('native-eligibility',eligibility),('original-simulator-comparisons',comparisons)):(root/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n')
