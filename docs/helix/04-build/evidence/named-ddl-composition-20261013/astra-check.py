from pathlib import Path
from types import SimpleNamespace, ModuleType
from unittest.mock import patch
from dataclasses import replace
import sys,json,hashlib,subprocess
ROOT=Path('/private/tmp/truss-security-main-integration');OUT=Path(__file__).parent
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'packages/python/src')]
import truss._psycopg_epoch_cut as epoch
import truss._psycopg_fact_cut as fact
import truss._psycopg_dependency_fact_cut as dep
import security_owned_read as owned
from truss._psycopg_subject_observation import _SubjectSelection
checks=[]
def check(name,value):
 assert value,name
 checks.append({'name':name,'passed':True})
barrier=epoch._DDLBarrierComparison(20,30,'original barrier body')
def rows(b=barrier):
 suffix=(str(b.function_oid),str(b.owner_oid),'truss','runtime_fence_routine_ddl_writer','plpgsql','f','0','true','false','false','v','["search_path=pg_catalog, pg_temp"]',b.source,'false')
 return [('truss_routine_ddl_writer_barrier','ddl_command_start','A',str(b.owner_oid),'["CREATE FUNCTION", "ALTER FUNCTION", "DROP FUNCTION", "CREATE PROCEDURE", "ALTER PROCEDURE", "DROP PROCEDURE"]',*suffix),('truss_table_ddl_writer_barrier','ddl_command_start','A',str(b.owner_oid),'["CREATE TABLE", "ALTER TABLE", "DROP TABLE"]',*suffix)]
def descriptors():return [SimpleNamespace(type_code=25) for _ in range(19)]
class Cursor:
 def __init__(self,desc,actual):self.description=desc;self.actual=actual;self.executions=0;self.fetches=0
 def execute(self,*args,**kwargs):self.executions+=1
 def fetchmany(self,n):assert n==3;self.fetches+=1;return self.actual

def run(name,desc,actual,b=barrier,success=False,fetches=1,mod=epoch):
 c=Cursor(desc,actual);calls=[];entered=[]
 def shell(h,t,e,callback):entered.append(True);return callback(c)
 try:
  with patch.object(mod,'_run_fenced_epoch_operation',shell):
   result=mod._run_ddl_fenced_epoch_operation(None,None,None,b,lambda cur:calls.append(cur) or 'done')
  good=True
 except ValueError:good=False
 check(name,good==success and c.fetches==fetches and calls==([c] if success else []))
 return c
run('exact installed DDL rows call original callback once',descriptors(),rows(),success=True)
for i in range(19):
 ds=descriptors();ds[i].type_code=19
 run('foreign NAME OID '+str(i)+' refuses before fetch',ds,rows(),fetches=0)
for name,ds in [('missing',None),('short',descriptors()[:-1]),('long',descriptors()+[SimpleNamespace(type_code=25)])]:run(name+' descriptors refuse before fetch',ds,rows(),fetches=0)
for r in (0,1):
 for i in range(19):
  rs=rows();row=list(rs[r]);row[i]='changed';rs[r]=tuple(row)
  run('native barrier '+str(r)+' field '+str(i)+' drift refuses',descriptors(),rs)
for name,rs in [('missing',[]),('only routine',rows()[:1]),('only table',rows()[1:]),('extra',rows()+rows()[:1]),('swapped',list(reversed(rows()))),('null body',[rows()[0][:17]+(None,)+rows()[0][18:],rows()[1]])]:run(name+' barrier rows refuse',descriptors(),rs)
for key in ('owner_oid','function_oid'):
 for v in (0,-1,True,4294967296,'20'):
  run('bounded '+key+' rejects '+repr(v),descriptors(),rows(),replace(barrier,**{key:v}),fetches=0)
for v in ('',b'body','x'*65537):run('bounded source refuses '+str(type(v))+' length '+str(len(v)),descriptors(),rows(),replace(barrier,source=v),fetches=0)
big=replace(barrier,source='x'*65536);run('source maximum accepted',descriptors(),rows(big),big,success=True)
# Preserve actual pre-fix file and prove the new descriptor ordering changes behavior.
oldsrc=subprocess.check_output(['git','show','HEAD:packages/python/src/truss/_psycopg_epoch_cut.py'],cwd=ROOT,text=True)
(OUT/'prechange.py').write_text(oldsrc)
old=ModuleType('truss._review_epoch_prechange');sys.modules[old.__name__]=old;exec(compile(oldsrc,str(OUT/'prechange.py'),'exec'),old.__dict__)
oldbar=old._DDLBarrierComparison(20,30,barrier.source)
d=descriptors();d[0].type_code=19
run('actual HEAD predecessor fetched foreign row before refusal',d,rows(),oldbar,fetches=1,mod=old)
# Actual original coverage + dependency/fact/DDL composition, with only native epoch host shell replaced.
raw=(ROOT/'docs/helix/04-build/evidence/security-named-source-profile/requirements.json').read_bytes()
cs=json.loads(Path('/private/tmp/resource-list-review-20261013/baseline.json').read_bytes())['cells']
providers=[];relations={};columns={}
for oid,g in enumerate(cs,10):
 rel=fact._FactRelationComparison('truss',g['relation'][1],oid,20,'fact guard')
 relations[oid]=rel
 for ref,num,typ in g['fields']:
  col=fact._FactColumnComparison(ref[2],num,typ,-1,True,0)
  columns[(oid,num)]=col;providers.append(dep._DependencyFactProvider('field',tuple(ref),rel,col))
 for ref in g['associations']:providers.append(dep._DependencyFactProvider('association',tuple(ref),rel))
