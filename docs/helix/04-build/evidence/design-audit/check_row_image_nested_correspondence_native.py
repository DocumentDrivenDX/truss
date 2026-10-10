"""Actual parent visibility during cascades on original UMF-exported tables; no semantic guard."""
import hashlib,importlib.metadata,json,sys,tempfile,struct
from pathlib import Path
from urllib.parse import urlparse,parse_qs
import pg8000.native,pgserver
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
if len(sys.argv)!=2 or Path(sys.argv[1]).name!=sys.argv[1] or not sys.argv[1].endswith('.json'):raise SystemExit('Fresh receipt basename required')
out=HERE/sys.argv[1]
if out.exists():raise SystemExit('Receipt exists')
if importlib.metadata.version('pgserver')!='0.1.4+truss.pg16.15' or importlib.metadata.version('pg8000')!='1.31.5':raise SystemExit('Pinned runtime required')
paths=['docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql','docs/helix/04-build/evidence/design-audit/row-event-image-attribution-probe.sql','docs/helix/04-build/evidence/design-audit/row-image-codec-preflight-source.owner-export.sql','docs/helix/04-build/evidence/design-audit/row-image-prestate.owner-export.sql','packages/postgresql/native/row-image/prestate.sql','docs/helix/02-design/contracts/row-image-prestate-v0.1.proposal.umf.json','docs/helix/04-build/evidence/design-audit/row-image-snapshot-prestate.owner-export.sql','packages/postgresql/native/row-image/snapshot-prestate.sql','packages/python/src/truss/_row_image.py','packages/python/src/truss/_row_event_attribution.py']
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
  connection.run("INSERT INTO truss.row_home_node(state_id,node_id,slot_kind,value_kind,definition_bytes,source_bytes) VALUES(501,601,'root','record',decode('05','hex'),decode('06','hex')),(502,602,'root','sequence',decode('05','hex'),decode('06','hex'))")
  connection.run("INSERT INTO truss.row_home_node(state_id,node_id,parent_node_id,slot_kind,record_field_identity_bytes,map_key,sequence_ordinal,value_kind,definition_bytes,source_bytes) VALUES(501,611,601,'record',decode('0a','hex'),NULL,NULL,'map',decode('05','hex'),decode('06','hex')),(501,612,611,'map',NULL,'list',NULL,'sequence',decode('05','hex'),decode('06','hex')),(501,613,612,'sequence',NULL,NULL,0,'scalar',decode('05','hex'),decode('06','hex')),(501,614,612,'sequence',NULL,NULL,1,'scalar',decode('05','hex'),decode('06','hex'))")
  for node,ordinal,value_kind in ((621,0,'scalar'),(622,1,'scalar'),(623,2,'scalar'),(624,3,'scalar'),(625,4,'null'),(626,5,'scalar')):
   connection.run("INSERT INTO truss.row_home_node(state_id,node_id,parent_node_id,slot_kind,sequence_ordinal,value_kind,definition_bytes,source_bytes) VALUES(502,:n,602,'sequence',:o,:k,decode('05','hex'),decode('06','hex'))",n=node,o=ordinal,k=value_kind)
  connection.run("INSERT INTO truss.row_home_scalar(state_id,node_id,scalar_kind,numeric_value,numeric_token,codec_definition_bytes,original_source_bytes) VALUES(501,613,'integer',9007199254740993,'9007199254740993',decode('07','hex'),decode('08','hex')),(501,614,'decimal',123.0000,'+0001.2300e+02',decode('07','hex'),decode('08','hex'))")
  connection.run("INSERT INTO truss.row_home_scalar(state_id,node_id,scalar_kind,boolean_value,codec_definition_bytes,original_source_bytes) VALUES(502,621,'boolean',false,decode('07','hex'),decode('08','hex'))")
  connection.run("INSERT INTO truss.row_home_scalar(state_id,node_id,scalar_kind,binary_value,codec_definition_bytes,original_source_bytes) VALUES(502,622,'binary',decode('0000ff80','hex'),decode('07','hex'),decode('08','hex'))")
  connection.run("INSERT INTO truss.row_home_scalar(state_id,node_id,scalar_kind,temporal_text,temporal_instant,codec_definition_bytes,original_source_bytes) VALUES(502,623,'timestamp','2030-01-02T03:04:05.123456+05:30','2030-01-02T03:04:05.123456+05:30'::timestamptz,decode('07','hex'),decode('08','hex'))")
  connection.run("INSERT INTO truss.row_home_scalar(state_id,node_id,scalar_kind,opaque_bytes,codec_definition_bytes,original_source_bytes) VALUES(502,624,'opaque',decode('ff000180','hex'),decode('07','hex'),decode('08','hex'))")
  connection.run("INSERT INTO truss.row_home_scalar(state_id,node_id,scalar_kind,text_value,codec_definition_bytes,original_source_bytes) VALUES(502,626,'string','',decode('07','hex'),decode('08','hex'))")
  connection.run('SET CONSTRAINTS ALL IMMEDIATE');connection.run('COMMIT')
  connection.run(frozen[paths[2]].decode())
  connection.run(frozen[paths[3]].decode())
  connection.run(frozen['docs/helix/04-build/evidence/design-audit/row-image-snapshot-prestate.owner-export.sql'].decode())
  connection.run(frozen[paths[1]].decode())
  connection.run('BEGIN ISOLATION LEVEL REPEATABLE READ');xid=connection.run('SELECT pg_current_xact_id()::text')[0][0]
  expected_images=tuple((kind,bytes(row[0])) for kind,table in [('state','row_home_state'),('node','row_home_node'),('scalar','row_home_scalar')] for row in connection.run('SELECT truss.row_image_'+kind+'_original(v) FROM truss.'+table+' v ORDER BY state_id'))
  captures=[]
  for state in (501,502):
   independently_expected=tuple((kind,raw) for kind,raw in expected_images if bytes(decode_row_image(raw).payload(0))==struct.pack('!q',state))
   byte_count=sum(len(raw) for kind,raw in independently_expected)
   actual=connection.run('SELECT * FROM truss.runtime_capture_row_images_snapshot_original(:s,:r,:b)',s=state,r=len(independently_expected),b=byte_count)
   actual=tuple((kind,bytes(raw)) for kind,raw in actual)
   if sorted(actual)!=sorted(independently_expected):raise ValueError('Complete native image mismatch')
   captures.extend(actual)
   checks.append({'id':'complete-bounded-capture-'+str(state),'rows':len(actual),'bytes':byte_count,'images':[[kind,raw.hex()] for kind,raw in actual]})
   for rows,allowance in ((len(actual)-1,byte_count),(len(actual),byte_count-1),(0,0)):
    connection.run('SAVEPOINT bounded_refusal')
    try:connection.run('SELECT * FROM truss.runtime_capture_row_images_snapshot_original(:s,:r,:b)',s=state,r=rows,b=allowance)
    except pg8000.exceptions.DatabaseError as error:
     if error.args[0].get('C')!='54000':raise
     checks.append({'id':'bounded-refusal-'+str(state)+'-'+str(rows)+'-'+str(allowance),'sqlstate':'54000','resultReturned':False})
    else:raise ValueError('Expected bounded refusal')
    connection.run('ROLLBACK TO SAVEPOINT bounded_refusal');connection.run('RELEASE SAVEPOINT bounded_refusal')
  for state,rows,allowance,code in ((999,3,100000,'55000'),(None,3,100000,'22023'),(501,-1,100000,'22023'),(501,3,-1,'22023')):
   connection.run('SAVEPOINT invalid_capture')
   try:connection.run('SELECT * FROM truss.runtime_capture_row_images_snapshot_original(:s,:r,:b)',s=state,r=rows,b=allowance)
   except pg8000.exceptions.DatabaseError as error:
    if error.args[0].get('C')!=code:raise
    checks.append({'id':'invalid-capture-'+str(state)+'-'+str(rows)+'-'+str(allowance),'sqlstate':code})
   else:raise ValueError('Expected invalid capture refusal')
   connection.run('ROLLBACK TO SAVEPOINT invalid_capture');connection.run('RELEASE SAVEPOINT invalid_capture')
  before=tuple(decode_row_image(raw) for kind,raw in captures)
  if len(before)!=21:raise ValueError('Complete original21 prestate images missing')
  connection.run('SAVEPOINT original_cascade')
  connection.run('DELETE FROM truss.edge WHERE id=100')
  connection.run('DELETE FROM truss.object WHERE id=100 AND type_id=1')
  events=connection.run('SELECT relation_name,relation_oid::text,event_kind,writer_xid::text,state_id::text,node_id::text,old_owner_kind,old_owner_id::text,old_discriminator::text,old_property_owner::text,old_property_id::text,live_state,live_node,retained_owner_kind,retained_owner_id::text,retained_discriminator::text,retained_property_owner::text,retained_property_id::text,original_image FROM public.cascade_events ORDER BY state_id,relation_name')
  expected={'501':['object','100','1','1','101'],'502':['edge','100','10','3','301']}
  if len(events)!=21:raise ValueError('Complete21 cascade observations missing')
  for captured in events:
   event,original_image=captured[:-1],captured[-1]
   image=decode_row_image(original_image)
   name,oid,kind,writer,state,node,*remaining=event
   old=remaining[:5];live_state,live_node=remaining[5:7];retained=remaining[7:]
   if kind!='DELETE' or writer!=xid or retained!=expected[state] or live_state is not False:raise ValueError('Original cascade association mismatch')
   if name=='row_home_state':
    if old!=expected[state] or node is not None or live_node is not None:raise ValueError('Original state image mismatch')
   elif name in ('row_home_node','row_home_scalar'):
    if old!=[None]*5 or node not in {'501':('601','611','612','613','614'),'502':('602','621','622','623','624','625','626')}[state] or live_node is not False:raise ValueError('Deleted parent visibility mismatch')
   else:raise ValueError('Unknown observed relation')
   checks.append({'id':state+'/'+name,'actualRelationOid':oid,'originalEvent':event,'originalImageHex':original_image.hex()})
   attributed=attribute_row_event('DELETE',image,None,before,(),21,100000)
   owner=attributed.old_owner
   if [owner.kind,owner.owner_id,owner.discriminator_id,owner.property_owner_type_id,owner.property_id]!=expected[state] or attributed.new_owner is not None or attributed.touch_owners!=(owner,):raise ValueError('Complete original Python event attribution mismatch')
   checks.append({'id':'complete-image-attribution-'+state+'/'+name,'originalByteCorrespondence':True,'ownerProperty':expected[state]})
  native_scalar=[decode_row_image(v[-1]) for v in events if v[0]=='row_home_scalar' and v[4]=='501' and v[5]=='613']
  if len(native_scalar)!=1:raise ValueError('Unique original scalar observation missing')
  missing=tuple(v for v in before if not (v.kind=='state' and bytes(v.payload(0))==struct.pack('!q',501)))
  try:attribute_row_event('DELETE',native_scalar[0],None,missing,(),21,100000)
  except ValueError as error:
   if str(error)!='Original state association missing':raise
   checks.append({'id':'actual-old-image-missing-retained-state-refusal','refused':True})
  else:raise ValueError('Expected missing original state refusal')
  nodes=[v for v in before if v.kind=='node' and bytes(v.payload(0))==struct.pack('!q',501) and bytes(v.payload(1))==struct.pack('!q',613)]
  if len(nodes)!=1:raise ValueError('Unique original node prestate missing')
  node=nodes[0];cell=node.cells[0]
  conflicting=decode_row_image(node.original[:cell.offset]+struct.pack('!q',502)+node.original[cell.offset+8:])
  try:attribute_row_event('DELETE',native_scalar[0],None,(*before,conflicting),(),22,100000)
  except ValueError as error:
   if str(error)!='Original node/state association conflicting':raise
   checks.append({'id':'native-input-projection-conflicting-node-state-refusal','refused':True,'control':'corrupted projection, not a native row or constraint violation'})
  else:raise ValueError('Expected conflicting original node/state refusal')
  actual_scalar=native_scalar[0]
  without_node=tuple(v for v in before if not (v.kind=='node' and bytes(v.payload(0))==struct.pack('!q',501) and bytes(v.payload(1))==struct.pack('!q',613)))
  actual_state=next(v for v in before if v.kind=='state' and bytes(v.payload(0))==struct.pack('!q',501))
  cell=actual_scalar.cells[-1]
  changed_scalar=decode_row_image(actual_scalar.original[:cell.offset]+bytes([actual_scalar.original[cell.offset]^1])+actual_scalar.original[cell.offset+1:])
  changed_prestate=tuple(changed_scalar if v is actual_scalar or v.original==actual_scalar.original else v for v in before)
  for label,retained,limit,message in (
   ('missing-actual-scalar-node',without_node,21,'Original node association missing'),
   ('duplicate-actual-state-image',(*before,actual_state),22,'Original attribution image identity ambiguous'),
   ('changed-retained-scalar-source-byte',changed_prestate,21,'Original event image correspondence missing')):
   try:attribute_row_event('DELETE',actual_scalar,None,retained,(),limit,100000)
   except ValueError as error:
    if str(error)!=message:raise
    checks.append({'id':label,'refused':True,'exactReason':message})
   else:raise ValueError('Expected original-image refusal')
  # Material correspondence boundary: scalar OLD alone carries no owner identity.
  owner_cell=actual_state.cells[2]
  substituted_state=decode_row_image(actual_state.original[:owner_cell.offset]+struct.pack('!q',200)+actual_state.original[owner_cell.offset+8:])
  substituted=tuple(substituted_state if v.original==actual_state.original else v for v in before)
  projected=attribute_row_event('DELETE',actual_scalar,None,substituted,(),21,100000)
  if projected.old_owner.owner_id!='200' or actual_state.original==substituted_state.original:raise ValueError('Original scope counterexample not witnessed')
  checks.append({'id':'retained-state-origin-correspondence-required','counterexampleReproduced':True,'control':'altered host projection, not a native state or admitted original capture','actualNativeOldScalarUnchanged':True,'actualOriginalOwner':'100','projectedSubstitutedOwner':projected.old_owner.owner_id,'completeOriginalCaptureBytesMatch':False,'scopeAuthorityQualified':False})
  if connection.run('SELECT count(*) FROM truss.row_home_state')[0][0]!=0 or connection.run('SELECT count(*) FROM truss.row_home_node')[0][0]!=0 or connection.run('SELECT count(*) FROM truss.row_home_scalar')[0][0]!=0:raise ValueError('Cascade not complete')
  checks.append({'id':'complete-state-node-scalar-cascade','remainingRows':[0,0,0]})
  connection.run('ROLLBACK TO SAVEPOINT original_cascade');connection.run('RELEASE SAVEPOINT original_cascade')
  counts=[connection.run('SELECT count(*) FROM truss.'+name)[0][0] for name in ('row_home_state','row_home_node','row_home_scalar')]
  if counts!=[2,12,7] or connection.run('SELECT count(*) FROM cascade_events')[0][0]!=0:raise ValueError('Rollback failed to restore original state')
  if connection.run('SELECT pg_current_xact_id()::text')[0][0]!=xid:raise ValueError('Original xid changed')
  for state in (501,502):
   restored=tuple((kind,bytes(raw)) for kind,raw in connection.run('SELECT * FROM truss.runtime_capture_row_images_snapshot_original(:s,21,100000)',s=state))
   original=tuple((kind,raw) for kind,raw in captures if bytes(decode_row_image(raw).payload(0))==struct.pack('!q',state))
   if sorted(restored)!=sorted(original):raise ValueError('Restored original images differ')
   checks.append({'id':'restored-native-producer-'+str(state),'originalBytesExact':True})
  checks.append({'id':'confirmed-savepoint-restoration','restoredRows':counts,'writerXid':xid,'eventRows':0})
  connection.run('ROLLBACK')
 finally:
  if connection is not None:connection.close()
  server.cleanup()
