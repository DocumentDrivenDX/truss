"""Administrative expression-correctness fixture, not policy qualification."""
from pathlib import Path
import json,tempfile,shutil
import psycopg
from truss import LocalPostgres
root=Path(tempfile.mkdtemp(prefix='truss-string-predicate-',dir='/private/tmp'));e=Path(__file__).parent
rows=json.loads((e/'after.json').read_text());observations=[]
try:
 with LocalPostgres(root/'data') as runtime:
  with psycopg.connect(runtime.info.connection_uri,autocommit=True) as c:
   version=c.execute("SELECT current_setting('server_version_num')").fetchone()[0];assert version=='180006'
   c.execute('CREATE SCHEMA fixture;CREATE TABLE fixture.staff(id text,native_login text);INSERT INTO fixture.staff VALUES(NULL,session_user)')
   for row in rows:
    assert 'sql' in row
    for same in [True,False]:
     value=row['value'] if same else row['value']+'different'
     c.execute('UPDATE fixture.staff SET id=%s',(value,))
     observed=c.execute('SELECT '+row['sql']).fetchone()[0];assert observed is same
     observations.append({'constant':row['value'],'subject':value,'expected':same,'observed':observed})
 (e/'native.json').write_text(json.dumps({'version':version,'observations':observations,'cleanup':'LocalPostgres context exited without error; no independent stop receipt','scope':'SQL expression correctness only; excluded administrative fixture, no authenticated ordinary policy admission'},indent=2)+'\n')
finally:shutil.rmtree(root,ignore_errors=True)
