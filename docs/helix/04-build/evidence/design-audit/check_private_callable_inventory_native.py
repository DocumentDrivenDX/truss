"""Actual 17-helper native/ACL inventory. Not complete protected installation."""
import hashlib, importlib.metadata, json, sys, tempfile
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import pg8000.native, pg8000.exceptions, pgserver
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[4]
if len(sys.argv)!=2 or Path(sys.argv[1]).name!=sys.argv[1] or not sys.argv[1].endswith('.json'):
 raise SystemExit('Fresh receipt basename required')
out=HERE/sys.argv[1]
if out.exists(): raise SystemExit('Receipt exists')
if importlib.metadata.version('pgserver')!='0.1.4+truss.pg16.15' or importlib.metadata.version('pg8000')!='1.31.5':
 raise SystemExit('Original local runtime and driver required')
manifest_path='docs/helix/02-design/contracts/capacity-component-source-handoff-v0.1.proposal.json'
manifest=json.loads((ROOT/manifest_path).read_bytes())
paths=[manifest_path,'docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql','docs/helix/04-build/evidence/design-audit/capacity-reservation-source.owner-export.sql','docs/helix/02-design/contracts/row-home-capacity-initialization-v0.1.proposal.sql','docs/helix/02-design/contracts/bindings/truss-row-touch-retention-resource-v0.1.proposal.json']
for group in manifest['sources']:
 for field in ('source','ownerExport','ownerCapture'):
  p=group[field]['path']; paths.append(p)
  if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=group[field]['sha256']: raise ValueError('Original handoff pin drift')
frozen={p:(ROOT/p).read_bytes() for p in paths}; checks=[]; inventory=[]
def expect(name,expected,observed):
 if expected!=observed: raise ValueError(name+': mismatch')
 checks.append({'id':name,'expected':expected,'observed':observed})
