# SPDX-License-Identifier: MIT OR Apache-2.0
"""Actual public scalar/capture/UMF transport; supplied source wrapper, no admission."""
import base64,copy,json,os,struct,hashlib,unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
from truss._current_disclosure_facts import capture_current_disclosure_facts_with_cursor
from truss._current_query_pipe import CurrentQueryPipe
from truss import Error,Ok
from truss.contracts import MapValue
from truss.groups import CreateObject,AuthoredValue,RootlessOwnership,GroupSuccess,GroupFailed
import test_current_disclosure_graphs_native as graph

ref=lambda name:{'documentId':'adoc','moduleId':'m','elementId':name}
VALUES={
 'RA':{'salary':{'integerToken':'9007199254740993'},'codecDecimal':{'decimalToken':'123456789012345678901234.2300'},'codecBytes':{'binaryHex':'00ff'},'codecUnicode':{'string':'e\u0301🙂'},'codecFlag':{'boolean':True},'codecOptional':None},
 'RB':{'salary':{'integerToken':'9223372036854775807'},'codecDecimal':{'decimalToken':'-0.0000'},'codecBytes':{'binaryHex':''},'codecUnicode':{'string':'é🙂'},'codecFlag':{'boolean':False}},
 'RO':{'salary':{'integerToken':'-9223372036854775808'},'codecDecimal':{'decimalToken':'1.0001'},'codecBytes':{'binaryHex':'cafe00babe'},'codecUnicode':{'string':''},'codecFlag':{'boolean':True},'codecOptional':{'string':''}},
}
FIELDS=[('codecDecimal','decimal','required',{'precision':28,'scale':4}),('codecBytes','binary','required',{}),
        ('codecUnicode','string','required',{}),('codecFlag','boolean','required',{}),('codecOptional','string','absent-allowed',{})]

def codec_fixture():
 corpus=copy.deepcopy(graph.PACKETS);initial=corpus['initialize'];source=initial['sources']
 module=source['closure']['documents'][0]['document']['modules'][0]
 resource=next(e for e in module['elements'] if e['id']=='Resource')
 resource['keys'][0]['fields']=[{'module':'m','element':'resourceId'},{'module':'m','element':'codecBytes'}]
 next(e for e in module['elements'] if e['id']=='salary')['facets']={'integerWidth':{'bits':64,'signed':True}}
 entity=next(e for e in source['ontology']['entities'] if e['type']==ref('Resource'))
 for name,family,availability,facets in FIELDS:
  module['elements'].append({'id':name,'name':name,'kind':'field','scalarType':family,'nullability':availability,'cardinality':'one','facets':facets,'extensions':{}})
  resource['members'].append({'module':'m','element':name})
  entity['fields'].append({'ref':ref(name),'protection':'unprotected'})
  initial['owner']['storage'].append({'type':ref('Resource'),'field':ref(name),'storageEffect':'canonical'})
  initial['selection']['fields'].append(ref(name))
 for packet in corpus['packets']:
  for fact in packet['cut']['facts']:
   if fact['type']!=ref('Resource'):continue
   key=fact['key'][0]['string'];values=VALUES[key]
   fact['key']=[{'string':key},values['codecBytes']]
   next(c for c in fact['fields'] if c['field']==ref('salary'))['value']=values['salary']
   for name,_,_,_ in FIELDS:
    if name in values:fact['fields'].append({'field':ref(name),'value':values[name]})
    else:fact['absent'].append(ref(name))
  for edge in packet['cut']['graphs']:
   if edge['relationship']['relationshipId']=='OwnershipResource':
    endpoint=next(e for e in edge['endpoints'] if e['role']=='target');key=endpoint['key'][0]['string']
    endpoint['key']=[{'string':key},VALUES[key]['codecBytes']]
 return corpus

