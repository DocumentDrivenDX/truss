from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from dataclasses import replace
import ast,json,subprocess,sys,hashlib
ROOT=Path('/private/tmp/truss-security-main-integration');OUT=Path(__file__).parent
sys.path[:0]=[str(ROOT/'packages/python/src'),str(ROOT/'scripts')]
import truss._psycopg_fact_cut as fact
import truss._psycopg_epoch_cut as epoch
import security_catalog_read as read
from truss._security_mapping import PreparedSecurityMapping
checks=[]
def check(n,v):assert v,n;checks.append({'name':n,'passed':True})
old=subprocess.check_output(['git','show','HEAD:packages/python/src/truss/_psycopg_fact_cut.py'],cwd=ROOT)
(OUT/'fact-cut-pre-extraction.py').write_bytes(old)
oldfn=next(n for n in ast.parse(old).body if isinstance(n,ast.FunctionDef) and n.name=='_run_fenced_fact_operation')
newtree=ast.parse((ROOT/'packages/python/src/truss/_psycopg_fact_cut.py').read_bytes())
newfn=next(n for n in newtree.body if isinstance(n,ast.FunctionDef) and n.name=='_prepare_fenced_fact_cut')
stop=next(i for i,n in enumerate(oldfn.body) if isinstance(n,ast.If) and isinstance(n.test,ast.Compare) and isinstance(n.test.left,ast.Name) and n.test.left.id=='ddl_barrier')
check('extracted qualifier recipe and acquire body are AST-identical',ast.dump(ast.Module(body=oldfn.body[1:stop],type_ignores=[]),include_attributes=False)==ast.dump(ast.Module(body=newfn.body[1:-1],type_ignores=[]),include_attributes=False))
newwrapper=next(n for n in newtree.body if isinstance(n,ast.FunctionDef) and n.name=='_run_fenced_fact_operation')
check('original wrapper routing remains AST-identical',ast.dump(ast.Module(body=oldfn.body[stop:],type_ignores=[]),include_attributes=False)==ast.dump(ast.Module(body=newwrapper.body[2:],type_ignores=[]),include_attributes=False))
BODY=(ROOT/'packages/postgresql/native/authorization-fact-write-fence.sql').read_text().split('AS $$',1)[1].split('$$;',1)[0]
column=fact._FactColumnComparison('id',1,25,-1,True,0)
relation=fact._FactRelationComparison('truss','object',10,20,BODY,(column,))
class Cursor:
 def __init__(self,mutate=None):self.trace=[];self.mutate=mutate;self.fetches=[]
 def execute(self,s,args=(),**kwargs):
  text=s if type(s) is str else s.as_string()
  if text.startswith('LOCK TABLE'):self.trace.append('lock');return
  if 'FROM pg_catalog.pg_class' in text:stage='relation';rows=[('10','20','r','p','false','false','false')]
  elif 'FROM pg_catalog.pg_trigger' in text:stage='guard';rows=[('A','62','0','','false','true','20','false','v','["search_path=pg_catalog, pg_temp"]',BODY,'false')]
  elif 'FROM pg_catalog.pg_attribute' in text:stage='column';rows=[('id','1','25','-1','true','0','','','false')]
  else:raise AssertionError(text)
  self.stage=stage;self.trace.append(stage);self.rows=rows;self.description=[SimpleNamespace(type_code=25) for v in rows[0]]
  if self.mutate:self.mutate(self,stage)
 def fetchmany(self,n):self.fetches.append(self.stage);return self.rows[:n]
c=Cursor();seen=[];acquire=fact._prepare_fenced_fact_cut((relation,),lambda x:seen.append(x) or 'done')
check('direct prepared cut validates lock relation guard and columns before callback',acquire(c)=='done' and c.trace==['lock','relation','guard','column'] and seen==[c])
for stage,width in [('relation',7),('guard',12),('column',9)]:
 for flavor in ('foreign','missing','short','duplicate','changed'):
  def mutate(c,s,stage=stage,flavor=flavor):
   if s==stage:
    if flavor=='foreign':c.description[0].type_code=19
    elif flavor=='short':c.description.pop()
    elif flavor=='missing':c.rows=[]
    elif flavor=='duplicate':c.rows*=2
    else:r=list(c.rows[0]);r[0]='changed';c.rows=[tuple(r)]
  c=Cursor(mutate);seen=[]
  try:fact._prepare_fenced_fact_cut((relation,),lambda c:seen.append(c))(c)
  except ValueError:check(stage+' '+flavor+' refuses before callback',not seen and (flavor not in ('foreign','short') or stage not in c.fetches))
  else:raise AssertionError((stage,flavor))
for i in range(12):
 def mutate(c,s,i=i):
  if s=='guard':r=list(c.rows[0]);r[i]='changed';c.rows=[tuple(r)]
 c=Cursor(mutate);seen=[]
 try:fact._prepare_fenced_fact_cut((relation,),lambda c:seen.append(c))(c)
 except ValueError as e:check('guard field '+str(i)+' refuses',str(e)=='Exact installed ALWAYS fact guard required' and not seen)
 else:raise AssertionError(i)
