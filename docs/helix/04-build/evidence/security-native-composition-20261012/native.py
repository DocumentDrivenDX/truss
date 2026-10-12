"""Administrative SQL truth matrix, not complete fact/caller admission."""
from pathlib import Path
import json,tempfile,shutil
import psycopg
from truss import LocalPostgres
root=Path(tempfile.mkdtemp(prefix='truss-composition-',dir='/private/tmp'));e=Path(__file__).parent
packet=json.loads((e/'cases.json').read_text());observations=[]
try:
 with LocalPostgres(root/'data') as runtime:
  with psycopg.connect(runtime.info.connection_uri,autocommit=True) as c:
   version=c.execute("SELECT current_setting('server_version_num')").fetchone()[0];assert version=='180006'
   c.execute('CREATE SCHEMA fixture;CREATE TABLE fixture.staff(native_login text,p1 bool,p2 bool,required bool,forbidden bool);INSERT INTO fixture.staff VALUES(session_user,NULL,NULL,NULL,NULL)')
   for case in packet['cases']:
    values=[{'T':True,'F':False,'U':None}[x] for x in case['truths']]
    c.execute('UPDATE fixture.staff SET p1=%s,p2=%s,required=%s,forbidden=%s',values)
    actual=c.execute('SELECT '+packet['sql']).fetchone()[0];assert actual is case['expected'],case
    observations.append({**case,'observed':actual})
 (e/'native.json').write_text(json.dumps({'postgres':version,'observations':observations,'cleanup':'LocalPostgres context exited without error; no independent stop receipt','limits':'Administrative raw truth fixture. NULL exercises U only; required source domains do not admit nullable physical bindings. No complete fact/issuer/source/caller/mask/publication admission.'},indent=2)+'\n')
finally:shutil.rmtree(root,ignore_errors=True)
