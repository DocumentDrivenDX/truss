"""Original invoker admission versus selected definer role transition; no grant adoption."""
import hashlib,importlib.metadata,json,sys,tempfile
from pathlib import Path
from urllib.parse import urlparse,parse_qs
import pg8000.native,pg8000.exceptions,pgserver
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
if len(sys.argv)!=2 or Path(sys.argv[1]).name!=sys.argv[1]:raise SystemExit('Fresh receipt basename required')
out=HERE/sys.argv[1]
if out.exists():raise SystemExit('Receipt exists')
if importlib.metadata.version('pgserver')!='0.1.4+truss.pg16.15' or importlib.metadata.version('pg8000')!='1.31.5':raise SystemExit('Original runtime/driver required')
paths=['docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql','packages/postgresql/native/issued-operation-admission/operation-admission.sql','docs/helix/02-design/contracts/reference-routine-design-v0.1.proposal.json'];paths += ['packages/postgresql/native/issued-operation-admission/operation-asserted-origin-admission.sql','packages/postgresql/native/issued-operation-admission/operation-epoch-context-admission.sql','packages/postgresql/native/issued-operation-admission/operation-configuration-context-admission.sql'];frozen={p:(ROOT/p).read_bytes() for p in paths};checks=[]
def expect(name,expected,observed):
 if expected!=observed:raise ValueError(name+': mismatch')
 checks.append({'id':name,'expected':expected,'observed':observed})
