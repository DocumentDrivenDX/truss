from pathlib import Path
from types import SimpleNamespace,ModuleType
from unittest.mock import patch
import sys,json,hashlib,subprocess
ROOT=Path('/private/tmp/truss-security-main-integration');OUT=Path(__file__).parent
sys.path.insert(0,str(ROOT/'packages/python/src'))
import truss._psycopg_graph_scope as current
WIDTH={'identity':7,'before':3,'registration':1,'after':3}
context={'xid':'1','databaseOid':'2','backendPid':'3','sessionUser':'s','actingUser':'a','actorRoleOid':'4','sessionRoleOid':'5'}
ctx=json.dumps(context).encode().hex();evidence=b'original'
class Cursor:
 adapters=SimpleNamespace(register_dumper=lambda *a:None)
 def __init__(self,bad=None,prior=False):self.bad=bad;self.prior=prior;self.scope_reads=0;self.phase=None;self.description=None;self.fetches=[];self.executed=[]
 def execute(self,s,*args,**kw):
  if s.startswith('LOCK'):self.executed.append('lock');return
  if 'AS registered_types' in s:self.phase='registration'
  elif 'authorization_graph_fact_scope' in s:self.scope_reads+=1;self.phase='before' if self.scope_reads==1 else 'after'
  else:self.phase='identity'
  self.executed.append(self.phase);self.description=[SimpleNamespace(type_code=25,name='registered_types') for i in range(WIDTH[self.phase])]
  if self.bad and self.phase==self.bad[0]:
   defect=self.bad[1]
   if defect=='oid':self.description[self.bad[2]].type_code=19
   elif defect=='none':self.description=None
   elif defect=='short':self.description=self.description[:-1]
   elif defect=='long':self.description.append(SimpleNamespace(type_code=25,name='registered_types'))
   elif defect=='name':self.description[0].name='wrong'
 def fetchmany(self,n):
  self.fetches.append(self.phase)
  if self.bad and self.phase==self.bad[0]:raise RuntimeError('foreign decode entered')
  if self.phase=='identity':assert n==2;return [tuple(context.values())]
  if self.phase=='registration':assert n==2;return [('2' if self.prior else '1',)]
  assert n==33
  if self.phase=='before':return [('50',ctx,evidence.hex())] if self.prior else []
  return ([('50',ctx,evidence.hex())] if self.prior else [])+[('100',ctx,evidence.hex())]
checks=[]
def run(mod,bad=None,prior=False):
 c=Cursor(bad,prior);called=[]
 try:
  with patch.object(mod,'_run_fenced_epoch_operation',lambda h,t,e,callback:callback(c)):
   result=mod._run_graph_scope_operation(None,None,None,mod._GraphScopeComparison((100,),evidence),lambda x:called.append(x) or 'ok')
  status='ok'
 except ValueError:status='refused'
 except RuntimeError as e:assert str(e)=='foreign decode entered';status='foreign-fetch'
 return status,c,called
for prior in (False,True):
 s,c,called=run(current,prior=prior);assert s=='ok' and called==[c] and c.fetches==list(WIDTH)
 checks.append({'name':'valid '+('existing scope union' if prior else 'empty initial scope')+' completes once','passed':True})
for phase,width in WIDTH.items():
 variants=[(phase,'oid',i) for i in range(width)]+[(phase,x) for x in ('none','short','long')]+([(phase,'name')] if phase=='registration' else [])
 for bad in variants:
  s,c,called=run(current,bad);assert s=='refused' and not called and c.phase==phase and phase not in c.fetches,(bad,s,c.phase,c.fetches)
  checks.append({'name':list(bad),'passed':True,'refusalAtSelectedPhase':True,'targetFetches':0})
oldsrc=subprocess.check_output(['git','show','995a2a95:packages/python/src/truss/_psycopg_graph_scope.py'],cwd=ROOT,text=True)
(OUT/'prechange.py').write_text(oldsrc)
old=ModuleType('truss._review_graph_scope_old');sys.modules[old.__name__]=old;exec(compile(oldsrc,str(OUT/'prechange.py'),'exec'),old.__dict__)
previous=[]
for phase in WIDTH:
 s,c,called=run(old,(phase,'oid',0));assert s=='foreign-fetch' and not called and c.phase==phase
 previous.append({'phase':phase,'foreignFetchBeforeRefusal':True})
def pin(p):p=Path(p);b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
record={'count':len(checks),'controls':checks,'prechangeReproductions':previous,'scope':'Actual graph scope acquisition logic, synthetic driver descriptors/rows and replaced native epoch envelope. Includes valid initial-empty/initial-existing scopes and exact target-phase assertions. No native database mutation or driver constructor/callback sandbox qualification.','sourcePins':[pin(current.__file__),pin(__file__),pin(OUT/'prechange.py')]}
(OUT/'results.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'controls':len(checks),'prechangeReproductions':len(previous),'passed':True}))
