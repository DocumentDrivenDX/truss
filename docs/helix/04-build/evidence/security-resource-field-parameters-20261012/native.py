"""Prepared parameter-expression correspondence only; excluded administrator."""
from pathlib import Path
import tempfile,shutil,json
from truss import LocalPostgres
import psycopg
out=Path(__file__).parent;sql=json.loads((out/'sql.json').read_text());root=Path(tempfile.mkdtemp(prefix='truss-resource-param-',dir='/private/tmp'));observations=[]
try:
 with LocalPostgres(root/'data') as runtime:
  with psycopg.connect(runtime.info.connection_uri,autocommit=True) as c:
   version=c.execute('SHOW server_version_num').fetchone()[0];assert version=='180006'
   c.execute('PREPARE plain(text,bool) AS SELECT '+sql['plain'])
   c.execute('PREPARE tagged(text,bigint,bool) AS SELECT '+sql['tagged'])
   for literal,expected in [('TRUE',True),('FALSE',False),('NULL',False)]:
    observed=c.execute("EXECUTE plain('r1',"+literal+")").fetchone()[0];assert observed is expected;observations.append({'statement':'plain','active':literal,'expected':expected,'observed':observed})
    for tag in [42,43]:
     observed=c.execute("EXECUTE tagged('r1',"+str(tag)+','+literal+')').fetchone()[0];wanted=expected and tag==42;assert observed is wanted;observations.append({'statement':'tagged','discriminator':tag,'active':literal,'expected':wanted,'observed':observed})
 (out/'native.json').write_text(json.dumps({'version':version,'observations':observations,'scope':'9 prepared expression controls with real native argument types; no ordinary policy admission or source/row/codec authenticity','cleanup':'LocalPostgres context exited; no independent stop receipt'},indent=2)+'\n')
finally:shutil.rmtree(root,ignore_errors=True)