with tempfile.TemporaryDirectory(prefix='truss-admission-elevation-') as directory:
 server=pgserver.get_server(Path(directory)/'data',cleanup_mode='stop');connections=[]
 try:
  uri=urlparse(server.get_uri());opts=parse_qs(uri.query);host=opts.get('host',[uri.hostname])[0];port=int(opts.get('port',[uri.port or 5432])[0])
  def connect(user):
   c=pg8000.native.Connection(user=user,database='postgres',unix_sock=str(Path(host)/f'.s.PGSQL.{port}'),ssl_context=False,timeout=5);connections.append(c);return c
  admin=connect('postgres');version=admin.run('SHOW server_version')[0][0]
  if not version.startswith('16.15'):raise ValueError('Native version mismatch')
  for p in [*paths[:2],*paths[3:]]:admin.run(frozen[p].decode())
  # Deliberately broad fixture grants exercise the invoker prototype; they are
  # explicitly forbidden as a shortcut to ordinary protected runtime adoption.
  admin.run('CREATE ROLE actor_probe LOGIN; CREATE ROLE integrity_probe NOLOGIN; CREATE SCHEMA elevation_probe; GRANT USAGE ON SCHEMA truss,elevation_probe TO actor_probe,integrity_probe; GRANT SELECT,UPDATE ON truss.schema_head TO actor_probe,integrity_probe; GRANT SELECT,INSERT ON truss.row_home_operation TO actor_probe,integrity_probe; GRANT EXECUTE ON FUNCTION truss.runtime_admit_operation(bigint,text,bytea,bytea,bytea,bytea,bytea,bytea) TO actor_probe,integrity_probe')
  admin.run("""CREATE FUNCTION elevation_probe.admit(n bigint) RETURNS TABLE(writer_xid text,ordinal text,context_hex text) LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$ SELECT * FROM truss.runtime_admit_operation(n,'mutation',decode('01','hex'),decode('02','hex'),decode('03','hex'),decode('04','hex'),decode('05','hex'),decode('06','hex')) $$;
ALTER FUNCTION elevation_probe.admit(bigint) OWNER TO integrity_probe;
CREATE FUNCTION elevation_probe.observe() RETURNS TABLE(person text,acting text,role_setting text,original_context bytea) LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$ SELECT session_user::text,current_user::text,current_setting('role'),o.original_context_bytes FROM truss.row_home_operation o WHERE o.original_writer_xid=pg_current_xact_id_if_assigned() $$;
ALTER FUNCTION elevation_probe.observe() OWNER TO integrity_probe;
GRANT EXECUTE ON FUNCTION elevation_probe.admit(bigint),elevation_probe.observe() TO actor_probe;""")
  actor=connect('actor_probe');actor.run('BEGIN');actor.run('SAVEPOINT rejected_definer')
  before=actor.run('SELECT session_user::text,current_user::text,current_setting(\'role\')')[0]
  expect('original-actor-boundary',['actor_probe','actor_probe','none'],before)
  try:actor.run('SELECT * FROM elevation_probe.admit(0)')
  except pg8000.exceptions.DatabaseError as e:expect('nested-definer-admission-refusal','55000',e.args[0]['C'])
  else:raise ValueError('Expected original invoker-boundary refusal')
  actor.run('ROLLBACK TO SAVEPOINT rejected_definer');actor.run('RELEASE SAVEPOINT rejected_definer')
  expect('refused-elevation-has-no-registry-effect',[[0]],actor.run('SELECT count(*) FROM truss.row_home_operation'))
  # Fault attempt consumes0 in the administrative schedule; actual host issuer
  # composition is not proved by manually selecting1 here.
  row=actor.run("SELECT * FROM truss.runtime_admit_operation(1,'mutation',decode('01','hex'),decode('02','hex'),decode('03','hex'),decode('04','hex'),decode('05','hex'),decode('06','hex'))")[0]
  original=bytes.fromhex(row[2]);context=json.loads(original)
  expect('invoker-original-actor-fields',['actor_probe','actor_probe'],[context['sessionUser'],context['actingUser']])
  expect('invoker-native-oid-correspondence',True,context['actorRoleOid']==context['sessionRoleOid'])
  observed=actor.run('SELECT * FROM elevation_probe.observe()')[0]
  expect('definer-person-owner-separation',['actor_probe','integrity_probe','none'],observed[:3])
  expect('original-context-preserved-across-elevation',original.hex(),observed[3].hex())
  expect('acting-role-restored-after-wrapper',before,actor.run('SELECT session_user::text,current_user::text,current_setting(\'role\')')[0])
  expect('actual-original-xid-preserved',row[0],actor.run('SELECT pg_current_xact_id_if_assigned()::text')[0][0])
  actor.run('ROLLBACK')
  expect('original-host-rollback-removes-registry',[[0]],admin.run('SELECT count(*) FROM truss.row_home_operation'))
  base_types=['bigint','text']+['bytea']*6
  base_args="0,'mutation',"+','.join("decode('01','hex')" for _ in range(6))
  for suffix,extra_types,extra_args in [('asserted_origin',['bytea','bytea'],",decode('02','hex'),decode('03','hex')"),('epoch_context',['bytea','bytea','text','text','text'],",decode('02','hex'),decode('03','hex'),'i','e','g'"),('configuration_context',['bytea','bytea','text','text','text','bytea'],",decode('02','hex'),decode('03','hex'),'i','e','g',decode('04','hex')")]:
   name='runtime_admit_operation_with_'+suffix;signature='truss.'+name+'('+','.join(base_types+extra_types)+')'
   attributes=admin.run("SELECT p.oid::text,p.proowner::text,p.prosecdef,p.proconfig FROM pg_proc p WHERE p.oid=to_regprocedure(:signature)",signature=signature)[0]
   expect(suffix+'-original-invoker-attributes',[False,['search_path=pg_catalog, pg_temp']],attributes[2:])
   admin.run('GRANT EXECUTE ON FUNCTION '+signature+' TO integrity_probe')
   wrapper='elevation_probe.admit_'+suffix
   admin.run('CREATE FUNCTION '+wrapper+'() RETURNS TABLE(writer_xid text,ordinal text,context_hex text) LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $body$ SELECT * FROM truss.'+name+'('+base_args+extra_args+') $body$; ALTER FUNCTION '+wrapper+'() OWNER TO integrity_probe; GRANT EXECUTE ON FUNCTION '+wrapper+'() TO actor_probe')
   actor.run('BEGIN');actor.run('SAVEPOINT refused_family')
   try:actor.run('SELECT * FROM '+wrapper+'()')
   except pg8000.exceptions.DatabaseError as error:expect(suffix+'-nested-definer-refusal','55000',error.args[0]['C'])
   else:raise ValueError('Advanced family bypassed original invoker boundary')
   actor.run('ROLLBACK TO SAVEPOINT refused_family');actor.run('RELEASE SAVEPOINT refused_family')
   expect(suffix+'-no-surviving-registry-effects',[[0]],actor.run('SELECT count(*) FROM truss.row_home_operation'))
   expect(suffix+'-original-actor-restored',before,actor.run("SELECT session_user::text,current_user::text,current_setting('role')")[0])
   actor.run('ROLLBACK')
  families=[('runtime_admit_operation',paths[1],base_types),('runtime_admit_operation_with_asserted_origin',paths[3],base_types+['bytea','bytea']),('runtime_admit_operation_with_epoch_context',paths[4],base_types+['bytea','bytea','text','text','text']),('runtime_admit_operation_with_configuration_context',paths[5],base_types+['bytea','bytea','text','text','text','bytea'])]
  registrations=[]
  for name,path,types in families:
   signature='truss.'+name+'('+','.join(types)+')'
   original_body=frozen[path].decode().split('AS $$',1)[1].split('$$;',1)[0]
   native=admin.run("SELECT p.oid::text,n.oid::text,p.proowner::text,owner.rolname,l.lanname,p.prosecdef,p.provolatile,p.proparallel,p.proisstrict,p.proleakproof,p.proconfig,p.prosrc,pg_get_functiondef(p.oid),pg_get_function_result(p.oid),p.proacl::text,has_function_privilege('actor_probe',p.oid,'EXECUTE'),has_function_privilege('integrity_probe',p.oid,'EXECUTE'),EXISTS(SELECT 1 FROM aclexplode(coalesce(p.proacl,acldefault('f',p.proowner))) a WHERE a.grantee=0 AND a.privilege_type='EXECUTE') FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace JOIN pg_roles owner ON owner.oid=p.proowner JOIN pg_language l ON l.oid=p.prolang WHERE p.oid=to_regprocedure(:signature)",signature=signature)[0]
   expect(name+'-complete-selected-native-attributes',['postgres','plpgsql',False,'v','u',False,False,['search_path=pg_catalog, pg_temp']],native[3:11])
   expect(name+'-original-body-exact',original_body,native[11])
   expect(name+'-original-result-type','TABLE(writer_xid text, ordinal text, context_hex text)',native[13])
   expect(name+'-effective-fixture-privileges',[name=='runtime_admit_operation',True,False],native[15:18])
   registrations.append({'sourcePath':path,'sourceSelector':signature,'routineOid':native[0],'namespaceOid':native[1],'ownerOid':native[2],'nativeDefinition':native[12],'nativeDefinitionSha256':hashlib.sha256(native[12].encode()).hexdigest(),'originalAcl':native[14]})
  if len({r['routineOid'] for r in registrations})!=4 or len({r['namespaceOid'] for r in registrations})!=1 or len({r['ownerOid'] for r in registrations})!=1:raise ValueError('Original native family identity mismatch')
  checks.append({'id':'complete-four-family-original-native-registration','originalRegistrations':registrations})
  admin.run('CREATE ROLE admission_ordinary_control LOGIN; GRANT USAGE ON SCHEMA truss TO admission_ordinary_control')
  for name,path,types in families:admin.run('GRANT EXECUTE ON FUNCTION truss.'+name+'('+','.join(types)+') TO admission_ordinary_control')
  ordinary=connect('admission_ordinary_control')
  extras=['',",decode('02','hex'),decode('03','hex')",",decode('02','hex'),decode('03','hex'),'i','e','g'",",decode('02','hex'),decode('03','hex'),'i','e','g',decode('04','hex')"]
  attempts=[(name,'SELECT * FROM truss.'+name+'('+base_args+extra+')') for (name,_,_),extra in zip(families,extras)]
  attempts += [('direct-registry-read','SELECT * FROM truss.row_home_operation'),('direct-registry-update',"UPDATE truss.row_home_operation SET phase='admitted'"),('direct-registry-delete','DELETE FROM truss.row_home_operation')]
  ordinary.run('BEGIN')
  for name,sql in attempts:
   ordinary.run('SAVEPOINT ordinary_refusal')
   try:ordinary.run(sql)
   except pg8000.exceptions.DatabaseError as error:
    missing=name in ('runtime_admit_operation_with_epoch_context','runtime_admit_operation_with_configuration_context')
    expect(name+'-ordinary-minimal-rights-refusal','42883' if missing else '42501',error.args[0]['C'])
    if missing:
     if 'runtime_lock_source_epoch' not in error.args[0].get('M',''):raise ValueError('Unexpected unresolved native dependency')
     checks.append({'id':name+'-original-missing-dependency','sqlstate':error.args[0]['C'],'originalMessage':error.args[0]['M'],'scope':'fixture missing required callable dependency; not permission closure proof'})
   else:raise ValueError('Minimal ordinary role gained registry authority')
   ordinary.run('ROLLBACK TO SAVEPOINT ordinary_refusal');ordinary.run('RELEASE SAVEPOINT ordinary_refusal')
  ordinary.run('ROLLBACK')
  expect('minimal-rights-refusals-no-surviving-registry',[[0]],admin.run('SELECT count(*) FROM truss.row_home_operation'))
 finally:
  for c in connections:c.close()
  server.cleanup()
if any((ROOT/p).read_bytes()!=v for p,v in frozen.items()):raise ValueError('Original source drift')
receipt={'scope':'Actual original invoker admission refusal under distinct definer owner and preservation of invoker context across read-only elevation; administrative grant/wrapper fixture only','serverVersion':version,'observations':checks,'sourceSha256':{p:hashlib.sha256(v).hexdigest() for p,v in frozen.items()},'producerSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'installerReady':False,'nativeOrdinaryProtectedAdmissionQualified':False,'acceptanceCasesPromoted':[],'limitations':['Broad fixture INSERT/SELECT/UPDATE grants are not an adopted ordinary-role plan','Read-only owner wrapper is not any of the seven semantic bodies or current authorization proof','Manual burned ordinal schedule is not original host issuer/account qualification','Current0.2 invoker context is not silently reinterpreted as definer owner context','Owner-aware original private admission/role/DDL/dependency profile remains unfinished']}
with out.open('x') as f:f.write(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'observations':len(checks),'installerReady':False}))
