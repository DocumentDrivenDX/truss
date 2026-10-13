from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from dataclasses import replace,dataclass
import ast,json,runpy,hashlib,subprocess
OUT=Path(__file__).parent
ns=runpy.run_path(str(OUT/'legacy_check.py'))
ROOT=ns['ROOT'];read=ns['read'];PsycopgHost=ns['PsycopgHost'];Ok=ns['Ok'];Error=ns['Error'];ExecutionFailure=ns['ExecutionFailure']
import truss._psycopg_fact_cut as fact
BODY=(ROOT/'packages/postgresql/native/authorization-fact-write-fence.sql').read_text().split('AS $$',1)[1].split('$$;',1)[0]
OWNER=ns['OWNER'];checks=[]
def check(n,v):assert v,n;checks.append({'name':n,'passed':True})
old=(OUT/'fact-cut-before-existing-mode.py').read_bytes()
def function(raw):return next(n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name=='_prepare_fenced_fact_cut')
a=function(old);b=function((ROOT/'packages/python/src/truss/_psycopg_fact_cut.py').read_bytes())
# Remove only the new exact-bool guard and select the legacy lock-acquisition branch.
b.body.pop(1);nested=next(n for n in b.body if isinstance(n,ast.FunctionDef) and n.name=='acquire');loop=nested.body[1];assert isinstance(loop,ast.For) and isinstance(loop.body[0],ast.If);loop.body[:1]=loop.body[0].orelse
check('default acquisition and existing qualification body remain AST-identical',ast.dump(ast.Module(body=a.body[1:],type_ignores=[]),include_attributes=False)==ast.dump(ast.Module(body=b.body[1:],type_ignores=[]),include_attributes=False))
base=(fact._FactRelationComparison('truss','object',10,int(OWNER),BODY),fact._FactRelationComparison('truss','catalog_subject_map',11,int(OWNER),BODY))
class Cursor(ns['Cursor']):
 def __init__(self,change=None):super().__init__(change);self.trace=[];self.current_oid=None
 def execute(self,statement,args=(),**kw):
  text=statement if type(statement) is str else statement.as_string()
  if text.startswith('LOCK TABLE'):
   self.trace.append(('lock',text));return
  if 'SELECT EXISTS(SELECT 1 FROM pg_catalog.pg_locks' in text:
   stage='held';self.current_oid=int(args[0]);rows=[('true',)];names=['held']
   assert all(fragment in text for fragment in ["l.locktype OPERATOR(pg_catalog.=) 'relation'","l.pid OPERATOR(pg_catalog.=) pg_catalog.pg_backend_pid()","l.database OPERATOR(pg_catalog.=)","pg_catalog.current_database()","l.relation OPERATOR(pg_catalog.=) %s::pg_catalog.oid","l.mode OPERATOR(pg_catalog.=) 'ShareLock'","AND l.granted"])
   assert kw=={'prepare':False,'binary':False}
  elif text.startswith('SELECT c.oid'):
   stage='relation';self.current_oid=10 if args[1]=='object' else 11;rows=[(str(self.current_oid),OWNER,'r','p','false','false','false')];names=['r'+str(i) for i in range(7)]
  elif 'FROM pg_catalog.pg_trigger' in text:
   stage='guard';self.current_oid=int(args[0]);rows=[('A','62','0','','false','true',OWNER,'false','v','["search_path=pg_catalog, pg_temp"]',BODY,'false')];names=['g'+str(i) for i in range(12)]
  else:
   super().execute(statement,args,**kw);self.trace.append((self.stage,self.current_oid));return
  self.stage=stage;self.rows=rows;self.description=[SimpleNamespace(name=n,type_code=25) for n in names];self.trace.append((stage,self.current_oid))
  if self.change:self.change(self,stage)
