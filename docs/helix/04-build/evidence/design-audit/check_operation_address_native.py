"""Candidate address scalar spelling against PostgreSQL builtin JSON encoding."""
import hashlib, importlib.metadata, json, sys, tempfile
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import pg8000.native, pg8000.exceptions, pgserver
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[4]
sys.path.insert(0,str(ROOT/'packages/python/src'))
from truss._row_operation_address import DOMAIN, encode_row_operation_address, decode_row_operation_address
if len(sys.argv)!=2 or Path(sys.argv[1]).name!=sys.argv[1] or not sys.argv[1].endswith('.json'): raise SystemExit('Fresh receipt basename required')
out=HERE/sys.argv[1]
if out.exists(): raise SystemExit('Receipt exists')
if importlib.metadata.version('pgserver')!='0.1.4+truss.pg16.15' or importlib.metadata.version('pg8000')!='1.31.5': raise SystemExit('Original local runtime/driver required')
paths=['packages/python/src/truss/_row_operation_address.py','packages/python/src/truss/_acceptance_json.py']; frozen={p:(ROOT/p).read_bytes() for p in paths}
samples=['installation','quotes" and backslash\\','\b\f\n\r\t',''.join(chr(i) for i in range(1,32)),chr(127),'é','\u2028\u2029',''.join(chr(i) for i in (128,2047,2048,55295,57344,65535,65536,1114111))]
checks=[]
with tempfile.TemporaryDirectory(prefix='truss-native-address-') as directory:
 server=pgserver.get_server(Path(directory)/'data',cleanup_mode='stop'); connection=None
 try:
  uri=urlparse(server.get_uri()); opts=parse_qs(uri.query); host=opts.get('host',[uri.hostname])[0]; port=int(opts.get('port',[uri.port or 5432])[0])
  connection=pg8000.native.Connection(user='postgres',database='postgres',unix_sock=str(Path(host)/f'.s.PGSQL.{port}'),ssl_context=False,timeout=5)
  version=connection.run('SHOW server_version')[0][0]
  if version!='16.15': raise ValueError('Native version mismatch')
  connection.run('BEGIN'); xid=connection.run('SELECT pg_current_xact_id()::text')[0][0]
  sql="""SELECT convert_to('[' || array_to_string(ARRAY[
  to_json(CAST(:domain AS text))::text,to_json(CAST(:installation AS text))::text,
  to_json(pg_current_xact_id()::text)::text,to_json(CAST(:ordinal AS text))::text], ',') || ']', 'UTF8')"""
  for i, installation in enumerate(samples):
   ordinal=str(7+4*i)
   native=connection.run(sql,domain=DOMAIN,installation=installation,ordinal=ordinal)[0][0]
   expected=encode_row_operation_address(installation,xid,ordinal)
   if native!=expected: raise ValueError('Native/Python scalar spelling mismatch')
   decoded=decode_row_operation_address(native)
   if (decoded.installation,decoded.writer_xid,decoded.operation_ordinal)!=(installation,xid,ordinal): raise ValueError('Native address projection mismatch')
   checks.append({'id':'scalar-'+str(i),'installationUtf8Hex':installation.encode().hex(),'originalAddressHex':native.hex(),'writerXid':xid,'operationOrdinal':ordinal})
  connection.run('SAVEPOINT unsupported_scalar')
  try: connection.run(sql,domain=DOMAIN,installation='nul\0scalar',ordinal='99')
  except pg8000.exceptions.DatabaseError as error:
   if error.args[0]['C']!='22021': raise
   checks.append({'id':'native-text-nul-refusal','sqlstate':'22021'})
  else: raise ValueError('Expected native text NUL refusal')
  connection.run('ROLLBACK TO SAVEPOINT unsupported_scalar');connection.run('RELEASE SAVEPOINT unsupported_scalar')
  if connection.run('SELECT pg_current_xact_id()::text')[0][0]!=xid: raise ValueError('Original native xid changed')
  checks.append({'id':'same-native-xid-after-confirmed-refusal','writerXid':xid})
  connection.run('ROLLBACK')
 finally:
  if connection is not None: connection.close()
  server.cleanup()
if any((ROOT/p).read_bytes()!=v for p,v in frozen.items()): raise ValueError('Original source drift')
receipt={'scope':'Native builtin JSON scalar spelling and current-xid correspondence against private Python candidate address codec; administrative isolated fixture, no installed address routine','serverVersion':version,'sql':sql,'observations':checks,'sourceSha256':{p:hashlib.sha256(v).hexdigest() for p,v in frozen.items()},'producerSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'nativeAddressProfileQualified':False,'installerReady':False,'acceptanceCasesPromoted':[],'limitations':['Eight finite scalar samples are not all native scalar/domain/encoding profiles','PostgreSQL text rejects NUL even though a host JSON string can represent it; original native installation identity admission must reject unsupported text','Ordinals are manually selected fixtures, not original host issuer custody','No installed encoder identity/owner/ACL/dependency qualification','No original installation/context/group registry resolution, semantic body, resource or authority qualification']}
with out.open('x') as f:f.write(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'observations':len(checks),'nativeAddressProfileQualified':False}))
