"""Committed registered-source capture and one retained compiler context.

Native fixture Subject/binding are diagnostic; no ordinary-caller admission.
"""
import hashlib,json,os,unittest
from pathlib import Path
from types import SimpleNamespace
from truss import Ok,Error,adopt_psycopg_host,register_current_disclosure_sources_in_transaction,prepare_current_disclosure_originals
from truss._current_disclosure_context_capture import capture_context_disclosure_with_cursor,verify_context_disclosure_with_cursor
from truss._current_disclosure_evaluation import evaluate_and_stage_current_disclosure
import test_current_disclosure_graphs_native as graph
wire=graph.wire
ROOT=Path(__file__).resolve().parents[3]/'docs/helix/04-build/evidence/actual-graph-requirements-20261016'

@unittest.skipUnless(os.environ.get('TRUSS_CONTEXT_DISCLOSURE_NATIVE_QUALIFICATION')=='1','explicit serialized context capture qualification required')
class ContextDisclosureNativeTests(graph.NativeGraphCaptureTests):
 for name in tuple(n for n in dir(graph.NativeGraphCaptureTests) if n.startswith('test_')):locals()[name]=None
 def test_registered_full_population_same_context_and_original_inspector(self):
  # Existing diagnostic setup creates the original14 objects and12 edges. It
  # rolls back its observation transaction; subsequent capture uses no mocks.
  self._run_population(False)
  out=Path(os.environ['TRUSS_GRAPH_CAPTURE_EVIDENCE']);base=out/'native-inputs-base'
  initial=json.loads((base/'initialize.json').read_bytes());accepted=(base/'accepted-request.json').read_bytes()
  request=json.loads((ROOT/'original-request.json').read_bytes());request['modules']=json.loads(accepted)['modules']
  for m in request['modules']:m['selectedModuleIds']=['m']
  for row in request['opaqueSources']:
   role=row['role']
   if role in ('policy','ontology','catalog','owner'):
    source=initial['owner'] if role=='owner' else initial['sources'][role]
    row['utf8']=wire(source).decode();row['sha256']=hashlib.sha256(row['utf8'].encode()).hexdigest();row['identity']={'documentId':source.get('id',source.get('documentId')),'revision':source['revision']}
  designation=next(r for r in request['opaqueSources'] if r['role']=='presence-designation');profile=json.loads(designation['utf8'])
  profile['modelPins']=[m['pin'] for m in request['modules']];profile['sources']=[{k:r[k] for k in ('role','identity','sha256')} for r in request['opaqueSources'] if r['role'] in ('policy','ontology','catalog','owner')]
  designation['utf8']=wire(profile).decode();designation['sha256']=hashlib.sha256(designation['utf8'].encode()).hexdigest()
  registered=wire({'kind':'initialize','requestId':'registered','sources':{**initial['sources'],'extensionSelection':None}})
  originals=prepare_current_disclosure_originals(wire(request['opaqueSources']))
  self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin,operation_timeout_ms=60000);self.tx=self.host.adopt_transaction().value
  result=register_current_disclosure_sources_in_transaction(self.host,self.tx,initialize_bytes=registered,accepted_request_bytes=accepted,disclosure_originals=originals)
  self.assertIsInstance(result,Ok,str(self.host._custody.last_attempt.error));self.host.detach();self.admin.commit()
  self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin,operation_timeout_ms=60000);self.tx=self.host.adopt_transaction().value
  bun=os.environ['TRUSS_BUN_EXECUTABLE']
  def capture(cursor,actual):return capture_context_disclosure_with_cursor(cursor,sql='SELECT r.salary FROM Resource r',parameters={},document_ids=('adoc',),bun_executable=bun)
  result=self.host._run_operation(self.tx,capture);self.assertIsInstance(result,Ok,str(self.host._custody.last_attempt.error));captured=result.value
  self.assertEqual(len(captured.facts.rows),14);self.assertEqual(len(captured.facts.graph_rows),12)
  self.assertEqual(captured.sources.query_originals,originals);self.assertEqual(captured.sources.initialize_bytes,registered)
  def evaluate(cursor,actual):return evaluate_and_stage_current_disclosure(cursor,captured,SimpleNamespace(key='Alice'),sql='SELECT r.salary FROM Resource r',parameters={},document_ids=('adoc',),bun_executable=bun,maximum_rows=4096,maximum_scan_rows=4096,maximum_bytes=8_000_000)
  result=self.host._run_operation(self.tx,evaluate);self.assertIsInstance(result,Ok,str(self.host._custody.last_attempt.error));evaluated=result.value
  self.assertIs(evaluated.current,captured.definitions.model.current);self.assertIs(evaluated.parent,captured.definitions.model.parent);evaluated.require_original_parent()
  batch=json.loads(evaluated.staged.reconstructed_batch);self.assertEqual(batch['rows'],[[{'disposition':'original','value':{'integerToken':'100'}}]])
  def close(cursor,actual):verify_context_disclosure_with_cursor(cursor,captured,bun_executable=bun);return True
  self.assertIsInstance(self.host._run_operation(self.tx,close),Ok)
  self.admin.execute('SAVEPOINT context_closing');self.admin.execute('UPDATE truss.edge SET ver=ver+1 WHERE id=%s',(captured.facts.graph_rows[0][0],))
  refused=self.host._run_operation(self.tx,close);self.assertIsInstance(refused,Error);self.assertIn('changed before closing',str(self.host._custody.last_attempt.error))
  self.admin.execute('ROLLBACK TO SAVEPOINT context_closing');self.admin.execute('RELEASE SAVEPOINT context_closing');self.assertIsInstance(self.host._run_operation(self.tx,close),Ok)
  for name,raw in [('registered-initialize.json',registered),('registered-opaque-sources.json',originals.opaque_sources_bytes),('registered-consumer.json',originals.consumer_bytes),('context-graph-requirements.json',captured.definitions.requirements),('context-definition-report.json',captured.definitions.report),('context-model-report.json',captured.definitions.model.report),('context-facts.json',captured.facts_bytes),('context-graphs.json',captured.graphs_bytes),('context-coverage.json',captured.coverage_bytes),('context-graph-coverage.json',captured.graph_coverage_bytes),('context-rendered-batch.json',evaluated.staged.reconstructed_batch)]:
   (out/name).write_bytes(raw)
  observation=captured.definitions.model.observation
  for name,raw in [('context-native-accepted-request.json',observation.accepted_request),('context-native-accepted-assessment.json',observation.accepted_assessment),('context-native-inventory.json',observation.native_inventory),('context-native-release.json',observation.runtime_release),('context-model-requirements.json',captured.definitions.model.requirements),('context-preparation.json',captured.definitions.model.current.json().encode())]:
   (out/name).write_bytes(raw)
  (out/'context-native-locators.json').write_bytes(wire({'objects':[[*r[:3],*[b.hex() for b in r[3:]]] for r in captured.facts.rows],'edges':captured.facts.graph_rows}))
  (out/'context-controls.json').write_bytes(wire({'registeredSourceProviderSubstitution':False,'priorSetupUsesDiagnosticWrapper':True,'facts':14,'graphs':12,'sameCurrentObjectThroughStageAndInspector':True,'sameParentObject':True,'closingSuccesses':2,'edgeVersionClosingRefusal':True,'Subject':'diagnostic fixture Alice','authority':False,'nativeAdmission':False,'guardedRelease':False}))