for mode in (False,True):
 c=Cursor();seen=[];answer=fact._prepare_fenced_fact_cut(base,lambda c:seen.append(c) or 'done',existing_locks=mode)(c)
 check(('existing' if mode else 'default')+' mode qualifies both homes before callback',answer=='done' and seen==[c] and sum(v[0]=='guard' for v in c.trace)==2 and sum(v[0]=='held' for v in c.trace)==(2 if mode else 0) and sum(v[0]=='lock' for v in c.trace)==(0 if mode else 2))
for value in (None,0,1,'true',[],object()):
 try:fact._prepare_fenced_fact_cut(base,lambda c:None,existing_locks=value)
 except ValueError as e:check('non-bool mode '+type(value).__name__+' '+str(len(checks))+' refuses',str(e)=='Exact fact lock acquisition mode required')
 else:raise AssertionError(value)
for label,modify in [('foreign',lambda c:setattr(c.description[0],'type_code',19)),('missing descriptor',lambda c:setattr(c,'description',None)),('extra descriptor',lambda c:c.description.append(SimpleNamespace(type_code=25))),('false',lambda c:setattr(c,'rows',[('false',)])),('NULL',lambda c:setattr(c,'rows',[(None,)])),('bool',lambda c:setattr(c,'rows',[(True,)])),('empty',lambda c:setattr(c,'rows',[])),('duplicate',lambda c:setattr(c,'rows',[('true',),('true',)]))]:
 def change(c,s,modify=modify):
  if s=='held':modify(c)
 c=Cursor(change);seen=[]
 try:fact._prepare_fenced_fact_cut(base,lambda c:seen.append(c),existing_locks=True)(c)
 except ValueError:check('existing lock '+label+' refuses before qualification/callback',not seen and not any(v[0] in ('relation','guard','lock') for v in c.trace) and (label not in ('foreign','missing descriptor','extra descriptor') or 'held' not in c.fetches))
 else:raise AssertionError(label)
# Exact copied recipe custody before inspector. Native/host/executor are synthetic; original inspector+codec run.
def invoke(change=None,relations=None,mutate_inputs=False):
 rels=tuple(replace(r) for r in base) if relations is None else relations
 caller=object.__new__(PsycopgHost);executor=object.__new__(PsycopgHost);caller._review_cursor=Cursor(change);executor._review_cursor=Cursor(change)
 events=[];errors=[];encoded=[];selected=[];inspected=[];real_encoder=read.encode_literal_key_tuple
 def inspector(request,probe):
  inspected.append(True)
  if mutate_inputs:
   for r in rels:object.__setattr__(r,'oid',999)
  return ns['weft'].inspect_security_mapping_subject_key_json(request,probe)
 def op(host,tx,callback):
  events.append('caller' if host is caller else 'executor-environment')
  try:return Ok(callback(host._review_cursor,ns['OBSERVED']))
  except Exception as e:errors.append(e);return Error(ExecutionFailure('execution_obligation','synthetic shell'))
 def encode(*a,**k):
  encoded.append(list(caller._review_cursor.trace));return real_encoder(*a,**k)
 def evaluate(host,tx,mapping,subject,*,fact_relations):
  assert host is executor and subject=='s1';selected.append(fact_relations);events.append('evaluate');caller._review_cursor.after=True;return Ok(ns['DECISION'])
 with patch.object(PsycopgHost,'_run_operation',op),patch.object(PsycopgHost,'_observe',lambda self,c:ns['OBSERVED']),patch.object(read,'_pin_cursor',lambda c:None),patch.object(read,'encode_literal_key_tuple',encode),patch.object(read,'run_owned_catalog_resource_read',evaluate):
  try:result=read.run_guarded_native_catalog_resource_read(caller,None,executor,None,ns['mapping'],ns['selection'],inspector,rels)
  except Exception as e:errors.append(e);result=None
 return result,events,errors,encoded,selected,inspected,caller._review_cursor,rels