if any((ROOT/p).read_bytes()!=raw for p,raw in frozen.items()):raise ValueError('Source drift')
receipt={'scope':'bounded native typed prestate -> complete original native OLD image -> Python byte correspondence during actual cascades; original UMF-exported tables/codecs, administrative fixture','serverVersion':version,'observations':checks,'sourceSha256':{p:hashlib.sha256(v).hexdigest() for p,v in frozen.items()},'producerSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'rowTouchObserverQualified':False,'acceptanceCasesPromoted':[],'limitations':['Probe captures complete native OLD images plus typed association fields; underlying native numeric/temporal logical semantics remain independently admitted','Retained prestate comes from bounded native typed-image component; selected state is administrative fixture input, not independently admitted protected scope/cut/authority. Native repeatable-read snapshot is selected by this fixture; original scope/authority/driver exclusion and same-cut publication facts remain external','Both object and edge IDs100 retain distinct kind/discriminator/property owner; edge discriminator10 is not property owner3','Event-local byte matching does not authenticate retained state origin: an altered host state projection can relabel a matching scalar OLD event. Independent complete original capture/context/scope correspondence must precede attribution','No touch/capacity generation update, native callable role/ACL closure, full resources or seven semantic body realization','Finite PostgreSQL16.15 nested record/map/sequence/null-node fixture with all seven stored scalar families; exact native bytes/tokens only, not logical numeric/temporal/catalog interpretation or all cascade/reparenting/type/deployment profiles']}
with out.open('x') as f:f.write(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'observations':len(checks),'rowTouchObserverQualified':False}))
