"""Original UMF-exported touch/reset effects; supplied fixture custody is not authority."""
import copy,hashlib,importlib.metadata,json,socket,sys,tempfile
from pathlib import Path
from urllib.parse import urlparse,parse_qs
import pg8000.core,pgserver
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
sys.path.insert(0,str(ROOT/'packages/python/src'));sys.path.insert(0,str(ROOT/'packages/python/tests'))
from truss._accounted_receive import AccountedReceiver
from truss._resource_account import BytePermitAccount
from truss._row_image import decode_row_image
from truss._row_event_attribution import attribute_row_event
from truss._row_operation_custody import decode_row_operation_custody
from truss._row_operation_address import encode_row_operation_address
from truss._operation_registry import COLUMNS
from truss._row_touch_registry import COLUMNS as TOUCH_COLUMNS, decode_touch_registry
from pg8000_accounted_instance_candidate import AccountedSocket
from pg8000_original_control_candidate import OriginalControlConnection
from test_row_operation_custody import fixture
if len(sys.argv)!=2 or Path(sys.argv[1]).name!=sys.argv[1] or not sys.argv[1].endswith('.json'):raise SystemExit('Fresh receipt basename required')
out=HERE/sys.argv[1]
if out.exists():raise SystemExit('Receipt exists')
if importlib.metadata.version('pgserver')!='0.1.4+truss.pg16.15' or importlib.metadata.version('pg8000')!='1.31.5':raise SystemExit('Pinned runtime required')
if hashlib.sha256(Path(pg8000.core.__file__).read_bytes()).hexdigest()!='cac1e50502901bcea3ddab588e0350149dd8fd771156ae1c531a2a04b3925e26':raise SystemExit('Pinned driver source required')
paths=['docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql',
 'docs/helix/04-build/evidence/design-audit/row-touch-create-and-seal.owner-export.sql',
 'docs/helix/04-build/evidence/design-audit/row-touch-generation-advance.owner-export.sql',
 'docs/helix/04-build/evidence/design-audit/row-operation-generation-reset.owner-export.sql',
 'docs/helix/04-build/evidence/design-audit/row-event-attribution-conflict-native.json']