r,events,errors,enc,selected,inspected,c,rels=invoke()
check('guarded composite executes genuine inspector and both original codecs',isinstance(r,Ok) and r.value==ns['DECISION'] and len(enc)==2 and events==['caller','executor-environment','evaluate'])
check('both caller object and map qualified before both encodings',all(sum(stage=='held' for stage,oid in trace)==2*(i+1) and sum(stage=='guard' for stage,oid in trace)==2*(i+1) for i,trace in enumerate(enc)) and not any(stage=='lock' for stage,oid in c.trace))
check('executor receives only copied object guard',len(selected)==1 and len(selected[0])==1 and selected[0][0].name=='object' and selected[0][0].oid==10 and selected[0][0] is not rels[0])
r,events,errors,enc,selected,inspected,c,rels=invoke(mutate_inputs=True)
check('inspector cannot replace original copied caller or executor guard OIDs',isinstance(r,Ok) and len(enc)==2 and selected[0][0].oid==10 and all(v.oid==999 for v in rels))
for oid in (10,11):
 for stage in ('held','guard'):
  def change(c,s,oid=oid,stage=stage):
   if s==stage and c.current_oid==oid:c.rows=[('false',)] if s=='held' else [('D',)+c.rows[0][1:]]
  r,events,errors,enc,selected,inspected,c,rels=invoke(change)
  check(str(oid)+' '+stage+' refuses before codec and executor',isinstance(r,Error) and not enc and not selected and events==['caller'])
for stage in ('held','guard'):
 def change(c,s,stage=stage):
  if c.after and s==stage:c.rows=[('false',)] if s=='held' else [('D',)+c.rows[0][1:]]
 r,events,errors,enc,selected,inspected,c,rels=invoke(change)
 check('late '+stage+' refusal prevents second codec and result',isinstance(r,Error) and len(enc)==1 and len(selected)==1)
for label,relations in [('list',list(base)),('empty',()),('one',(base[0],)),('duplicate',(base[0],base[0])),('foreign',(base[0],object()))]:
 r,events,errors,enc,selected,inspected,c,rels=invoke(relations=relations);check(label+' selected set refuses before inspector and hosts',r is None and not inspected and not events)
# Mandatory None gate is separate from the intentional legacy None behavior.
with patch.object(read,'run_owned_native_catalog_resource_read') as delegate:
 try:read.run_guarded_native_catalog_resource_read(None,None,None,None,None,None,None,None)
 except ValueError as e:check('mandatory None never delegates to legacy',str(e)=='Mandatory native caller fact cuts required' and not delegate.called)
 else:raise AssertionError('None')
# Regression for pre-copy validation: do not iterate non-tuples or invoke foreign constructors.
column=fact._FactColumnComparison('id',1,25,-1,True,0);visits=[]
def gen():visits.append(True);yield column
construction=[]
@dataclass
class Foreign:
 value:int=0
 def __post_init__(self):construction.append(True)
f=Foreign();construction.clear()
for label,columns in [('list',[column]),('generator',gen()),('foreign',(f,)),('oversize',(column,)*1601)]:
 r,events,errors,enc,selected,inspected,c,rels=invoke(relations=(replace(base[0],columns=columns),base[1]));check(label+' columns refuse before inspector and host',r is None and not events and not inspected)
check('non-tuple generator never iterated and foreign constructor never called',not visits and not construction)
def pin(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
record={'count':len(checks),'controls':checks,'scope':'Actual current lock qualifier and composite orchestration with synthetic native rows, exact-type host shells and delegated evaluator. Original Weft inspector and UMF key encoder execute. Lock SQL predicates and descriptor-before-fetch are inspected; no native lock/privilege/host-containment theorem.','sourcePins':[pin(ROOT/n) for n in ['packages/python/src/truss/_psycopg_fact_cut.py','scripts/security_catalog_subject_read.py','scripts/security_catalog_read.py','scripts/security-catalog-subject.sql']]+[pin(Path(__file__)),pin(OUT/'fact-cut-before-existing-mode.py')]}
(OUT/'guarded-results.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'guardedControls':len(checks),'passed':True}))
