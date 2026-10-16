from pathlib import Path
from tempfile import TemporaryDirectory
from hashlib import sha256
import json,secrets,time
import psycopg
from psycopg import sql
from truss import LocalPostgres
out=Path('/private/tmp/truss-scram-auth-proof-20261014');out.mkdir(exist_ok=True)
with TemporaryDirectory(prefix='truss-auth-proof-') as directory:
 with LocalPostgres(Path(directory)/'data') as runtime:
  params=psycopg.conninfo.conninfo_to_dict(runtime.info.connection_uri)
  with psycopg.connect(**params,autocommit=True) as admin:
   version=admin.execute('SHOW server_version').fetchone()[0]
   assert version=='18.6'
   password=secrets.token_urlsafe(32)
   admin.execute("SET password_encryption='scram-sha-256'")
   admin.execute(sql.SQL('CREATE ROLE auth_probe_login LOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS PASSWORD {}').format(sql.Literal(password)))
   role=admin.execute("SELECT oid::text,rolcanlogin,rolsuper,rolcreaterole,rolcreatedb,rolreplication,rolbypassrls,rolpassword LIKE 'SCRAM-SHA-256$%%' FROM pg_authid WHERE rolname='auth_probe_login'").fetchone()
   assert role[1:]==(True,False,False,False,False,False,True)
   hba=Path(admin.execute('SHOW hba_file').fetchone()[0]);original=hba.read_bytes()
   selected=b'local all auth_probe_login scram-sha-256\n'+original
   hba.write_bytes(selected)
   assert admin.execute('SELECT pg_reload_conf()').fetchone()==(True,)
   attempts=[]
   deadline=time.monotonic()+5
   while True:
    try:
     unexpected=psycopg.connect(**dict(params,user='auth_probe_login',password='wrong'),connect_timeout=2)
    except psycopg.Error as e:
     attempts.append({'wrongPassword':'refused','sqlstate':e.sqlstate,'structuredSqlstateUnavailable':e.sqlstate is None});break
    else:
     unexpected.close();attempts.append({'wrongPassword':'acceptedBeforeReload','qualified':False})
     assert time.monotonic()<deadline
     time.sleep(.05)
   rules=admin.execute("SELECT type,database,user_name,auth_method,error FROM pg_hba_file_rules WHERE user_name=ARRAY['auth_probe_login']::text[] ORDER BY rule_number").fetchall()
   assert rules==[('local',['all'],['auth_probe_login'],'scram-sha-256',None)]
   with psycopg.connect(**dict(params,user='auth_probe_login',password=password,require_auth='scram-sha-256'),autocommit=True,connect_timeout=2) as caller:
    assert caller.pgconn.used_password
    captured=caller.execute("SELECT (SELECT oid::text FROM pg_roles WHERE rolname=SESSION_USER),SESSION_USER::text,CURRENT_USER::text,current_database()::text,pg_backend_pid()::text,current_setting('role'),current_setting('server_version_num')").fetchone()
    assert captured[0]==role[0] and captured[1:3]==('auth_probe_login','auth_probe_login') and captured[5:] == ('none','180006')
    caller.execute('BEGIN ISOLATION LEVEL REPEATABLE READ READ WRITE')
    actual=caller.execute("SELECT SESSION_USER::text,CURRENT_USER::text,current_setting('transaction_isolation'),current_setting('transaction_read_only')").fetchone()
    assert actual==('auth_probe_login','auth_probe_login','repeatable read','off')
    caller.rollback()
   try:
    unexpected=psycopg.connect(**dict(params,user='auth_probe_login',password=''),connect_timeout=2)
   except psycopg.Error:missing_refused=True
   else:unexpected.close();missing_refused=False
   assert missing_refused
   report={'scope':'Stock SCRAM native-login/caller-custody feasibility on owned Unix-only PG18.6; no external human/service classification, action role, Subject, delegation, permit, selection or seal qualification','server':version,'psycopg':psycopg.__version__,'libpq':psycopg.pq.version(),'selectedHbaSha256':sha256(selected).hexdigest(),'originalHbaSha256':sha256(original).hexdigest(),'storedScramVerifier':True,'wrongPasswordRefused':True,'missingPasswordRefused':True,'actualOriginalNativeRoleObserved':True,'sameCallerRRReadWrite':True,'requireAuth':'scram-sha-256','usedPassword':True,'reloadObservations':attempts,'nativePrincipalKindQualified':False,'passed':True}
   (out/'receipt.json').write_text(json.dumps(report,indent=2)+'\n')
   print(json.dumps(report))
