"""Installed candidate private address encoder; no registry or authority qualification."""
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
paths=['packages/python/src/truss/_row_operation_address.py','packages/python/src/truss/_acceptance_json.py','packages/postgresql/native/operation-address/encoder.sql','docs/helix/04-build/evidence/design-audit/operation-address-source.owner-export.sql']; frozen={p:(ROOT/p).read_bytes() for p in paths}
samples=['installation','quotes" and backslash\\','\b\f\n\r\t',''.join(chr(i) for i in range(1,32)),chr(127),'é','\u2028\u2029',''.join(chr(i) for i in (128,2047,2048,55295,57344,65535,65536,1114111))]
checks=[]
with tempfile.TemporaryDirectory(prefix='truss-native-address-') as directory:
 server=pgserver.get_server(Path(directory)/'data',cleanup_mode='stop'); connection=None
 try:
  uri=urlparse(server.get_uri()); opts=parse_qs(uri.query); host=opts.get('host',[uri.hostname])[0]; port=int(opts.get('port',[uri.port or 5432])[0])
  connection=pg8000.native.Connection(user='postgres',database='postgres',unix_sock=str(Path(host)/f'.s.PGSQL.{port}'),ssl_context=False,timeout=30)
  version=connection.run('SHOW server_version')[0][0]
  if version!='16.15': raise ValueError('Native version mismatch')
  connection.run('CREATE SCHEMA truss');connection.run(frozen[paths[3]].decode())
  connection.run('CREATE ROLE address_actor LOGIN; GRANT USAGE ON SCHEMA truss TO address_actor')
  native_binding=connection.run("SELECT p.oid::text,p.proowner::text,p.prosecdef,p.provolatile,p.proparallel,p.proconfig,p.proacl::text,pg_get_functiondef(p.oid),has_function_privilege('address_actor',p.oid,'EXECUTE') FROM pg_proc p WHERE p.oid='truss.operation_address_original(text,xid8,bigint)'::regprocedure")[0]
  if native_binding[2:6]!=[False,'v','u',['search_path=pg_catalog, pg_temp']] or native_binding[8] is not False:raise ValueError('Original private binding mismatch')
  checks.append({'id':'private-native-binding','binding':native_binding})
  connection.run('BEGIN'); xid=connection.run('SELECT pg_current_xact_id()::text')[0][0]
  sql='SELECT truss.operation_address_original(CAST(:installation AS text),CAST(:xid AS xid8),CAST(:ordinal AS bigint))'
  for i, installation in enumerate(samples):
   ordinal=str(7+4*i)
   native=connection.run(sql,xid=xid,installation=installation,ordinal=ordinal)[0][0]
   expected=encode_row_operation_address(installation,xid,ordinal)
   if native!=expected: raise ValueError('Native/Python scalar spelling mismatch')
   decoded=decode_row_operation_address(native)
   if (decoded.installation,decoded.writer_xid,decoded.operation_ordinal)!=(installation,xid,ordinal): raise ValueError('Native address projection mismatch')
   checks.append({'id':'scalar-'+str(i),'installationUtf8Hex':installation.encode().hex(),'originalAddressHex':native.hex(),'writerXid':xid,'operationOrdinal':ordinal})
  connection.run('SAVEPOINT unsupported_scalar')
  try: connection.run(sql,xid=xid,installation='nul\0scalar',ordinal='99')
  except pg8000.exceptions.DatabaseError as error:
   if error.args[0]['C']!='22021': raise
   checks.append({'id':'native-text-nul-refusal','sqlstate':'22021'})
  else: raise ValueError('Expected native text NUL refusal')
  connection.run('ROLLBACK TO SAVEPOINT unsupported_scalar');connection.run('RELEASE SAVEPOINT unsupported_scalar')
  if connection.run('SELECT pg_current_xact_id()::text')[0][0]!=xid: raise ValueError('Original native xid changed')
  checks.append({'id':'same-native-xid-after-confirmed-refusal','writerXid':xid})
  connection.run('ROLLBACK')
  def refuse(name, installation, writer, ordinal, expected):
   try: connection.run(sql,installation=installation,xid=writer,ordinal=ordinal)
   except pg8000.exceptions.DatabaseError as error:
    if error.args[0]['C']!=expected:raise
    checks.append({'id':name,'sqlstate':expected})
   else:raise ValueError('Expected native input refusal')
  for name,installation,writer,ordinal in [('null-installation',None,xid,'1'),('null-writer','installation',None,'1'),('negative-ordinal','installation',xid,'-1')]:
   refuse(name,installation,writer,ordinal,'22023')
  installation='a'*(8388608-13-len(DOMAIN)-len(xid)-1)
  native=connection.run(sql,installation=installation,xid=xid,ordinal='0')[0][0]
  expected=encode_row_operation_address(installation,xid,'0')
  if native!=expected or len(native)!=8388608:raise ValueError('Native exact output ceiling mismatch')
  checks.append({'id':'exact-eight-mib-output','bytes':len(native),'sha256':hashlib.sha256(native).hexdigest(),'fullPythonByteEquality':True,'inputPattern':'ASCII a repeated to full output ceiling; ordinal0 and captured xid'})
  refuse('one-byte-over-output',installation+'a',xid,'0','54000')
  refuse('escaped-expansion-over-output','\x01'*(8388608//6),xid,'0','54000')
  maximum=connection.run(sql,installation='installation',xid='18446744073709551615',ordinal='9223372036854775807')[0][0]
  if maximum!=encode_row_operation_address('installation','18446744073709551615','9223372036854775807'):raise ValueError('Native max domain mismatch')
  checks.append({'id':'native-maximum-domains','originalAddressHex':maximum.hex()})
  connection.run('SET ROLE address_actor')
  refuse('ordinary-private-call-denial','installation',xid,'0','42501')
  connection.run('RESET ROLE')
 finally:
  if connection is not None: connection.close()
  server.cleanup()
if any((ROOT/p).read_bytes()!=v for p,v in frozen.items()): raise ValueError('Original source drift')
receipt={'scope':'Installed private native address encoding, attributes/ACL and output preflight against Python candidate; isolated administrative fixture, no original registry/authority qualification','serverVersion':version,'sql':sql,'observations':checks,'sourceSha256':{p:hashlib.sha256(v).hexdigest() for p,v in frozen.items()},'producerSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'nativeAddressProfileQualified':False,'installerReady':False,'acceptanceCasesPromoted':[],'limitations':['Eight finite scalar samples are not all native scalar/domain/encoding profiles','PostgreSQL text rejects NUL even though a host JSON string can represent it; original native installation identity admission must reject unsupported text','Ordinals are manually selected fixtures, not original host issuer custody','Actual fixture identity/attributes and one ordinary role tested; complete production owner/private ACL/dependency/resource qualification absent','No original installation/context/group registry resolution, semantic body, resource or authority qualification']}
with out.open('x') as f:f.write(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'observations':len(checks),'nativeAddressProfileQualified':False}))
