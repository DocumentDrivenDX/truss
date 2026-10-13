"""Original source AST gates/branch ordering only; no native/container/network setup."""
from pathlib import Path
import ast,hashlib,itertools,json,types
ROOT=Path('/private/tmp/truss-security-main-integration')
SERVICE=ROOT/'scripts/security_channel_composition_service.py'
COMPOSE=Path('/private/tmp/truss-security-linux-composition/compose.py')
OUT=Path(__file__).resolve().parent
st=ast.parse(SERVICE.read_text());ct=ast.parse(COMPOSE.read_text());rows=[]
fn=next(n for n in st.body if isinstance(n,ast.FunctionDef) and n.name=='serve')
class Entered(Exception):pass
calls=[]
def factory(*args):calls.append(True);raise Entered()
env={'native':types.SimpleNamespace(AuthenticatedCatalogChannelTests=factory)}
exec(compile(ast.Module(body=[fn],type_ignores=[]),str(SERVICE),'exec'),env)
fields=('refuse_event_triggers','refuse_helper_public_grant','refuse_helper_owner')
for field in fields:
 for value in (None,0,1,[],(),{},b'',object(),'','False'):
  calls.clear()
  try:env['serve'](**{field:value})
  except ValueError as err:assert str(err)=='Exact owner fixture mode required'
  else:raise AssertionError(field)
  assert not calls;rows.append({'control':field+':nonbool:'+str(len(rows)),'passed':True})
for flags in itertools.product((False,True),repeat=3):
 calls.clear()
 try:env['serve'](**dict(zip(fields,flags)))
 except Entered:assert sum(flags)<=1 and calls==[True]
 except ValueError as err:assert sum(flags)>1 and not calls and str(err)=='Exact owner fixture mode required'
 else:raise AssertionError(flags)
 rows.append({'control':'boolean_flags:'+str(flags),'passed':True})
options=('--refuse-event-triggers','--refuse-helper-public-grant','--refuse-helper-owner')
cases=[([],True)]+[([v],True) for v in options]+[(list(v),False) for v in itertools.product(options,repeat=2)]+[(list(options),False),(['bad'],False),([options[2]+'=true'],False),(['--refuse-helper-owner','false'],False),(['--'],False)]
for args,ok in cases:
 for name,body in [('service_cli',[st.body[-1]]),('orchestrator_cli',ct.body[1:3])]:
  invoked=[];e={'__name__':'__main__','sys':types.SimpleNamespace(argv=['script']+args),'serve':lambda **kw:invoked.append(kw)}
  try:exec(compile(ast.Module(body=body,type_ignores=[]),name,'exec'),e)
  except ValueError:assert not ok and not invoked
  else:
   assert ok
   if name=='service_cli':assert invoked==[{field:args==[option] for field,option in zip(fields,options)}]
   else:assert e['refuse'] is bool(args)
  rows.append({'control':name+':'+repr(args),'passed':True})
# Execute the unchanged native setup branch against a call recorder. This checks
# composition/commit order, not PostgreSQL semantics or transaction success.
try_body=next(n for n in fn.body if isinstance(n,ast.Try)).body
branch=next(n for n in try_body if isinstance(n,ast.If) and ast.unparse(n.test)=='refuse_helper_owner or refuse_helper_public_grant')
for owner,grant in [(False,False),(False,True),(True,False)]:
 events=[]
 class Admin:
  def execute(self,sql):events.append(('execute',sql))
  def commit(self):events.append(('commit',))
 class Host:
  def detach(self):events.append(('detach',))
  def adopt_transaction(self):events.append(('adopt_transaction',));return types.SimpleNamespace(value='fresh-tx')
 fixture=types.SimpleNamespace(admin=Admin(),host=Host(),tx='old-tx')
 def adopt(admin):assert admin is fixture.admin;events.append(('adopt_host',));return Host()
 env={'refuse_helper_owner':owner,'refuse_helper_public_grant':grant,'fixture':fixture,'adopt_psycopg_host':adopt}
 exec(compile(ast.Module(body=[branch],type_ignores=[]),str(SERVICE),'exec'),env)
 if owner or grant:
  sql='ALTER FUNCTION truss.catalog_subject_current(text) OWNER TO postgres' if owner else 'GRANT EXECUTE ON FUNCTION truss.catalog_subject_current(text) TO PUBLIC'
  assert events==[('execute',sql),('detach',),('commit',),('execute','BEGIN'),('adopt_host',),('adopt_transaction',)]
  assert fixture.tx=='fresh-tx'
 else:assert events==[] and fixture.tx=='old-tx'
 rows.append({'control':'mutation_commit_order:'+str((owner,grant)),'passed':True})
result={'scope':'Original source AST owner-mode/CLI gates and recorded mutation/commit/re-adoption ordering; no native/Docker/network operation or production proof','passed':len(rows),'controls':rows,'sourceSha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [SERVICE,COMPOSE]}}
(OUT/'owner-mode-results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'passed':len(rows),'sourceSha256':result['sourceSha256']}))
