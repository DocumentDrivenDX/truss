# SPDX-License-Identifier: MIT OR Apache-2.0
"""Actual issued Graph context/native catalog definition correspondence only."""
import hashlib,json,os,unittest
from pathlib import Path
from truss import Ok,Error,CatalogDocument,adopt_psycopg_host
from truss._native_graph_correspondence import capture_native_graph_correspondence_with_cursor
import test_catalog_runtime_native as base
ROOT=Path(__file__).resolve().parents[3]/'docs/helix/04-build/evidence/actual-graph-requirements-20261016'

@unittest.skipUnless(os.environ.get('TRUSS_NATIVE_GRAPH_JOIN_QUALIFICATION')=='1','explicit serialized native Graph correspondence required')
class NativeGraphJoinTests(base.PublicCatalogRuntimeTests):
 for name in tuple(n for n in dir(base.PublicCatalogRuntimeTests) if n.startswith('test_')):locals()[name]=None
 def test_issued_graph_context_maps_actual_catalog_and_edge_columns(self):
  import weft,weft.weft as native
  self.assertEqual(hashlib.sha256(Path(native.__file__).read_bytes()).hexdigest(),'7e6384ddada0f67a45839a222ffb059e04a5de00f6a9281ad811eefacdeffa42')
  original=(ROOT/'original-request.json').read_bytes();module=json.loads(original)['modules'][0];pin=module['pin']
  self.install();connection,host,assembly,transaction=self.consumer()
  prepared=assembly.prepare_catalog((CatalogDocument(pin['documentId'],pin['revision'],module['documentJson'].encode()),),source_version='0.10.0',bun_executable=os.environ['TRUSS_BUN_EXECUTABLE'])
  accepted=assembly.accept_in_transaction(transaction,prepared,request_key='graph-definition-join')
  self.assertIsInstance(accepted,Ok,str(host._custody.last_attempt.error));host.detach();connection.commit()
  accepted_request=json.dumps({'modules':[{'pin':pin,'documentJson':module['documentJson']}]},separators=(',',':')).encode()
  parent=weft.prepare_application_lineage(original.decode());current=parent.prepare_current_presence()
  self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin,operation_timeout_ms=60000);self.tx=self.host.adopt_transaction().value
  def capture(cursor,actual):return capture_native_graph_correspondence_with_cursor(cursor,current=current,accepted_request=accepted_request)
  observed=self.host._run_operation(self.tx,capture)
  self.assertIsInstance(observed,Ok,str(self.host._custody.last_attempt.error));joined=observed.value
  self.assertIs(joined.model.current,current);self.assertIs(joined.model.parent,parent)
  report=json.loads(joined.report);self.assertEqual(len(report['associations']),6)
  expected={'ProjectClient':('Project','Client'),'StaffAssignment':('Staff','Assignment'),'AssignmentProject':('Assignment','Project'),'OwnershipResource':('Ownership','Resource'),'OwnershipProject':('Ownership','Project')}
  types=dict(self.admin.execute('SELECT element,type_id FROM truss.type_def WHERE retired_rev IS NULL').fetchall())
  relationships=dict(self.admin.execute('SELECT rel_id,rel_type_id FROM truss.rel_def WHERE retired_rev IS NULL').fetchall())
  physical=self.admin.execute("SELECT attname,attnum,atttypid::text FROM pg_catalog.pg_attribute WHERE attrelid='truss.edge'::regclass AND attnum>0 AND NOT attisdropped").fetchall();columns={n:{'attnum':i,'typeOid':oid} for n,i,oid in physical}
  for a in report['associations']:
   if a['kind']=='record-members':
    self.assertEqual(a['ownerTypeId'],types['Assignment']);continue
   name=a['reference']['relationshipId'];self.assertEqual(a['relationshipTypeId'],relationships[name])
   self.assertEqual([e['targetTypeId'] for e in a['endpoints']],[types[n] for n in expected[name]])
   self.assertEqual(a['home']['columns'],{n:columns[n] for n in a['home']['columns']})
  self.admin.execute("CREATE TEMP TABLE graph_prior(value text);INSERT INTO graph_prior VALUES('kept')")
  self.admin.execute('SAVEPOINT graph_column');self.admin.execute('ALTER TABLE truss.edge RENAME COLUMN source_type TO source_type_drift')
  refused=self.host._run_operation(self.tx,capture)
  self.assertIsInstance(refused,Error);self.assertIn('Original native object column',str(self.host._custody.last_attempt.error))
  self.assertEqual(self.admin.execute('TABLE graph_prior').fetchall(),[('kept',)])
  self.admin.execute('ROLLBACK TO SAVEPOINT graph_column');self.admin.execute('RELEASE SAVEPOINT graph_column')
  restored=self.host._run_operation(self.tx,capture);self.assertIsInstance(restored,Ok,str(self.host._custody.last_attempt.error));self.assertEqual(restored.value.report,joined.report)
  out=Path(os.environ['TRUSS_NATIVE_GRAPH_JOIN_EVIDENCE']);out.mkdir(exist_ok=True,parents=True)
  observation=joined.model.observation
  for name,raw in [('graph-report.json',joined.report),('graph-requirements.json',joined.requirements),('model-report.json',joined.model.report),('model-requirements.json',joined.model.requirements),('accepted-request.json',observation.accepted_request),('accepted-assessment.json',observation.accepted_assessment),('native-inventory.json',observation.native_inventory),('runtime-release.json',observation.runtime_release)]:
   (out/name).write_bytes(raw)
  (out/'controls.json').write_text(json.dumps({'scope':'Actual graph definition correspondence, no graph populations or release','coreRelationships':5,'recordAssociations':1,'nativeEdgeColumnDriftRefused':True,'originalCallerWorkPreserved':True,'restoredReportMatches':True,'sameOriginalParent':True,'authority':False,'nativeAdmission':False},indent=2)+'\n')