@unittest.skipUnless(graph._ENABLED,'requires explicit isolated graph/codec native campaign')
class NativeScalarCodecTests(graph.NativeGraphCaptureTests):
 for name in tuple(n for n in dir(graph.NativeGraphCaptureTests) if n.startswith('test_')):locals()[name]=None
 def test_public_exact_scalar_capture_and_original_disclosure(self):
  corpus=codec_fixture()
  with patch.object(graph,'PACKETS',corpus):self._run_population(False)
  out=Path(os.environ['TRUSS_GRAPH_CAPTURE_EVIDENCE'])
  captured=json.loads((out/'native-inputs-base/facts.json').read_bytes())
  resources={f['key'][0]['string']:f for f in captured if f['type']==ref('Resource')}
  self.assertEqual(set(resources),set(VALUES))
  for key,values in VALUES.items():
   actual={f['field']['elementId']:f['value'] for f in resources[key]['fields']}
   self.assertEqual(resources[key]['key'],[{'string':key},values['codecBytes']])
   self.assertEqual(actual,{'resourceId':{'string':key},**values})
   self.assertEqual(resources[key]['absent'],[] if 'codecOptional' in values else [ref('codecOptional')])
  result=json.loads((out/'native-graph-capture-base-result.json').read_bytes())
  fields=[f['elementId'] for f in corpus['initialize']['selection']['fields']]
  for observation in result['observations']:
   subject=observation['subject'];batch=observation['decision']['batch']
   self.assertEqual([c['field']['elementId'] for c in batch['columns']],fields)
   key={'Alice':'RA','Bob':'RB'}.get(subject)
   if key is None:self.assertEqual(batch['rows'],[]);continue
   values={'resourceId':{'string':key},**VALUES[key]}
   expected=[{'disposition':'original','value':values[f]} if f in values else {'disposition':'absent'} for f in fields]
   self.assertEqual(batch['rows'],[expected])
  negative=self._negative_controls(out,corpus)
  (out/'codec-correspondence.json').write_text(json.dumps({'scope':'Public exact native scalar/capture/original semantic renderer; supplied source wrapper, no native graph/query admission','expectedValues':VALUES,'families':['string','boolean','integer','decimal','binary'],'resourceKeyFields':['resourceId','codecBytes'],'integerWidth':{'bits':64,'signed':True},'decimalFacets':{'precision':28,'scale':4},'optionalStates':['present-null','absent','present-empty-string'],'fixtureUsesPythonFloat':False,'observations':result['observations'],'negativeControls':negative},ensure_ascii=True,indent=2)+'\n')

 def _negative_controls(self,out,corpus):
  original=out/'native-inputs-base'
  initial=json.loads((original/'initialize.json').read_bytes())
  assessment=(original/'assessment.json').read_bytes()
  supplied=SimpleNamespace(source_profile='truss-current-disclosure-sources/0.1-candidate',initialize_bytes=graph.wire(initial),accepted_request_bytes=(original/'accepted-request.json').read_bytes(),accepted_assessment_bytes=assessment)
  inventory=json.loads(assessment)['inventory'];type_id=next(t['type_id'] for t in inventory['types'] if t['element']=='Resource')
  properties={p['element']:p['prop_id'] for p in inventory['properties'] if p['type_id']==type_id and p['retired_rev'] is None}
  self.admin.execute('BEGIN');cursor=graph.NativeCursor(self.admin)
  from truss._security_catalog_assessment import SOURCE_TABLES
  self.admin.execute('LOCK TABLE '+','.join('ONLY truss.'+name for name in SOURCE_TABLES)+' IN SHARE MODE NOWAIT')
  row=self.admin.execute("SELECT id FROM ONLY truss.object WHERE type_id=%s AND props->%s->>'text'='RO'",(type_id,str(properties['resourceId']))).fetchone()
  self.assertIsNotNone(row);controls=[]
  def capture():
   with patch('truss._current_disclosure_facts.capture_current_query_sources_with_cursor',return_value=supplied):
    return capture_current_disclosure_facts_with_cursor(cursor,bun_executable=os.environ['TRUSS_BUN_EXECUTABLE'])
  baseline=capture()
  for label,field,cell,stage in [
   ('integer-width','salary',{'kind':'integer','text':'9223372036854775808'},'semantic'),
   ('integer-underflow','salary',{'kind':'integer','text':'-9223372036854775809'},'semantic'),
   ('decimal-precision','codecDecimal',{'kind':'decimal','text':'1234567890123456789012345.0001'},'semantic'),
   ('decimal-scale','codecDecimal',{'kind':'decimal','text':'0.00001'},'semantic'),
   ('binary-base64','codecBytes',{'kind':'binary','text':'?'},'base64'),
   ('boolean-number','codecFlag',{'kind':'boolean','value':1},'Exact native scalar fact cell'),
   ('required-null','codecFlag',{'kind':'null'},'Required fact Field null')]:
   self.admin.execute('SAVEPOINT codec_control')
   self.admin.execute('UPDATE truss.object SET props=pg_catalog.jsonb_set(props,ARRAY[%s],%s::jsonb) WHERE id=%s',(str(properties[field]),json.dumps(cell),row[0]))
   if stage=='semantic':
    captured=capture();cut=copy.deepcopy(corpus['packets'][0]['cut'])
    cut.update(facts=json.loads(captured.facts_bytes),coverage=json.loads(captured.coverage_bytes),graphs=json.loads(captured.graphs_bytes),graphCoverage=json.loads(captured.graph_coverage_bytes),domains=initial['sources']['closure']['pins'])
    raw=graph.wire(initial);receipt=hashlib.sha256(struct.pack('>I',len(raw))+raw).hexdigest()
    with CurrentQueryPipe((os.environ['TRUSS_BUN_EXECUTABLE'],os.environ['TRUSS_GRAPH_CAPTURE_UMF_CHILD']),timeout_seconds=20) as child:
     self.assertEqual(json.loads(child.exchange(raw,source_receipt=receipt))['kind'],'initialized')
     reply=json.loads(child.exchange(graph.wire({'version':initial['version'],'kind':'evaluate-disclosure','requestId':'evaluate','sourceReceipt':receipt,'cut':cut}),source_receipt=receipt))
     self.assertEqual(reply['kind'],'disclosure-evaluated');result=reply['result']
     self.assertEqual(result['status'],'refused');self.assertEqual(result['resources'],[]);self.assertEqual(result['decisions'],[]);self.assertIsNone(result['batch'])
    self.assertTrue(child._cleanup_complete)
    controls.append({'control':label,'stage':'original-UMF-global-domain-refusal','ownerlessCorruptedResource':'RO','subject':'Alice','result':result})
   else:
    with self.assertRaisesRegex(ValueError,stage):capture()
    controls.append({'control':label,'stage':'native-cell-capture-refusal','messagePattern':stage})
   self.admin.execute('ROLLBACK TO SAVEPOINT codec_control');self.admin.execute('RELEASE SAVEPOINT codec_control')
   self.assertEqual(capture(),baseline)
  self.admin.rollback()
  (out/'codec-domain-and-decoder-controls.json').write_text(json.dumps(controls,indent=2)+'\n')
  # Exercise the public writer's explicit NUL limitation separately.
  before=self.admin.execute('SELECT id,type_id,ver,props::text FROM truss.object ORDER BY id').fetchall()
  connection,host,assembly,transaction=self.consumer();context=assembly.group_context_in_transaction(transaction).value
  values={'resourceId':{'string':'R-NUL'},**VALUES['RA']};values['codecUnicode']={'string':'a\0b'}
  operation=CreateObject(type_definition_pin=self.types[('adoc','Resource')].definition_pin,values=tuple(AuthoredValue(name=name,value=graph.native_literal(value)) for name,value in values.items()),ownership=RootlessOwnership(),alias='nul')
  response=assembly.apply_in_transaction(transaction,context.input((operation,),MapValue(entries=())),context.request('codec-nul'),documents=self.documents,bun_executable=os.environ['TRUSS_BUN_EXECUTABLE'])
  self.assertFalse(isinstance(response,Ok) and isinstance(response.value,GroupSuccess),'NUL must not silently normalize or store')
  self.assertIsInstance(response,Ok);self.assertIsInstance(response.value,GroupFailed)
  self.assertEqual(response.value.failure.code,'invalid')
  diagnostic=json.loads(base64.b64decode(response.value.failure.diagnostic.bytes_base64,validate=True))
  self.assertEqual(diagnostic,{'code':'invalid_input','outcome':'failed','nativeState':'22023','operationIndex':'0'})
  host.detach();connection.commit()
  self.assertEqual(self.admin.execute('SELECT id,type_id,ver,props::text FROM truss.object ORDER BY id').fetchall(),before)
  controls.append({'control':'public-string-NUL','stage':'native-create-input-refusal','nativeDiagnostic':diagnostic,'canonicalObjectRowsUnchangedAfterCommit':True})
  return controls

if __name__=='__main__':unittest.main()
