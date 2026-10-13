"""Owned PostgreSQL catalog lock feasibility; no installed profile admission."""
import json,tempfile,shutil
from pathlib import Path
import psycopg
from truss import LocalPostgres
root=Path(tempfile.mkdtemp(prefix='truss-role-lock-'));observations=[]
try:
 with LocalPostgres(root/'data') as runtime:
  params=psycopg.conninfo.conninfo_to_dict(runtime.info.connection_uri)
  with psycopg.connect(**params,autocommit=True) as admin:
   admin.execute('CREATE ROLE lock_probe LOGIN; CREATE ROLE lock_bridge NOLOGIN')
   version=admin.execute('SELECT version()').fetchone()[0]
   for table in ('pg_authid','pg_auth_members'):
    admin.execute('BEGIN')
    try:
     admin.execute('LOCK TABLE pg_catalog.'+table+' IN SHARE MODE NOWAIT')
     lock='held'
     for statement in ('ALTER ROLE lock_probe BYPASSRLS','GRANT lock_bridge TO lock_probe'):
      with psycopg.connect(**params,autocommit=True,options='-c lock_timeout=100ms') as writer:
       try:writer.execute(statement);state='committed';code=None
       except psycopg.Error as error:state='refused';code=error.sqlstate
       observations.append({'catalog':table,'lock':lock,'writer':statement,'result':state,'sqlstate':code})
    except psycopg.Error as error:observations.append({'catalog':table,'lock':'refused','sqlstate':error.sqlstate})
    finally:admin.execute('ROLLBACK');admin.execute('ALTER ROLE lock_probe NOBYPASSRLS');admin.execute('REVOKE lock_bridge FROM lock_probe')
   admin.execute('BEGIN')
   admin.execute('LOCK TABLE pg_catalog.pg_authid,pg_catalog.pg_auth_members IN SHARE MODE NOWAIT')
   for statement in ('ALTER ROLE lock_probe BYPASSRLS','GRANT lock_bridge TO lock_probe'):
    with psycopg.connect(**params,autocommit=True,options='-c lock_timeout=100ms') as writer:
     try:writer.execute(statement);state='committed';code=None
     except psycopg.Error as error:state='refused';code=error.sqlstate
     assert (state,code)==('refused','55P03')
     observations.append({'catalog':'both','writer':statement,'result':state,'sqlstate':code})
   admin.execute('ROLLBACK')
   with psycopg.connect(**params,autocommit=True,options='-c lock_timeout=100ms') as writer:
    writer.execute('ALTER ROLE lock_probe BYPASSRLS');writer.execute('GRANT lock_bridge TO lock_probe')
    assert writer.execute("SELECT rolbypassrls,pg_catalog.pg_has_role('lock_probe','lock_bridge','MEMBER') FROM pg_catalog.pg_roles WHERE rolname='lock_probe'").fetchone()==(True,True)
   observations.append({'afterRollback':'both writers committed with exact flag/membership readback'})
   admin.execute('ALTER ROLE lock_probe NOBYPASSRLS');admin.execute('REVOKE lock_bridge FROM lock_probe')
   ordinary=dict(params);ordinary['user']='lock_probe'
   with psycopg.connect(**ordinary,autocommit=True) as caller:
    caller.execute('BEGIN')
    try:caller.execute('LOCK TABLE pg_catalog.pg_authid IN SHARE MODE NOWAIT');observations.append({'ordinaryLock':'held'})
    except psycopg.Error as error:observations.append({'ordinaryLock':'refused','sqlstate':error.sqlstate})
    finally:caller.execute('ROLLBACK')
   admin.execute('DROP ROLE lock_probe; DROP ROLE lock_bridge')
 print(json.dumps({'version':version,'observations':observations,'scope':'Owned catalog lock feasibility only; no production role-custody or backend admission.'},indent=2))
finally:shutil.rmtree(root)