class CutCursor:
 def __init__(self,bad=False):self.events=[];self.description=None;self.current=None;self.actual=None;self.bad=bad
 def execute(self,stmt,args=None,**kwargs):
  s=stmt.as_string() if hasattr(stmt,'as_string') else str(stmt)
  if 'pg_catalog.pg_event_trigger' in s:
   self.current='barrier';self.actual=rows()
   if self.bad:self.actual=[self.actual[0][:2]+('D',)+self.actual[0][3:],self.actual[1]]
  elif s.startswith('LOCK TABLE'):
   self.events.append('fact-lock');return
  elif 'FROM pg_catalog.pg_class c' in s:
   rel=next(r for r in relations.values() if (r.schema,r.name)==args)
   self.current='relation';self.actual=[(str(rel.oid),'20','r','p','false','false','false')]
  elif 'FROM pg_catalog.pg_trigger t' in s:
   self.current='fact-guard';self.actual=[('A','62','0','','false','true','20','false','v','["search_path=pg_catalog, pg_temp"]','fact guard','false')]
  elif 'FROM pg_catalog.pg_attribute' in s:
   col=columns[tuple(map(int,args))];self.current='column';self.actual=[(col.name,str(col.number),str(col.type_oid),'-1','true','0','','','false')]
  else:raise AssertionError(s)
  self.events.append(self.current);self.description=[SimpleNamespace(type_code=25) for _ in self.actual[0]]
 def fetchmany(self,n):self.events.append(self.current+'-fetch');return self.actual
for enabled,bad in ((False,False),(True,False),(True,True)):
 c=CutCursor(bad);value=None;error=None
 def shell(h,t,e,cb):c.events.append('epoch');return cb(c)
 def callback(cur):assert cur is c;c.events.append('callback');return 'done'
 try:
  with patch.object(epoch,'_run_fenced_epoch_operation',shell),patch.object(fact,'_run_fenced_epoch_operation',shell):
   kw={'ddl_barrier':barrier} if enabled else {}
   value=dep._run_dependency_fact_operation(None,None,None,raw,hashlib.sha256(raw).hexdigest(),tuple(providers),callback,**kw)
 except ValueError as e:error=str(e)
 if bad:check('disabled barrier stops actual dependency chain before any fact lock or callback',error=='Exact original installed DDL barriers required' and c.events==['epoch','barrier','barrier-fetch'])
 elif enabled:check('actual dependency -> DDL -> fact -> callback ordering',value=='done' and c.events[0:3]==['epoch','barrier','barrier-fetch'] and c.events[-1]=='callback' and c.events.index('barrier-fetch')<c.events.index('fact-lock'))
 else:check('legacy actual dependency chain omits DDL qualification',value=='done' and c.events[0]=='epoch' and c.events[1]=='fact-lock' and 'barrier' not in c.events)
# Compatibility: legacy call shape, explicit barrier custody, fixed wrapper exact gates.
seen=[]
def target(*a,**kw):seen.append((a,kw));return 'done'
with patch.object(dep,'_run_fenced_fact_operation',target):
 for b in (None,barrier):dep._run_dependency_fact_operation('h','t','e',raw,hashlib.sha256(raw).hexdigest(),tuple(providers),callback,ddl_barrier=b)
check('legacy None preserves prior positional call shape',seen[0][1]=={})
check('selected barrier forwarded by exact object identity',seen[1][1]['ddl_barrier'] is barrier)
sel=_SubjectSelection(b'{}',b'{}','m','Staff','pk','actor','truss','named_subject_current',('staff_id',))
for s,b in ((None,barrier),(sel,None),(sel,object()),(object(),barrier)):
 with patch.object(owned,'_run_owned_identity_read') as inner:
  try:owned.run_ddl_fenced_named_subject_resource_read(None,None,None,None,None,s,None,b)
  except ValueError as e:check('fixed wrapper rejects before preparation '+str(len(checks)),str(e)=='Required exact subject selection and DDL barrier' and not inner.called)
  else:raise AssertionError('wrapper bypass')
with patch.object(owned,'_run_owned_identity_read',return_value='done') as inner:
 assert owned.run_ddl_fenced_named_subject_resource_read('h','t','e','r','s',sel,'i',barrier)=='done'
 kw=inner.call_args.kwargs
 check('fixed wrapper retains resource/named/subject/inspector/barrier routing',kw==dict(resource_list=True,source_profile='named',native_subject=sel,original_inspector='i',ddl_barrier=barrier))
def pin(p):p=Path(p);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
paths=[epoch.__file__,fact.__file__,dep.__file__,owned.__file__,__file__,OUT/'prechange.py',ROOT/'docs/helix/04-build/evidence/security-named-source-profile/requirements.json']
record=dict(count=len(checks),controls=checks,sourcePins=[pin(p) for p in paths],scope='Actual validators, original coverage and dependency/fact/DDL routing with synthetic native descriptors/rows and replaced epoch host shell. No native mutation or native driver/transaction/lifetime qualification.')
(OUT/'results.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'controls':len(checks),'pass':True}))
