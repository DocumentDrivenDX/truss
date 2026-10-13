from pathlib import Path
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import patch
import sys,json,hashlib
ROOT=Path('/private/tmp/truss-security-main-integration');OUT=Path(__file__).parent
sys.path[:0]=[str(ROOT/'packages/python/src'),str(ROOT/'scripts')]
import truss._psycopg_epoch_cut as epoch
barrier=epoch._DDLBarrierComparison(20,30,'body');checks=[]
def check(n,p):assert p,n;checks.append({'name':n,'passed':True})
def descriptors():return [SimpleNamespace(type_code=25) for _ in range(19)]
def rows(b):
 suffix=('30','20','truss','runtime_fence_routine_ddl_writer','plpgsql','f','0','true','false','false','v','["search_path=pg_catalog, pg_temp"]','body','false')
 rs=[('truss_routine_ddl_writer_barrier','ddl_command_start','A','20','["CREATE FUNCTION", "ALTER FUNCTION", "DROP FUNCTION", "CREATE PROCEDURE", "ALTER PROCEDURE", "DROP PROCEDURE"]',*suffix),('truss_table_ddl_writer_barrier','ddl_command_start','A','20','["CREATE TABLE", "ALTER TABLE", "DROP TABLE"]',*suffix)]
 if b.include_alter_routine:rs.append(('truss_z_routine_ddl_writer_barrier','ddl_command_start','A','20','["ALTER ROUTINE"]',*suffix))
 return rs
class Cursor:
 def __init__(self,d,r):self.description=d;self.rows=r;self.fetched=[];self.executed=[]
 def execute(self,*args,**kw):self.executed.append((args,kw))
 def fetchmany(self,n):self.fetched.append(n);return self.rows

def run(name,b,d,r,success=False,fetch=True):
 c=Cursor(d,r);called=[];entered=[]
 def shell(h,t,e,fn):entered.append(True);return fn(c)
 try:
  with patch.object(epoch,'_run_fenced_epoch_operation',shell):result=epoch._run_ddl_fenced_epoch_operation(None,None,None,b,lambda cur:called.append(cur) or 'done')
  ok=True
 except ValueError:ok=False
 check(name,ok==success and called==([c] if success else []) and c.fetched==([4 if b.include_alter_routine is True else 3] if fetch else []))
 return c,entered
check('new field default is exact False',barrier.include_alter_routine is False)
run('legacy two rows accept default',barrier,descriptors(),rows(barrier),True)
extended=replace(barrier,include_alter_routine=True)
run('explicit True requires and accepts third original hook',extended,descriptors(),rows(extended),True)
run('optin missing third hook refuses',extended,descriptors(),rows(barrier))
run('optin extra returned hook refuses',extended,descriptors(),rows(extended)+rows(extended)[-1:])
run('optin wrong row order refuses',extended,descriptors(),list(reversed(rows(extended))))
for i in range(19):
 rs=rows(extended);last=list(rs[-1]);last[i]='changed';rs[-1]=tuple(last)
 run('supplementary hook exact field '+str(i)+' drift refuses',extended,descriptors(),rs)
for val in (None,0,1,'true',[],object()):
 c,entered=run('nonbool selection refuses before host '+repr(val),replace(barrier,include_alter_routine=val),descriptors(),rows(extended),fetch=False)
 check('nonbool host not entered '+str(len(checks)),not entered and not c.executed)
for b in (barrier,extended):
 for i in range(19):
  ds=descriptors();ds[i].type_code=19
  run('before-fetch foreign descriptor '+str(b.include_alter_routine)+' '+str(i),b,ds,rows(b),fetch=False)
 for name,d in [('missing',None),('short',descriptors()[:-1]),('long',descriptors()+[SimpleNamespace(type_code=25)])]:run(name+' descriptor '+str(b.include_alter_routine),b,d,rows(b),fetch=False)
# Capture exact bool before the epoch host wrapper is entered.
changing=replace(extended);c=Cursor(descriptors(),rows(extended));called=[]
def mutate_shell(h,t,e,fn):object.__setattr__(changing,'include_alter_routine',False);return fn(c)
with patch.object(epoch,'_run_fenced_epoch_operation',mutate_shell):result=epoch._run_ddl_fenced_epoch_operation(None,None,None,changing,lambda c:called.append(True) or 'done')
check('selected bool captured before host entry mutation',result=='done' and called==[True] and c.fetched==[4])
def pin(p):p=Path(p);b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
(OUT/'results.json').write_text(json.dumps({'count':len(checks),'controls':checks,'sourcePins':[pin(epoch.__file__),pin(__file__)],'scope':'Actual qualification function with synthetic native epoch host and catalog descriptor/row carriers; no native effects or independent DDL event semantics.'},indent=2)+'\n')
print(json.dumps({'controls':len(checks),'passed':True}))