with tempfile.TemporaryDirectory(prefix='truss-callable-inventory-') as directory:
 server=pgserver.get_server(Path(directory)/'data',cleanup_mode='stop'); connections=[]
 try:
  uri=urlparse(server.get_uri()); opts=parse_qs(uri.query); host=opts.get('host',[uri.hostname])[0]; port=int(opts.get('port',[uri.port or 5432])[0])
  def connect(user):
   c=pg8000.native.Connection(user=user,database='postgres',unix_sock=str(Path(host)/f'.s.PGSQL.{port}'),ssl_context=False,timeout=5); connections.append(c); return c
  admin=connect('postgres'); version=admin.run('SHOW server_version')[0][0]
  if version!='16.15': raise ValueError('Native version mismatch')
  admin.run(frozen[paths[1]].decode()); admin.run(frozen[paths[2]].decode())
  init=frozen[paths[3]].decode().replace('$1::bytea',':layout').replace('$2::bytea',':resource')
  admin.run(init,layout=frozen[paths[1]],resource=frozen[paths[4]])
  before={r[0] for r in admin.run("SELECT p.oid::text FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='truss'")}
  for group in manifest['sources']: admin.run(frozen[group['ownerExport']['path']].decode())
  after={r[0] for r in admin.run("SELECT p.oid::text FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='truss'")}
  admin.run('CREATE ROLE inventory_actor LOGIN; CREATE ROLE inventory_grantee NOLOGIN; GRANT USAGE ON SCHEMA truss TO inventory_actor; GRANT inventory_grantee TO inventory_actor')
  actor=connect('inventory_actor'); selected=set()
  allowed={'bigint','bytea','bytea[]','integer[]','oid','text','truss.row_home_operation','truss.row_home_touch'}
  for r in manifest['routines']:
   selector=r['selector']; types=r['sqlArgumentTypes']
   if not selector.startswith('truss.') or not selector[6:].replace('_','').isalnum() or any(t not in allowed for t in types): raise ValueError('Closed source selector required')
   signature=selector+'('+','.join(types)+')'
   row=admin.run("""SELECT p.oid::text,n.oid::text,p.proowner::text,owner.rolname,l.lanname,p.prosecdef,p.provolatile,p.proparallel,p.proisstrict,p.proleakproof,p.proconfig,p.proacl::text,pg_get_functiondef(p.oid),pg_get_function_result(p.oid),
 EXISTS(SELECT 1 FROM aclexplode(coalesce(p.proacl,acldefault('f',p.proowner))) a WHERE a.grantee=0 AND a.privilege_type='EXECUTE'),
 has_function_privilege('inventory_actor',p.oid,'EXECUTE'),has_function_privilege('postgres',p.oid,'EXECUTE')
 FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace JOIN pg_roles owner ON owner.oid=p.proowner JOIN pg_language l ON l.oid=p.prolang WHERE p.oid=to_regprocedure(:signature)""",signature=signature)[0]
   selected.add(row[0])
   expect(signature+'-native-attributes',['postgres','plpgsql',False,'v','u',False,False,['search_path=pg_catalog, pg_temp']],row[3:11])
   expect(signature+'-effective-execute',[False,False,True],row[14:17])
   expect(signature+'-result-type',r['sqlResultType'],row[13])
   inventory.append({'sourceSelector':signature,'routineOid':row[0],'namespaceOid':row[1],'ownerOid':row[2],'owner':row[3],'acl':row[11],'nativeDefinition':row[12],'nativeDefinitionSha256':hashlib.sha256(row[12].encode()).hexdigest()})
   try: actor.run('SELECT '+selector+'('+','.join('NULL::'+t for t in types)+')')
   except pg8000.exceptions.DatabaseError as error: expect(signature+'-direct-call-refusal','42501',error.args[0]['C'])
   else: raise ValueError('Ordinary direct call unexpectedly succeeded')
  expect('complete-new-routine-inventory',sorted(selected),sorted(after-before))
  # Effective membership matters even without a direct grant to the login role.
  signature=inventory[0]['sourceSelector']
  admin.run('GRANT EXECUTE ON FUNCTION '+signature+' TO inventory_grantee')
  expect('inherited-extra-grant-detected',True,admin.run("SELECT has_function_privilege('inventory_actor',CAST(:signature AS regprocedure),'EXECUTE')",signature=signature)[0][0])
  admin.run('REVOKE EXECUTE ON FUNCTION '+signature+' FROM inventory_grantee')
  expect('inherited-grant-removal-restores-denial',False,admin.run("SELECT has_function_privilege('inventory_actor',CAST(:signature AS regprocedure),'EXECUTE')",signature=signature)[0][0])
  admin.run('GRANT EXECUTE ON FUNCTION '+signature+' TO PUBLIC')
  expect('public-extra-grant-detected',True,admin.run("SELECT has_function_privilege('inventory_actor',CAST(:signature AS regprocedure),'EXECUTE')",signature=signature)[0][0])
  admin.run('REVOKE EXECUTE ON FUNCTION '+signature+' FROM PUBLIC')
  expect('public-grant-removal-restores-denial',False,admin.run("SELECT has_function_privilege('inventory_actor',CAST(:signature AS regprocedure),'EXECUTE')",signature=signature)[0][0])
 finally:
  for c in connections: c.close()
  server.cleanup()
if any((ROOT/p).read_bytes()!=v for p,v in frozen.items()): raise ValueError('Original source drift')
receipt={'scope':'Actual jointly installed 17-helper native identity/attribute/effective-EXECUTE inventory under administrative fixture owner postgres','serverVersion':version,'routines':inventory,'observations':checks,'sourceSha256':{p:hashlib.sha256(v).hexdigest() for p,v in frozen.items()},'producerSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'installerReady':False,'completeProtectedCallableClosureQualified':False,'acceptanceCasesPromoted':[],'limitations':['Native OIDs and postgres owner belong only to this ephemeral fixture, not adopted production registrations','No complete indirect/transitive dependency or native data-rights closure','Seven semantic bodies and owner subject/current-authority integration remain absent','Effective EXECUTE denial does not prove trigger-path or administrative bypass security','No protected mutation, journal/feed/receipt or installation publication qualification']}
with out.open('x') as f: f.write(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'routineCount':len(inventory),'observations':len(checks),'installerReady':False}))
