"""Complete native binary row images on original UMF-exported tables; no semantic guard."""
import hashlib,importlib.metadata,json,sys,tempfile
from pathlib import Path
from urllib.parse import urlparse,parse_qs
import pg8000.native,pg8000.exceptions,pgserver
import struct
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
if len(sys.argv)!=2 or Path(sys.argv[1]).name!=sys.argv[1] or not sys.argv[1].endswith('.json'):raise SystemExit('Fresh receipt basename required')
out=HERE/sys.argv[1]
if out.exists():raise SystemExit('Receipt exists')
if importlib.metadata.version('pgserver')!='0.1.4+truss.pg16.15' or importlib.metadata.version('pg8000')!='1.31.5':raise SystemExit('Pinned runtime required')
paths=['docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql','docs/helix/04-build/evidence/design-audit/row-image-codec-preflight-source.owner-export.sql','packages/postgresql/native/row-image/codec.sql']
frozen={p:(ROOT/p).read_bytes() for p in paths};checks=[];connection=None
with tempfile.TemporaryDirectory(prefix='truss-row-image-') as directory:
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
  connection.run(frozen[paths[1]].decode())
  def frame(kind,cells):
   result=('truss.row-image.'+kind+'/0.1').encode()+b'\0'+struct.pack('!i',len(cells))
   for oid,raw in cells:
    result+=struct.pack('!Ii',oid,-1 if raw is None else len(raw))+(b'' if raw is None else raw)
   return result
  def i8(v):return struct.pack('!q',v)
  def i4(v):return struct.pack('!i',v)
  def t(v):return None if v is None else v.encode('utf8')
  state=[(20,i8(501)),(25,b'object'),(20,i8(100)),(23,i4(1)),(20,None),(23,None),(23,i4(1)),(23,i4(101)),(20,i8(601)),(17,b'\x01'),(17,b'\x02'),(17,b'\x03'),(17,b'\x04')]
  node=[(20,i8(501)),(20,i8(601)),(20,None),(25,b'root'),(20,None),(25,None),(17,None),(25,b'scalar'),(17,b'\x05'),(17,b'\x06')]
  scalar=[(20,i8(501)),(20,i8(601)),(25,b'string'),(25,b'object-value'),(16,None),(1700,None),(25,None),(17,None),(25,None),(1184,None),(17,None),(17,b'\x07'),(17,b'\x08')]
  for kind,table,expected in [('state','row_home_state',state),('node','row_home_node',node),('scalar','row_home_scalar',scalar)]:
   original=connection.run('SELECT truss.row_image_'+kind+'_original(v) FROM truss.'+table+' v WHERE state_id=501')[0][0]
   if original!=frame(kind,expected):raise ValueError('Complete original stored image mismatch')
   checks.append({'id':'complete-stored-'+kind,'cells':len(expected),'originalHex':original.hex(),'independentByteEquality':True})
   vector='ARRAY['+','.join('NULL' if raw is None else str(len(raw)) for _,raw in expected)+']::integer[]'
   measured=connection.run("SELECT truss.row_image_size_original('"+kind+"',"+vector+")")[0][0]
   if measured!=len(original):raise ValueError('Original preflight size parity mismatch')
   checks.append({'id':'length-parity-'+kind,'bytes':measured})
  # Constructed native scalar composites exercise payload fidelity only; their
  # source/codec labels do not establish valid logical values or event authority.
  scalar_types=[20,20,25,25,16,1700,25,17,25,1184,17,17,17]
  numeric=struct.pack('!hhhh',6,4,0,4)+struct.pack('!6h',1234,5678,9012,3456,7890,1234)
  samples=[('string',"'string', 'é'::text,NULL::bool,NULL::numeric,NULL::text,NULL::bytea,NULL::text,NULL::timestamptz,NULL::bytea",[b'string',t('é'),None,None,None,None,None,None,None]),
   ('false',"'boolean',NULL::text,false,NULL::numeric,NULL::text,NULL::bytea,NULL::text,NULL::timestamptz,NULL::bytea",[b'boolean',None,b'\0',None,None,None,None,None,None]),
   ('decimal',"'decimal',NULL::text,NULL::bool,12345678901234567890.1234::numeric,'0012345678901234567890.1234'::text,NULL::bytea,NULL::text,NULL::timestamptz,NULL::bytea",[b'decimal',None,None,numeric,b'0012345678901234567890.1234',None,None,None,None]),
   ('empty-binary',"'binary',NULL::text,NULL::bool,NULL::numeric,NULL::text,decode('','hex'),NULL::text,NULL::timestamptz,NULL::bytea",[b'binary',None,None,None,None,b'',None,None,None]),
   ('temporal',"'timestamp',NULL::text,NULL::bool,NULL::numeric,NULL::text,NULL::bytea,'1999-12-31 19:00:00-05'::text,'2000-01-01 00:00:00+00'::timestamptz,NULL::bytea",[b'timestamp',None,None,None,None,None,b'1999-12-31 19:00:00-05',i8(0),None]),
   ('lexical-only-temporal',"'timestamp',NULL::text,NULL::bool,NULL::numeric,NULL::text,NULL::bytea,'original lexical carrier'::text,NULL::timestamptz,NULL::bytea",[b'timestamp',None,None,None,None,None,b'original lexical carrier',None,None]),
   ('opaque',"'opaque',NULL::text,NULL::bool,NULL::numeric,NULL::text,NULL::bytea,NULL::text,NULL::timestamptz,decode('00ff80','hex')",[b'opaque',None,None,None,None,None,None,None,b'\0\xff\x80'])]
  for name,sql,values in samples:
   original=connection.run("SELECT truss.row_image_scalar_original(ROW(501::bigint,601::bigint,"+sql+",decode('07','hex'),decode('08','hex'))::truss.row_home_scalar)")[0][0]
   expected=frame('scalar',list(zip(scalar_types,[i8(501),i8(601),*values,b'\x07',b'\x08'])))
   if original!=expected:raise ValueError('Independent native scalar binary payload mismatch')
   checks.append({'id':'scalar-'+name,'originalHex':original.hex(),'independentByteEquality':True})
  def refusal(name,call,expected):
   try:connection.run(call)
   except pg8000.exceptions.DatabaseError as error:
    if error.args[0]['C']!=expected:raise
    checks.append({'id':name,'sqlstate':expected})
   else:raise ValueError('Expected native refusal')
  for kind,table in [('state','row_home_state'),('node','row_home_node'),('scalar','row_home_scalar')]:
   refusal('null-'+kind,'SELECT truss.row_image_'+kind+'_original(NULL::truss.'+table+')','22023')
  refusal('unknown-kind',"SELECT truss.row_image_columns_original('other')",'22023')
  for name,alter in [('extra-column','ALTER TABLE truss.row_home_scalar ADD COLUMN extra text'),
                     ('collation-change','ALTER TABLE truss.row_home_scalar ALTER COLUMN scalar_kind TYPE text COLLATE pg_catalog."default"'),
                     ('nullable-change','ALTER TABLE truss.row_home_scalar ALTER COLUMN scalar_kind DROP NOT NULL')]:
   connection.run('BEGIN');connection.run('SAVEPOINT original_profile')
   connection.run(alter)
   refusal(name,"SELECT truss.row_image_columns_original('scalar')",'55000')
   connection.run('ROLLBACK TO SAVEPOINT original_profile');connection.run('RELEASE SAVEPOINT original_profile');connection.run('ROLLBACK')
   connection.run("SELECT truss.row_image_columns_original('scalar')")
  refusal('null-lengths',"SELECT truss.row_image_size_original('scalar',NULL)",'22023')
  refusal('wrong-length-count',"SELECT truss.row_image_size_original('scalar',ARRAY[0])",'22023')
  refusal('negative-length',"SELECT truss.row_image_size_original('scalar',ARRAY[-1,0,0,0,0,0,0,0,0,0,0,0,0])",'22023')
  refusal('two-dimensional-lengths',"SELECT truss.row_image_size_original('scalar',array_fill(0,ARRAY[1,13]))",'22023')
  empty=scalar.copy();empty[3]=(25,b'')
  count=8388608-len(frame('scalar',empty))
  large_sql="SELECT truss.row_image_scalar_original(ROW(501::bigint,601::bigint,'string'::text,repeat('a',CAST(:count AS integer)),NULL::bool,NULL::numeric,NULL::text,NULL::bytea,NULL::text,NULL::timestamptz,NULL::bytea,decode('07','hex'),decode('08','hex'))::truss.row_home_scalar)"
  original=connection.run(large_sql,count=count)[0][0];empty[3]=(25,b'a'*count)
  if original!=frame('scalar',empty) or len(original)!=8388608:raise ValueError('Exact image output ceiling mismatch')
  checks.append({'id':'exact-eight-mib-image','bytes':len(original),'sha256':hashlib.sha256(original).hexdigest(),'fullIndependentByteEquality':True})
  try:connection.run(large_sql,count=count+1)
  except pg8000.exceptions.DatabaseError as error:
   if error.args[0]['C']!='54000':raise
   checks.append({'id':'one-byte-over-image-refusal','sqlstate':'54000'})
  else:raise ValueError('Expected preflight output overflow refusal')
  connection.run('CREATE ROLE image_actor');connection.run('GRANT USAGE ON SCHEMA truss TO image_actor');connection.run('SET ROLE image_actor')
  for kind,table in [('state','row_home_state'),('node','row_home_node'),('scalar','row_home_scalar')]:
   refusal('ordinary-private-'+kind,'SELECT truss.row_image_'+kind+'_original(NULL::truss.'+table+')','42501')
  refusal('ordinary-private-column-validator',"SELECT truss.row_image_columns_original('scalar')",'42501')
  refusal('ordinary-private-size',"SELECT truss.row_image_size_original('scalar',array_fill(0,ARRAY[13]))",'42501')
  connection.run('RESET ROLE')
 finally:
  if connection is not None:connection.close()
  server.cleanup()
if any((ROOT/p).read_bytes()!=raw for p,raw in frozen.items()):raise ValueError('Source drift')
receipt={'scope':'actual private native state/node/scalar binary codecs and exact length preflight against independent complete field/OID/null/byte payload expectations; original UMF-exported tables and codec','serverVersion':version,'observations':checks,'sourceSha256':{p:hashlib.sha256(v).hexdigest() for p,v in frozen.items()},'producerSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'rowTouchObserverQualified':False,'acceptanceCasesPromoted':[],'limitations':['Stored administrative fixture plus constructed native scalar composites; no protected OLD/NEW/prestate producer','Native binary values qualify finite PostgreSQL16.15 datum correspondence, not portable UMF value semantics','Complete output length checked before record serialization; numeric cell length measurement and full pre-materialization/detoast/copy/work/heap/deadline qualification remain independent','Current profile/DDL/native callable dependency and full role/ACL closure missing','No complete association/family/current authority or seven-body realization']}
with out.open('x') as f:f.write(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'observations':len(checks),'rowTouchObserverQualified':False}))
