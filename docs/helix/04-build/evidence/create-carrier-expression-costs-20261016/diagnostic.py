import hashlib,json,subprocess,time,unittest
from pathlib import Path
from truss._group_runtime import _bytes,_wire
from truss.catalog_runtime import _release
from truss.contracts import MapValue
import test_group_capacity_native as base
OUT=Path('/private/tmp/truss-create-carrier-costs-report-20261016.json')
report={'scope':'Read-only expression diagnostic on one genuinely admitted original1024-operation carrier, rolled back without effects/finish/commit. Materialized decoded payload models selected_input; aggregate EXPLAIN plans do not establish PLpgSQL cached-plan or whole workflow costs. No product changes or admission/census removal.','sourceCommit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'statementTimeoutMs':10000,'plans':[]}
def save():OUT.write_text(json.dumps(report,indent=2,default=str)+'\n')
class Carrier(base.GroupCapacityTests):
 def tearDown(self):
  try:super().tearDown();report['fixtureCleanup']='completed'
  finally:save()
 def test_exact_create_carriers(self):
  c,h,a,t=self.ready(document_ids=('adoc',));context=a.group_context_in_transaction(t).value
  semantic=context.input(self.operations(1024),MapValue(entries=()));original=_bytes(_wire(semantic))
  documents=_bytes([{'documentId':d.document_id,'sourceText':d.content.decode('utf8')} for d in self.documents])
  request=_bytes(_wire(context.request('carrier-expression-diagnostic')));manifest,digest,_=_release()
  report.update(inputBytes=len(original),inputSha256=hashlib.sha256(original).hexdigest(),documentBytes=len(documents),documentsSha256=hashlib.sha256(documents).hexdigest(),runtimeManifestSha256=digest)
  h.detach();self.admin.execute('GRANT EXECUTE ON FUNCTION truss.object_group_begin(bytea,bytea,bytea,text,text,bytea,boolean) TO consumer')
  try:
   opened=json.loads(bytes(c.execute('SELECT truss.object_group_begin(%s,%s,%s,%s,%s,%s,%s)',(original,documents,request,manifest['releaseId'],digest,b'[]',False),prepare=False).fetchone()[0]));self.assertEqual(opened['outcome'],'execute',opened);selected=opened['attemptId']
   # Inspection starts after admission; no later native writes or finalization.
   self.admin.execute('GRANT SELECT ON truss.runtime_object_attempt TO consumer')
   stored=c.execute('SELECT input_bytes,documents_bytes,next_index FROM truss.runtime_object_attempt WHERE id=%s',(selected,)).fetchone();self.assertEqual(bytes(stored[0]),original);self.assertEqual(bytes(stored[1]),documents);self.assertEqual(stored[2],0)
   report['originalCarrierMatched']=True
   payload="WITH payload AS MATERIALIZED (SELECT convert_from(input_bytes,'UTF8')::jsonb input,documents_bytes documents FROM truss.runtime_object_attempt WHERE id=%s) "
   current="(input-ARRAY['preconditions','operations'])||jsonb_build_object('operations',jsonb_build_array(jsonb_extract_path(input,'operations',i::text)))"
   control="base||jsonb_build_object('operations',jsonb_build_array(jsonb_extract_path(input,'operations',i::text)))"
   equality=payload+", prepared AS MATERIALIZED (SELECT input,input-ARRAY['preconditions','operations'] base FROM payload) SELECT count(*),bool_and(("+current+") IS NOT NULL AND ("+control+") IS NOT NULL AND convert_to(("+current+")::text,'UTF8')=convert_to(("+control+")::text,'UTF8')),sum(octet_length(convert_to(("+current+")::text,'UTF8'))) FROM prepared CROSS JOIN generate_series(0,1023) i"
   count,equal,total=c.execute(equality,(selected,),prepare=False).fetchone();self.assertEqual((count,equal),(1024,True));report['derivedBytesEquality']={'operations':count,'allIdentical':equal,'totalLeafBytes':int(total)}
   queries={
    'derive_each':payload+"SELECT sum(octet_length(convert_to(("+current+")::text,'UTF8'))) FROM payload CROSS JOIN generate_series(0,1023) i",
    'precomputed_base_control':payload+", prepared AS MATERIALIZED (SELECT input,input-ARRAY['preconditions','operations'] base FROM payload) SELECT sum(octet_length(convert_to(("+control+")::text,'UTF8'))) FROM prepared CROSS JOIN generate_series(0,1023) i",
    'documents_unique_json':payload+"SELECT sum(CASE WHEN (convert_from(documents,'UTF8') IS JSON ARRAY WITH UNIQUE KEYS) THEN 1 ELSE 0 END) FROM payload CROSS JOIN generate_series(0,1023) i",
    'documents_jsonb_decode':payload+"SELECT sum(pg_column_size(convert_from(documents,'UTF8')::jsonb)) FROM payload CROSS JOIN generate_series(0,1023) i"}
   for repeat in range(3):
    order=list(queries);order=order if repeat%2==0 else list(reversed(order))
    for name in order:
     started=time.monotonic();plan=c.execute('EXPLAIN (ANALYZE,BUFFERS,VERBOSE,FORMAT JSON) '+queries[name],(selected,),prepare=False).fetchone()[0]
     report['plans'].append({'repeat':repeat,'name':name,'clientElapsedMs':(time.monotonic()-started)*1000,'sql':queries[name],'explain':plan});save()
   report['result']='All1024derivedbytesidentical; three alternating expression samples each captured'
  finally:c.rollback();report['callerRollback']='completed';save()
if __name__=='__main__':unittest.main(defaultTest='Carrier.test_exact_create_carriers',verbosity=2)