paths += [str(p.relative_to(ROOT)) for p in sorted((ROOT/'packages/python/src/truss').glob('*.py'))]
paths += ['packages/python/tests/test_row_operation_custody.py']
paths += ['docs/helix/04-build/evidence/design-audit/'+p for p in ['pg8000_original_control_candidate.py','pg8000_instance_candidate.py','pg8000_accounted_instance_candidate.py','python_pg_receive_candidate.py','python_pg_frame_candidate.py']]
paths += ['docs/helix/04-build/evidence/design-audit/row-touch-current-writer-observation.owner-export.sql']
paths += ['docs/helix/04-build/evidence/design-audit/row-touch-current-writer-cohort.owner-export.sql']
frozen={p:(ROOT/p).read_bytes() for p in paths}
lookup=frozen[paths[-2]].decode()
cohort_query=frozen[paths[-1]].decode()
create,seal=[s.strip() for s in frozen[paths[1]].decode().split(';') if s.strip()]
advance=frozen[paths[2]].decode();reset=frozen[paths[3]].decode()
images=tuple(decode_row_image(bytes.fromhex(v['originalImageHex'])) for v in json.loads(frozen[paths[4]])['observations'] if 'originalImageHex' in v)
scalars=[image for image in images if image.kind=='scalar' and bytes(image.payload(0))==(501).to_bytes(8,'big')]
if len(images)!=6 or len(scalars)!=1:raise ValueError('Original native image vector membership mismatch')
owner=attribute_row_event('DELETE',scalars[0],None,images,(),6,100000).old_owner
owner_args=(owner.kind,owner.owner_id,owner.discriminator_id,owner.property_owner_type_id,owner.property_id)
checks=[];captures=[];connection=None;supplied=None
with tempfile.TemporaryDirectory(prefix='truss-touch-transition-') as directory:
 server=pgserver.get_server(Path(directory)/'data',cleanup_mode='stop')
 try:
  uri=urlparse(server.get_uri());opts=parse_qs(uri.query);host=opts.get('host',[uri.hostname])[0];port=int(opts.get('port',[uri.port or 5432])[0])
  transport=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);transport.settimeout(10);transport.connect(str(Path(host)/f'.s.PGSQL.{port}'))
  producer=object();account=BytePermitAccount(producer,134217728,268435456,16384);supplied=AccountedSocket(transport,account,producer)
  supplied.file.receiver=AccountedReceiver(transport,account,producer,frame_bytes=1048576,total_bytes=33554432,messages=1024,reads=100000)
  supplied.file.remaining_writes=1024;supplied.file.remaining_send_bytes=16777216
  connection=OriginalControlConnection(user='postgres',database='postgres',sock=supplied,ssl_context=False,startup_params={'client_encoding':'UTF8'})
  version=connection.parameter_statuses['server_version']
  if version!='16.15':raise ValueError('Native version mismatch')
  def cells(result):return [[None if v is None else v.decode('ascii') for v in row] for row in result.rows]
  connection.execute_simple(frozen[paths[0]].decode())
  connection.execute_simple('BEGIN')
  if cells(connection.execute_simple('SELECT pg_current_xact_id_if_assigned()::text'))!=[[None]]:raise ValueError('Unassigned original xid required')
  def execute(name,sql,args,expected):
   start=len(connection.original_controls);result=connection.execute_unnamed(sql,vals=args)
   raw=cells(result)
   if raw!=expected or result.row_count!=len(expected) or connection._ready_status!=b'T':raise ValueError(name+': complete native effect mismatch')
   names=tuple(c.name.decode('ascii') for c in result.columns)
   expected_names=COLUMNS if sql==reset else ('transaction_id','owner_kind','owner_id','owner_discriminator_id','property_owner_type_id','property_id','dirty_generation','sealed_generation','original_layout_bytes_hex','original_home_bytes_hex','original_owner_property_bytes_hex','original_operation_bytes_hex')
   if names!=expected_names or any(c.type_oid!=25 or c.format!=0 for c in result.columns):raise ValueError('Complete original text descriptor required')
   frames=connection.original_controls[start:]
   tag=(('INSERT 0 ' if sql==create else 'UPDATE ')+str(len(expected))).encode()+b'\0'
   expected_frame=b'C'+(len(tag)+4).to_bytes(4,'big')+tag
   if [f for f in frames if f[:1]==b'C']!=[expected_frame] or frames[-1]!=b'Z\0\0\0\5T':raise ValueError('Complete original command/ready frames required')
   captures.append({'id':name,'columns':[c.name.decode('ascii') for c in result.columns],'rows':raw,'commandReadyFramesHex':[f.hex() for f in connection.original_controls[start:]]})
   checks.append({'id':name,'affectedRows':len(expected),'fullReturnedCellsMatch':True})
  def observe(name,args,expected,actual_xid):
   start=len(connection.original_controls);result=connection.execute_unnamed(lookup,vals=args)
   raw=cells(result);names=tuple(c.name.decode('ascii') for c in result.columns)
   if raw!=expected or names!=TOUCH_COLUMNS or result.row_count!=len(expected) or any(c.type_oid!=25 or c.format!=0 for c in result.columns):raise ValueError('Original point lookup cells/descriptor mismatch')
   frames=connection.original_controls[start:];tag=('SELECT '+str(len(expected))).encode()+b'\0'
   if [v for v in frames if v[:1]==b'C']!=[b'C'+(len(tag)+4).to_bytes(4,'big')+tag] or frames[-1]!=b'Z\0\0\0\5T':raise ValueError('Original point lookup control mismatch')
   decoded=decode_touch_registry('fixture',actual_xid,names,raw,'SELECT',str(result.row_count),1,100000)
   if tuple(row.cells for row in decoded)!=tuple(tuple(row) for row in expected):raise ValueError('Decoded original complete cells mismatch')
   captures.append({'id':name,'columns':list(names),'rows':raw,'commandReadyFramesHex':[v.hex() for v in frames]})
   checks.append({'id':name,'originalRows':len(decoded),'fullDecodedCellsMatch':True,'scope':'selected current-writer tuple only; not complete cohort or authority-qualified absence'})
  def observe_cohort(name,expected,actual_xid):
   start=len(connection.original_controls);result=connection.execute_unnamed(cohort_query,vals=())
   raw=cells(result);names=tuple(c.name.decode('ascii') for c in result.columns)
   if raw!=expected or names!=TOUCH_COLUMNS or result.row_count!=len(expected) or any(c.type_oid!=25 or c.format!=0 for c in result.columns):raise ValueError('Original cohort cells/descriptor mismatch')
   frames=connection.original_controls[start:];tag=('SELECT '+str(len(expected))).encode()+b'\0'
   if [v for v in frames if v[:1]==b'C']!=[b'C'+(len(tag)+4).to_bytes(4,'big')+tag] or frames[-1]!=b'Z\0\0\0\5T':raise ValueError('Original cohort control mismatch')
   decoded=decode_touch_registry('fixture',actual_xid,names,raw,'SELECT',str(result.row_count),2,100000)
   if tuple(v.cells for v in decoded)!=tuple(map(tuple,expected)):raise ValueError('Original cohort decoding mismatch')
   captures.append({'id':name,'columns':list(names),'rows':raw,'commandReadyFramesHex':[v.hex() for v in frames]})
   checks.append({'id':name,'originalRows':len(decoded),'fullDecodedCellsMatch':True,'scope':'complete finite administrative current-writer fixture; protected visibility/cut/authority external'})
  # No original assigned transaction: first-touch source must return zero, not
  # allocate an xid or silently supply a default/current operation.
  execute('unassigned-first-touch-zero-refusal',create,(*owner_args,'\\x01','\\x02','\\x03','\\x04'),[])
  if cells(connection.execute_simple('SELECT pg_current_xact_id_if_assigned()::text'))!=[[None]]:raise ValueError('First-touch predicate assigned xid')
  observe('unassigned-point-lookup-does-not-assign-xid',owner_args,[],'0')
  if cells(connection.execute_simple('SELECT pg_current_xact_id_if_assigned()::text'))!=[[None]]:raise ValueError('Lookup assigned xid')
  observe_cohort('unassigned-complete-cohort-read',[],'0')
  if cells(connection.execute_simple('SELECT pg_current_xact_id_if_assigned()::text'))!=[[None]]:raise ValueError('Cohort lookup assigned xid')
  checks.append({'id':'unassigned-observation-preserved'})
  xid=cells(connection.execute_simple('SELECT pg_current_xact_id()::text'))[0][0]
  value=fixture(2)
  for entry,ordinal in zip(value['operations'],('7','11')):
   entry['operationIdentity']=entry['nativeGroupCustodyIdentity']=encode_row_operation_address('fixture',xid,ordinal).decode()
  next_body=decode_row_operation_custody(json.dumps(value).encode())
  first=copy.deepcopy(value);first['operations']=first['operations'][:1]
  prior_body=decode_row_operation_custody(json.dumps(first).encode())
  layout,home,property_bytes=prior_body.layout.original,prior_body.home.original,prior_body.owner_property.original
  custody=(layout,home,property_bytes)
  hex_arg=lambda b:'\\x'+b.hex()
  def touch(dirty,sealed,manifest):return [[xid,*owner_args,dirty,sealed,*[v.hex() for v in custody],manifest.hex()]]
  connection.execute_simple('SAVEPOINT original_touch')
  # Administrative phase/context fixture only. Original carriers stay opaque;
  # these labels do not establish OC admission, readiness or family semantics.
  connection.execute_simple("INSERT INTO truss.row_home_operation VALUES(pg_current_xact_id_if_assigned(),7,'mutation','row_sealed',0,0,0,NULL,decode('01','hex'),decode('02','hex'),decode('03','hex'),decode('04','hex'),decode('05','hex'),decode('06','hex'),decode('07','hex'),NULL)")
  operation=[[xid,'7','mutation','admitted','1',None,None,None,'01','02','03','04','05','06','07',None]]
  execute('original-operation-reset-clears-proofs',reset,('7','0','\\x01'),operation)
  execute('first-touch-complete-originals',create,(*owner_args,*map(hex_arg,custody),hex_arg(prior_body.original)),touch('1',None,prior_body.original))
  observe_cohort('actual-one-touch-complete-cohort',touch('1',None,prior_body.original),xid)
  observe('actual-first-touch-point-read-decode',owner_args,touch('1',None,prior_body.original),xid)
  execute('seal-current-complete-touch',seal,(*owner_args,'1',*map(hex_arg,custody),hex_arg(prior_body.original)),touch('1','1',prior_body.original))
  observe('actual-sealed-touch-point-read-decode',owner_args,touch('1','1',prior_body.original),xid)
  execute('stale-seal-zero-refusal',seal,(*owner_args,'0',*map(hex_arg,custody),hex_arg(prior_body.original)),[])
  connection.execute_simple("UPDATE truss.row_home_operation SET phase='application_finalized',readiness_generation=effect_generation,sealed_generation=effect_generation,application_generation=effect_generation,application_result_bytes=decode('ff','hex') WHERE operation_ordinal=7")
  connection.execute_simple("INSERT INTO truss.row_home_operation VALUES(pg_current_xact_id_if_assigned(),11,'mutation','admitted',0,NULL,NULL,NULL,decode('11','hex'),decode('12','hex'),decode('13','hex'),decode('14','hex'),decode('15','hex'),decode('16','hex'),decode('17','hex'),NULL)")
  execute('next-operation-reset',reset,('11','0','\\x11'),[[xid,'11','mutation','admitted','1',None,None,None,'11','12','13','14','15','16','17',None]])
  args=(*owner_args,'1',*map(hex_arg,custody),hex_arg(prior_body.original),hex_arg(next_body.original))
  execute('advance-retains-complete-next-manifest-clears-seal',advance,args,touch('2',None,next_body.original))
  observe('actual-next-manifest-point-read-decode',owner_args,touch('2',None,next_body.original),xid)
  connection.execute_simple('SAVEPOINT cohort_membership')
  edge_args=('edge',*owner_args[1:])
  edge=[[xid,*edge_args,'1',None,*[v.hex() for v in custody],next_body.original.hex()]]
  execute('second-distinct-owner-kind-touch',create,(*edge_args,*map(hex_arg,custody),hex_arg(next_body.original)),edge)
  connection.execute_simple("UPDATE truss.row_home_touch SET dirty_generation=2,sealed_generation=1 WHERE owner_kind='edge'")
  edge[0][6:8]=['2','1']
  observe_cohort('actual-complete-two-kind-cohort-includes-old-seal',edge+touch('2',None,next_body.original),xid)
  connection.execute_simple('ROLLBACK TO SAVEPOINT cohort_membership');connection.execute_simple('RELEASE SAVEPOINT cohort_membership')
  observe('foreign-owner-point-read-empty-projection',('edge',*owner_args[1:]),[],xid)
  execute('stale-dirty-zero-refusal',advance,args,[])
  wrong=list(args);wrong[5]='2';wrong[6]='\\x00';wrong[9]=hex_arg(next_body.original)
  execute('foreign-layout-zero-refusal',advance,tuple(wrong),[])
  wrong=list(args);wrong[1]='101';wrong[5]='2';wrong[9]=hex_arg(next_body.original)
  execute('foreign-owner-tuple-zero-refusal',advance,tuple(wrong),[])
  execute('foreign-operation-context-zero-refusal',reset,('11','1','\\x00'),[])
  wrong=list(args);wrong[5]='2';wrong[9]='\\x00'
  execute('foreign-prior-manifest-zero-refusal',advance,tuple(wrong),[])
  wrong=list(args);wrong[5]='2';wrong[10]='\\x'
  execute('empty-next-manifest-zero-refusal',advance,tuple(wrong),[])
  execute('finalized-operation-reset-zero-refusal',reset,('7','1','\\x01'),[])
  connection.execute_simple('SAVEPOINT original_overflow')
  connection.execute_simple('UPDATE truss.row_home_touch SET dirty_generation=9223372036854775807,sealed_generation=NULL')
  overflow=list(args);overflow[5]='9223372036854775807';overflow[9]=hex_arg(next_body.original)
  execute('touch-generation-exhaustion-zero-refusal',advance,tuple(overflow),[])
  connection.execute_simple('ROLLBACK TO SAVEPOINT original_overflow');connection.execute_simple('RELEASE SAVEPOINT original_overflow')
  execute('seal-restored-generation-two',seal,(*owner_args,'2',*map(hex_arg,custody),hex_arg(next_body.original)),touch('2','2',next_body.original))
  connection.execute_simple('ROLLBACK TO SAVEPOINT original_touch');connection.execute_simple('RELEASE SAVEPOINT original_touch')
  if cells(connection.execute_simple('SELECT count(*)::text FROM truss.row_home_touch'))!=[['0']] or cells(connection.execute_simple('SELECT count(*)::text FROM truss.row_home_operation'))!=[['0']]:raise ValueError('Touch/operation rollback did not restore originals')
  if cells(connection.execute_simple('SELECT pg_current_xact_id()::text'))!=[[xid]]:raise ValueError('Original xid changed')
  observe_cohort('confirmed-whole-cohort-rollback-empty',[],xid)
  observe('rolled-back-touch-point-read-empty-projection',owner_args,[],xid)
  checks.append({'id':'confirmed-whole-operation-touch-restoration','writerXid':xid,'retainedRows':[0,0]})
  connection.execute_simple('ROLLBACK')
  if connection._ready_status!=b'I':raise ValueError('Original rollback completion missing')
 finally:
  if connection is not None:connection.close()
  if supplied is not None:supplied.close()
  server.cleanup()
