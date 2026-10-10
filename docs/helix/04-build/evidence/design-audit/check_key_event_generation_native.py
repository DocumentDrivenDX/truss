"""Compose actual cascades with the existing private operation generation trigger."""
import hashlib,importlib.metadata,json,sys,tempfile,struct
from pathlib import Path
from urllib.parse import urlparse,parse_qs
import pg8000.native,pgserver
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
if len(sys.argv)!=2 or Path(sys.argv[1]).name!=sys.argv[1] or not sys.argv[1].endswith('.json'):raise SystemExit('Fresh receipt basename required')
out=HERE/sys.argv[1]
if out.exists():raise SystemExit('Receipt exists')
if importlib.metadata.version('pgserver')!='0.1.4+truss.pg16.15' or importlib.metadata.version('pg8000')!='1.31.5':raise SystemExit('Pinned runtime required')
paths=['docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql','docs/helix/04-build/evidence/design-audit/row-event-image-attribution-probe.sql','docs/helix/04-build/evidence/design-audit/row-image-codec-preflight-source.owner-export.sql','packages/python/src/truss/_row_image.py','packages/python/src/truss/_row_event_attribution.py']
paths += ['packages/postgresql/native/operation-generation-observer.sql']
frozen={p:(ROOT/p).read_bytes() for p in paths};checks=[];connection=None
sys.path.insert(0,str(ROOT/'packages/python/src'))
from truss._row_image import decode_row_image
from truss._row_event_attribution import attribute_row_event
with tempfile.TemporaryDirectory(prefix='truss-row-cascade-') as directory:
 server=pgserver.get_server(Path(directory)/'data',cleanup_mode='stop')
 try:
  uri=urlparse(server.get_uri());opts=parse_qs(uri.query);host=opts.get('host',[uri.hostname])[0];port=int(opts.get('port',[uri.port or 5432])[0])
  connection=pg8000.native.Connection(user='postgres',database='postgres',unix_sock=str(Path(host)/f'.s.PGSQL.{port}'),ssl_context=False,timeout=30)
  version=connection.run('SHOW server_version')[0][0]
  if version!='16.15':raise ValueError('Native version mismatch')
  connection.run(frozen[paths[0]].decode())
  connection.run('BEGIN')
  connection.run('INSERT INTO truss.schema_rev(rev) VALUES(1)')
  connection.run("INSERT INTO truss.schema_doc VALUES(1,0,'fixture','1','fixture',repeat('0',64),'{}','{}')")
  for type_id in (1,2,3):
   connection.run("INSERT INTO truss.type_def(document_id,type_id,module,element,kind,since_rev,doc_ord,lineage_profile,lineage_bytes,definition_source_kind,definition_rev,definition_doc_ord,definition_document_id) VALUES('fixture',CAST(:id AS integer),'m','T'||CAST(CAST(:id AS integer) AS text),'record',1,0,'fixture',decode('01','hex'),'accepted_document',1,0,'fixture')",id=type_id)
  for prop,type_id in ((101,1),(301,3)):
   connection.run("INSERT INTO truss.prop_def(prop_id,type_id,element,name,nullability,cardinality,home,since_rev,doc_ord,declaration_module,definition_source_kind,definition_rev,definition_doc_ord,definition_document_id) VALUES(:prop,:type,'p','p','required','one','row',1,0,'m','accepted_document',1,0,'fixture')",prop=prop,type=type_id)
  connection.run('INSERT INTO truss.object(id,type_id,rev) VALUES(100,1,1),(200,2,1)')
  connection.run("INSERT INTO truss.rel_def(document_id,rel_type_id,module,rel_id,name,source_min,target_min,lifecycle,directed,assoc_type_id,since_rev,doc_ord,definition_source_kind,definition_rev,definition_doc_ord,definition_document_id) VALUES('fixture',10,'m','r','r',0,0,'manual',true,3,1,0,'accepted_document',1,0,'fixture')")
  connection.run('INSERT INTO truss.rel_endpoint VALUES(10,1,2)')
  connection.run('INSERT INTO truss.edge(id,rel_type_id,source_id,source_type,target_id,target_type,rev) VALUES(100,10,100,1,200,2,1)')
  connection.run("INSERT INTO truss.row_home_state(state_id,owner_kind,object_id,object_type_id,edge_id,relationship_type_id,property_owner_type_id,property_id,root_node_id,definition_bytes,home_profile_bytes,value_profile_bytes,source_bytes) VALUES(501,'object',100,1,NULL,NULL,1,101,601,decode('01','hex'),decode('02','hex'),decode('03','hex'),decode('04','hex')),(502,'edge',NULL,NULL,100,10,3,301,602,decode('01','hex'),decode('02','hex'),decode('03','hex'),decode('04','hex'))")
  connection.run("INSERT INTO truss.row_home_node(state_id,node_id,slot_kind,value_kind,definition_bytes,source_bytes) VALUES(501,601,'root','scalar',decode('05','hex'),decode('06','hex')),(502,602,'root','scalar',decode('05','hex'),decode('06','hex'))")
  connection.run("INSERT INTO truss.row_home_scalar(state_id,node_id,scalar_kind,text_value,codec_definition_bytes,original_source_bytes) VALUES(501,601,'string','object-value',decode('07','hex'),decode('08','hex')),(502,602,'string','edge-value',decode('07','hex'),decode('08','hex'))")
  connection.run('SET CONSTRAINTS ALL IMMEDIATE');connection.run('COMMIT')
  connection.run("INSERT INTO truss.key_def(type_id,key_id,key_num,prop_ids,is_primary,since_rev,definition_source_kind,definition_rev,definition_doc_ord,definition_document_id) VALUES(1,'fixture-key',1,ARRAY[101],true,1,'accepted_document',1,0,'fixture')")
  connection.run(frozen[paths[-1]].decode())
  connection.run('BEGIN');xid=connection.run('SELECT pg_current_xact_id()::text')[0][0]
  connection.run("INSERT INTO truss.row_home_operation VALUES(pg_current_xact_id_if_assigned(),7,'mutation','row_sealed',0,0,0,NULL,decode('01','hex'),decode('02','hex'),decode('03','hex'),decode('04','hex'),decode('05','hex'),decode('06','hex'),decode('07','hex'),NULL)")
  connection.run("INSERT INTO truss.key_bucket_guard VALUES(sha256(decode('61','hex')),sha256(decode('6b','hex')),0),(sha256(decode('62','hex')),sha256(decode('6b','hex')),0)")
  connection.run('SAVEPOINT all_effects')
  def state(name,expected,generation):
   # Hash sort is not lexical namespace sort; select exact routes independently.
   actual=[connection.run("SELECT generation::text FROM truss.key_bucket_guard WHERE namespace_sha256=sha256(decode(:hex,'hex'))",hex=h)[0][0] for h in ('61','62')]
   operation=connection.run('SELECT phase,effect_generation::text,readiness_generation::text,sealed_generation::text,application_generation::text,application_result_bytes FROM truss.row_home_operation')
   if actual!=list(map(str,expected)) or operation!=[['admitted',str(generation),None,None,None,None]]:raise ValueError(name+': original guard/operation mismatch')
   checks.append({'id':name,'routeGenerations':actual,'originalOperationCells':operation})
  for table,rowid,offset in [('object_key_bucket',701,0),('object_key_reservation_bucket',702,4)]:
   if table=='object_key_bucket':
    sql="INSERT INTO truss.object_key_bucket(storage_row_id,type_id,key_num,object_id,namespace_bytes,key_bytes,original_context_bytes) VALUES(701,1,1,100,decode('61','hex'),decode('6b','hex'),decode('01','hex'))"
   else:sql="INSERT INTO truss.object_key_reservation_bucket(storage_row_id,namespace_bytes,key_bytes,original_reservation_bytes) VALUES(702,decode('61','hex'),decode('6b','hex'),decode('01','hex'))"
   connection.run(sql);state(table+'-insert',(1+3*(offset//4),2*(offset//4)),offset+1)
   column='original_context_bytes' if table=='object_key_bucket' else 'original_reservation_bytes'
   connection.run('UPDATE truss.'+table+" SET "+column+"=decode('02','hex') WHERE storage_row_id=:id",id=rowid)
   state(table+'-same-route-update-deduplicated',(2+3*(offset//4),2*(offset//4)),offset+2)
   connection.run('UPDATE truss.'+table+" SET namespace_bytes=decode('62','hex') WHERE storage_row_id=:id",id=rowid)
   state(table+'-route-move-invalidates-both',(3+3*(offset//4),1+2*(offset//4)),offset+3)
   connection.run('DELETE FROM truss.'+table+' WHERE storage_row_id=:id',id=rowid)
   state(table+'-delete',(3+3*(offset//4),2+2*(offset//4)),offset+4)
  connection.run('SAVEPOINT guard_exhaustion')
  connection.run("UPDATE truss.key_bucket_guard SET generation=9223372036854775807 WHERE namespace_sha256=sha256(decode('62','hex'))")
  try:connection.run("INSERT INTO truss.object_key_reservation_bucket(storage_row_id,namespace_bytes,key_bytes,original_reservation_bytes) VALUES(703,decode('62','hex'),decode('6b','hex'),decode('01','hex'))")
  except pg8000.exceptions.DatabaseError as error:
   if error.args[0].get('C')!='54000':raise
  else:raise ValueError('Expected exhausted guard refusal')
  connection.run('ROLLBACK TO SAVEPOINT guard_exhaustion');connection.run('RELEASE SAVEPOINT guard_exhaustion')
  state('exhausted-guard-refusal-restores-operation-and-routes',(6,4),8)
  if connection.run('SELECT count(*) FROM truss.object_key_reservation_bucket')!=[[0]]:raise ValueError('Refused reservation survived')
  connection.run('ROLLBACK TO SAVEPOINT all_effects');connection.run('RELEASE SAVEPOINT all_effects')
  if connection.run('SELECT generation::text FROM truss.key_bucket_guard ORDER BY namespace_sha256')!=[['0'],['0']] or connection.run('SELECT phase,effect_generation::text,readiness_generation::text,sealed_generation::text FROM truss.row_home_operation')!=[['row_sealed','0','0','0']]:raise ValueError('Whole key operation restoration failed')
  if connection.run('SELECT pg_current_xact_id()::text')!=[[xid]]:raise ValueError('Original xid changed')
  checks.append({'id':'confirmed-original-guard-operation-restoration','routeGenerations':['0','0'],'writerXid':xid})
  connection.run('ROLLBACK')
 finally:
  if connection is not None:connection.close()
  server.cleanup()
if any((ROOT/p).read_bytes()!=raw for p,raw in frozen.items()):raise ValueError('Source drift')
receipt={'scope':'actual native key/reservation route generation invalidation and operation proof reset/refusal/rollback; original UMF-exported tables/codecs, administrative fixture','serverVersion':version,'observations':checks,'sourceSha256':{p:hashlib.sha256(v).hexdigest() for p,v in frozen.items()},'producerSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'rowTouchObserverQualified':False,'acceptanceCasesPromoted':[],'limitations':['Exact namespace/key bytes are administrative fixture values, not independently admitted logical key derivation','Administrative catalog and operation registry writes do not qualify protected admission or current authority','Finite two-route key/reservation fixture; no digest-collision, concurrency or complete original event custody qualification','Actual key/reservation INSERT/UPDATE/DELETE generation component only; no complete logical key derivation, protected custody, touch/capacity or native role/DDL closure','Finite PostgreSQL16.15 fixture, not all cascade/reparenting/type/deployment profiles']}
with out.open('x') as f:f.write(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'observations':len(checks),'rowTouchObserverQualified':False}))
