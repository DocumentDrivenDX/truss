#!/usr/bin/env python3
"""Native caller/asserted-origin capture experiment; no public R5 qualification."""
import hashlib
import importlib.metadata
import importlib.resources
import json
from pathlib import Path
import subprocess
import tempfile
from urllib.parse import urlparse, urlunparse
import pgserver

root=Path(__file__).resolve().parents[1]
paths=['docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql',
       'packages/postgresql/native/operation-asserted-origin-admission.sql']
originals=[(root/path).read_bytes() for path in paths]
psql=Path(str(importlib.resources.files('pgserver')))/'pginstall/bin/psql'
asserted='external origin: Ω'
profile='fixture-not-admitted'
call="SELECT convert_from(decode(context_hex,'hex'),'UTF8') FROM truss.runtime_admit_operation_with_asserted_origin('mutation',decode('01','hex'),decode('02','hex'),decode('03','hex'),decode('04','hex'),decode('05','hex'),decode('06','hex'),convert_to('"+asserted+"','UTF8'),convert_to('"+profile+"','UTF8'));"
setup="""
CREATE ROLE truss_origin_person LOGIN NOSUPERUSER NOBYPASSRLS;
CREATE ROLE truss_origin_role NOLOGIN NOSUPERUSER NOBYPASSRLS;
GRANT truss_origin_role TO truss_origin_person;
GRANT USAGE ON SCHEMA truss TO truss_origin_person,truss_origin_role;
GRANT SELECT,UPDATE ON truss.schema_head TO truss_origin_person,truss_origin_role;
GRANT SELECT,INSERT ON truss.row_home_operation TO truss_origin_person,truss_origin_role;
GRANT EXECUTE ON FUNCTION truss.runtime_admit_operation_with_asserted_origin(text,bytea,bytea,bytea,bytea,bytea,bytea,bytea,bytea) TO truss_origin_person,truss_origin_role;
"""
with tempfile.TemporaryDirectory(prefix='truss-origin-capture-') as directory:
 server=pgserver.get_server(Path(directory)/'data',cleanup_mode='stop')
 try:
  uri=server.get_uri(); parsed=urlparse(uri)
  if '@' not in parsed.netloc:raise RuntimeError('Expected original local URI user component')
  person_uri=urlunparse(parsed._replace(netloc='truss_origin_person@'+parsed.netloc.split('@',1)[1]))
  def query(sql,connection_uri=uri):
   return subprocess.check_output([str(psql),connection_uri,'-X','-q','-A','-t','-v','ON_ERROR_STOP=1'],input=sql,text=True,timeout=60).strip()
  version=query('SHOW server_version;')
  if version!='16.15' or importlib.metadata.version('pgserver')!='0.1.4+truss.pg16.15':raise RuntimeError('Corrected candidate required')
  query('BEGIN;\n'+';\n'.join(data.decode() for data in originals)+';\n'+setup+'\nCOMMIT;')
  captured=[]
  for role_command in ['', 'SET ROLE truss_origin_role;']:
   result=query('BEGIN;'+role_command+call+'ROLLBACK;',person_uri)
   captured.append(json.loads(result))
  role_oids=json.loads(query("SELECT json_object_agg(rolname,oid::text) FROM pg_roles WHERE rolname IN ('truss_origin_person','truss_origin_role');"))
  for context,acting in zip(captured,['truss_origin_person','truss_origin_role']):
   expected={'sessionUser':'truss_origin_person','actingUser':acting,
    'sessionRoleOid':role_oids['truss_origin_person'],'actorRoleOid':role_oids[acting],
    'assertedOriginUtf8Hex':asserted.encode().hex(),'assertedOriginCaptureProfileHex':profile.encode().hex()}
   if any(context[key]!=value for key,value in expected.items()):raise RuntimeError('Native original actor/asserted-origin substitution')
  if query('SELECT count(*) FROM truss.row_home_operation;')!='0':raise RuntimeError('Caller rollback left registry rows')
 finally:server.cleanup()
receipt={'scope':'Two native0.16 asserted-origin captures from an actual non-superuser authenticated local connection; fixture grants and bytes only',
 'serverVersion':version,'pgserver':importlib.metadata.version('pgserver'),'capturedContexts':captured,
 'independentNativeRoleOids':role_oids,'fixtureGrantsSql':setup,'callSql':call,
 'sources':[{'path':path,'sha256':hashlib.sha256(data).hexdigest()} for path,data in zip(paths,originals)],
 'producerSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
 'registryRowsAfterCallerRollback':0,'r5Qualified':False,'nativeIssuerQualified':False,
 'limitations':['Disposable local trust authentication only; no TLS or deployment grants',
 'Fixture grants include head UPDATE and are not an installed security profile',
 'Fixture asserted/profile bytes are not original admitted UMF/application evidence',
 'No public Python mutation, journal/action correspondence or completion proof',
 'Original row-derived ordinal allocator remains incompatible']}
(root/'docs/helix/04-build/evidence/design-audit/pgserver-corrected-origin.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'authenticatedCallerCaptures':2,'serverVersion':version,'r5Qualified':False}))
