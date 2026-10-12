"""Ordinary-role RLS argument-route controls; not admitted backend policy."""
from pathlib import Path
import tempfile,shutil,json
from truss import LocalPostgres
import psycopg
out=Path(__file__).parent;sql=json.loads((out/'sql.json').read_text());root=Path(tempfile.mkdtemp(prefix='truss-resource-rls-',dir='/private/tmp'));observations=[]
try:
 with LocalPostgres(root/'data') as runtime:
  with psycopg.connect(runtime.info.connection_uri,autocommit=True) as admin:
   version=admin.execute('SHOW server_version_num').fetchone()[0];assert version=='180006'
   admin.execute('CREATE ROLE abac_reader LOGIN NOSUPERUSER NOBYPASSRLS;CREATE SCHEMA fixture;GRANT USAGE ON SCHEMA fixture TO abac_reader;CREATE TABLE fixture.resource(id text PRIMARY KEY,active bool);INSERT INTO fixture.resource VALUES(\'yes\',true),(\'no\',false),(\'unknown\',null)')
   admin.execute('CREATE FUNCTION fixture.eligible(text,bool) RETURNS bool LANGUAGE SQL IMMUTABLE AS $$ SELECT '+sql['plain']+' $$')
   admin.execute('ALTER TABLE fixture.resource ENABLE ROW LEVEL SECURITY;CREATE POLICY admitted_row ON fixture.resource TO abac_reader USING(fixture.eligible(id,active));GRANT SELECT ON fixture.resource TO abac_reader')
   connection=psycopg.conninfo.conninfo_to_dict(runtime.info.connection_uri);connection['user']='abac_reader'
   with psycopg.connect(**connection,autocommit=True) as reader:
    identity=reader.execute('SELECT session_user,current_user,pg_backend_pid()').fetchone();assert identity[0]==identity[1]=='abac_reader';observations.append({'id':'original-role','observed':list(identity)})
    for name,query,expected in [('ordinary-rows','SELECT id FROM fixture.resource ORDER BY id',[['yes']]),('ordinary-count','SELECT count(*) FROM fixture.resource',[[1]]),('denied-key',"SELECT id FROM fixture.resource WHERE id='no'",[])]:
     actual=[list(r) for r in reader.execute(query).fetchall()];assert actual==expected;observations.append({'id':name,'expected':expected,'observed':actual})
    forged=reader.execute("SELECT fixture.eligible('no',true)").fetchone()[0];assert forged is True;observations.append({'id':'forged-predicate-is-not-resource-authority','expected':True,'observed':forged})
    actual=reader.execute("SELECT id FROM fixture.resource WHERE id='no' AND fixture.eligible(id,true)").fetchall();assert actual==[];observations.append({'id':'forged-outer-argument-does-not-bypass-rls','expected':[],'observed':actual})
    admin.execute("UPDATE fixture.resource SET active=false WHERE id='yes'")
    actual=reader.execute('SELECT id FROM fixture.resource').fetchall();assert actual==[];observations.append({'id':'new-statement-observes-attribute-change','expected':[],'observed':actual})
   actual=[r[0] for r in admin.execute('SELECT id FROM fixture.resource ORDER BY id')];assert actual==['no','unknown','yes'];observations.append({'id':'excluded-admin-bypass','expected':['no','unknown','yes'],'observed':actual})
 (out/'rls.json').write_text(json.dumps({'version':version,'observations':observations,'scope':'Actual native ordinary-role RLS field-argument route in synthetic raw fixture; direct predicate result is deliberately shown forgeable and not authority. Not compiler-owned source/binding admission or complete lifecycle/privacy profile.','cleanup':'LocalPostgres context exited; no independent stop receipt'},indent=2)+'\n')
finally:shutil.rmtree(root,ignore_errors=True)