if any((ROOT/p).read_bytes()!=raw for p,raw in frozen.items()):raise ValueError('Source drift')
receipt={'scope':'actual original UMF-exported transition effects, point and full current-writer cohort SELECT -> private Python complete-cell decoder through pinned accounted raw pg8000 seam; administrative supplied custody','serverVersion':version,'observations':checks,'originalCaptures':captures,'sourceSha256':{p:hashlib.sha256(v).hexdigest() for p,v in frozen.items()},'producerSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'rowTouchObserverQualified':False,'acceptanceCasesPromoted':[],'limitations':['Tuple derived from retained historical native image vector; not an original current event/complete scope authority producer','Manifest shape/original bytes retained, but no native complete contributor/family/current authority proof','Manual native phase labels/sealing are scheduling fixtures, not application readiness/settlement proof','No head/capacity/guard/reservation or complete role/DDL/callable closure','Zero-row effects are required refusals; no public retry/no-op success classification or engine factory','Receive limits/byte permits do not qualify complete native/host allocation/work/deadline','Point lookup captures a selected tuple; cohort query covers the finite administrative current-writer fixture. Protected visibility/cut/current authority and absence proof remain external','No seven semantic bodies, public API or installed-wheel/interchange qualification']}
with out.open('x') as f:f.write(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'observations':len(checks),'captures':len(captures),'rowTouchObserverQualified':False}))