for label,value in [('list',[relation]),('empty',()),('oversize',(relation,)*33),('duplicate',(relation,relation)),('wrong oid',(replace(relation,oid=True),)),('wrong columns',(replace(relation,columns=[]),)),('duplicate column',(replace(relation,columns=(column,column)),)),('empty body',(replace(relation,guard_source=''),))]:
 try:fact._prepare_fenced_fact_cut(value,lambda c:None)
 except ValueError:check(label+' input refuses at preparation',True)
 else:raise AssertionError(label)
# Capture selected immutable scalar values, not mutable dataclass slots.
r=replace(relation);col=replace(column);r=replace(r,columns=(col,));a=fact._prepare_fenced_fact_cut((r,),lambda c:'copied');object.__setattr__(r,'oid',999);object.__setattr__(col,'number',2)
check('prepared recipe retains originally copied relation and column fields',a(Cursor())=='copied')
for ddl in (False,True):
 seen=[];h=object();tx=object();comparison=object();barrier=object();c=Cursor()
 def run(*args):seen.append(args[:-1]);return args[-1](c)
 target='_run_ddl_fenced_epoch_operation' if ddl else '_run_fenced_epoch_operation';module=epoch if ddl else fact
 with patch.object(module,target,run):answer=fact._run_fenced_fact_operation(h,tx,comparison,(relation,),lambda c:'answer',**({'ddl_barrier':barrier} if ddl else {}))
 check(('DDL' if ddl else 'legacy')+' wrapper forwards original identity and executes same prepared callback',answer=='answer' and seen==[(h,tx,comparison,barrier) if ddl else (h,tx,comparison)])
# New selected path around actual capture projection and actual original evaluator, with synthetic catalog/host shell.
E=ROOT/'docs/helix/04-build/evidence/accepted-catalog-policy-read-20261013';request=(E/'request.json').read_bytes();assessment=(E/'assessment.json').read_bytes();packet=json.loads((E/'capture.json').read_bytes())[0];decision=json.loads((E/'decision.json').read_bytes())
mapping=PreparedSecurityMapping(request,(E/'owner-response.json').read_bytes(),accepted_catalog_assessment=assessment)
class Host:
 def __init__(self,c):self.cursor=c;self.entered=0
 def _observe(self,c):c.trace.append('observe');return None
 def _run_operation(self,t,callback):self.entered+=1;return callback(self.cursor,None)
def invoke(relations,mutate=None):
 c=Cursor(mutate);h=Host(c);captures=[]
 def capture(c,req):c.trace.append('capture');captures.append(req);return assessment
 def rows(c,*args):c.trace.append('rows');return packet['rows']
 try:
  with patch.object(read,'_pin_cursor',lambda c:c.trace.append('pin')),patch.object(read,'capture_accepted_catalog',capture),patch.object(read,'_text_rows',rows):r=read.run_owned_catalog_resource_read(h,None,mapping,'s1',fact_relations=relations)
  error=None
 except ValueError as e:r=None;error=str(e)
 return r,error,h,c,captures
r,e,h,c,caps=invoke((relation,));check('selected object guard completes genuine original evaluation after qualifying cut',r==decision and e is None and c.trace.index('column')<c.trace.index('observe')<c.trace.index('capture')<c.trace.index('rows') and len(caps)==2)
def disabled(c,s):
 if s=='guard':c.rows=[('D',)+c.rows[0][1:]]
r,e,h,c,caps=invoke((relation,),disabled);check('disabled selected guard refuses before native catalog capture and evaluator',r is None and e=='Exact installed ALWAYS fact guard required' and not caps and 'rows' not in c.trace)
for label,relations in [('list',[relation]),('empty',()),('other home',(replace(relation,name='edge'),)),('extra home',(relation,relation)),('wrong type',(object(),))]:
 r,e,h,c,caps=invoke(relations);check(label+' selected binding refuses before host',r is None and e=='Exact accepted object fact cut required' and h.entered==0)
r,e,h,c,caps=invoke(None);check('explicit legacy None avoids guard factory and preserves original result',r==decision and not any(t in c.trace for t in ('guard','relation','observe','column')))
def pin(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
record={'count':len(checks),'controls':checks,'scope':'AST extraction/routing equivalence and actual current qualifier/guarded orchestrator with synthetic native rows and host/capture shells. New selected and legacy paths execute genuine original UMF evaluator on retained actual capture rows. No independently executed native lock/trigger or host containment assertion.','sourcePins':[pin(ROOT/n) for n in ['packages/python/src/truss/_psycopg_fact_cut.py','scripts/security_catalog_read.py','packages/postgresql/native/authorization-fact-write-fence.sql']]+[pin(Path(__file__)),pin(OUT/'fact-cut-pre-extraction.py')],'inputPins':[pin(E/n) for n in ['request.json','assessment.json','capture.json','decision.json']]}
(OUT/'guard-results.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'controls':len(checks),'passed':True}))
