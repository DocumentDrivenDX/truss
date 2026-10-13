import ast,hashlib,json
from pathlib import Path
from types import SimpleNamespace
ROOT=Path('/private/tmp/truss-security-main-integration')
SOURCE=ROOT/'scripts/security_catalog_read.py'
raw=SOURCE.read_bytes();tree=ast.parse(raw)
outer=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run_owned_catalog_resource_read')
node=next(n for n in outer.body if isinstance(n,ast.FunctionDef) and n.name=='execute')
controls=[]

def run(case,drift=False):
 events=[]
 class Cursor:
  path='registered_hostile,pg_catalog'
  sets=0
  rows=[]
  def execute(self,sql,args=None,**kw):
   if "current_setting('search_path')" in sql:
    assert '::pg_catalog.text' in sql
    self.rows=[] if case=='missing-original' else [(b'x',)] if case=='nontext-original' else [(self.path,)]
   elif "set_config('search_path'" in sql:
    self.sets+=1
    self.path=args[0] if args else 'pg_catalog, pg_temp'
    self.rows=[('wrong',)] if case==f'bad-set-{self.sets}' else [(self.path,)]
    events.append(('set',self.path))
   elif sql.startswith('LOCK TABLE ONLY'):events.append(('lock',self.path));self.rows=[]
   else:raise AssertionError(sql)
  def fetchmany(self,n):assert n==2;return self.rows
 c=Cursor()
 def guard(cursor):assert cursor.path=='pg_catalog, pg_temp';events.append(('guard',cursor.path))
 def capture(cursor,request):assert cursor.path=='pg_catalog, pg_temp';events.append(('capture',cursor.path));return b'{}'
 def evaluate(*a,**k):
  assert c.path=='pg_catalog, pg_temp';events.append(('evaluate',c.path))
  if drift:c.path='changed_after_evaluation,pg_catalog'
  return SimpleNamespace(returncode=0,stdout='{}')
 env=dict(_pin_cursor=lambda c:None,guard=guard,capture_accepted_catalog=capture,original_request=b'{}',assessment=b'{}',
  _catalog_record_recipe=lambda *a:[(1,None,None,None)],transport={},document={},_text_rows=lambda *a:[],
  _catalog_record_cells=lambda *a:[],json=json,subject_key='s1',expected_guard=(b'i',b'p',1),
  subprocess=SimpleNamespace(run=evaluate),prepared=SimpleNamespace(tool=Path('fixture.ts')),ROOT=ROOT,pins=(),hashlib=hashlib,
  _read_owned_resource_receipt=lambda t:{'rows':[]})
 exec(compile(ast.Module(body=[node],type_ignores=[]),str(SOURCE),'exec'),env)
 try:r=env['execute'](c,None)
 except ValueError:
  assert case!='positive';assert not any(e[0]=='evaluate' for e in events) if case in ('missing-original','nontext-original','bad-set-1') else True
  return dict(name=case,refused=True,events=events)
 assert case=='positive' and r=={'rows':[]} and c.path=='registered_hostile,pg_catalog'
 assert [e[0] for e in events]==['set','guard','lock','capture','evaluate','set','guard','capture','set']
 return dict(name='positive-after-evaluator-path-drift' if drift else 'positive-exact-restoration',passed=True,events=events)
for case in ('positive','missing-original','nontext-original','bad-set-1','bad-set-2','bad-set-3'):controls.append(run(case))
controls.append(run('positive',True))
result=dict(scope='Actual nested execute AST with synthetic cursor/capture/evaluator seams. Pins initial and late SQL path and exact restoration; failures propagate. No native SQL execution or host rollback proof.',count=len(controls),passed=True,sourceSha256=hashlib.sha256(raw).hexdigest(),controls=controls)
Path(__file__).with_name('read-path-results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'count':len(controls),'passed':True}))
