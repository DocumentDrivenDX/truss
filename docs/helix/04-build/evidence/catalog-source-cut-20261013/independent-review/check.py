from pathlib import Path
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import patch
import json,hashlib
import security_catalog_subject_read as read
import truss._psycopg_epoch_cut as epoch
import truss._psycopg_fact_cut as fact
from truss.execution import Ok,Error,ExecutionFailure
from truss.psycopg_host import PsycopgHost
ROOT=Path('/private/tmp/truss-security-main-integration');OUT=Path(__file__).parent;records=[]
request=b'original fixture request';mapping=read.PreparedSecurityMapping(request,b'{}',accepted_catalog_assessment=b'original assessment')
selection=read._SubjectSelection(request,(read.BASE/'document.json').read_bytes(),'m','Staff','pk','consumer','truss','catalog_subject_current',('staff_id',))
relations=(fact._FactRelationComparison('truss','object',10,12,'body'),fact._FactRelationComparison('truss','catalog_subject_map',11,12,'body'))
base=(epoch._EpochComparison('installation','epoch','incarnation',b'profile',b'evidence'),epoch._DDLBarrierComparison(12,13,'source',False))
class Cursor:
 def execute(self,q,*a,**k):
  self.context='catalog_subject_context' in q
  names=('installation_id','database_oid','role_oid') if self.context else ('installation_id','database_oid')
  self.description=[SimpleNamespace(name=n,type_code=25) for n in names]
 def fetchmany(self,n):return [('installation','db','role') if self.context else ('installation','db')]

def invoke(cut='default',rels=relations,fail_at=0,mutate=False,audience_mutation=None):
 cut=tuple(replace(v) for v in base) if cut=='default' else cut
 caller=object.__new__(PsycopgHost);executor=object.__new__(PsycopgHost);events=[];seen=[];delivered=[];errors=[];cursor=Cursor()
 def prepare(host,sel,inspector,produce,profiles):
  events.append('inspector')
  if mutate:
   object.__setattr__(cut[0],'epoch','changed');object.__setattr__(cut[1],'function_oid',999)
  def observe(c,o):events.append('subject');return produce(SimpleNamespace(identity=('m','Staff','pk'),values=('s1',)))
  return observe
 def qualify(host,tx,comp,barrier,callback):
  assert host is executor;seen.append((comp,barrier));events.append('source'+str(len(seen)))
  if len(seen)==fail_at:return Error(ExecutionFailure('execution_obligation','synthetic epoch refusal'))
  class Audience:
   def execute(self,q,*a,**k):
    self.description=[SimpleNamespace(type_code=25)];self.rows=[('installation',)];self.fetches=0
    if audience_mutation:audience_mutation(self,len(seen))
   def fetchmany(self,n):self.fetches+=1;return self.rows[:n]
  c=Audience()
  try:r=callback(c)
  except Exception as e:
   errors.append(e)
   if c.description is None or len(c.description)!=1 or c.description[0].type_code!=25:assert c.fetches==0
   return Error(ExecutionFailure('execution_obligation','synthetic epoch host refused audience'))
  return Ok(r)
 def operation(host,tx,callback):
  events.append('caller' if host is caller else 'environment')
  try:return Ok(callback(cursor,None))
  except Exception as e:errors.append(e);return Error(ExecutionFailure('execution_obligation','synthetic host refusal'))
 def published(host,tx,callback,publisher):
  result=operation(host,tx,callback)
  if isinstance(result,Ok):publisher(result.value)
  return result
 def evaluate(*a,**k):events.append('evaluate');return Ok({'kind':'synthetic decision','rows':[]})
 def encode(*a,**k):events.append('key');return SimpleNamespace(tuple_bytes=b'key')
 def helper(*a):events.append('helper')
 def prepare_fact(*a,**k):return lambda c:events.append('fact')
 def sink(v):events.append('publish');delivered.append(v)
 with patch.object(read,'_prepare_subject_operation',prepare),patch.object(read,'_verify_helpers',helper),patch.object(read,'_pin_cursor',lambda c:None),patch.object(read,'encode_literal_key_tuple',encode),patch.object(read,'run_owned_catalog_resource_read',evaluate),patch.object(epoch,'_run_ddl_fenced_epoch_operation',qualify),patch.object(fact,'_prepare_fenced_fact_cut',prepare_fact),patch.object(PsycopgHost,'_run_operation',operation),patch.object(PsycopgHost,'_run_published_operation',published),patch.object(PsycopgHost,'_observe',lambda *a:None):
  try:r=read.publish_ddl_epoch_guarded_native_catalog_resource_read(caller,None,executor,None,mapping,selection,lambda *a:None,rels,cut,sink)
  except Exception as e:errors.append(e);r=None
 return r,events,seen,delivered,errors,cut

def check(n,v):assert v,n;records.append({'name':n,'passed':True})
r,ev,seen,out,err,cut=invoke()
check('source acquisition precedes helper/subject and requalification precedes publication',isinstance(r,Ok) and ev==['inspector','caller','source1','helper','subject','fact','key','environment','evaluate','helper','subject','fact','key','source2','publish'])
check('source cut copies retain exact original values and native qualifier identity',len(seen)==2 and all(pair==base for pair in seen) and all(seen[0][i] is not cut[i] for i in range(2)))
check('publisher receives exact immutable serialized decision',len(out)==1 and type(out[0]) is bytes and json.loads(out[0])=={'kind':'synthetic decision','rows':[]})
r,ev,seen,out,err,cut=invoke(mutate=True)
check('inspector mutation of caller-owned comparisons cannot replace copied cuts',isinstance(r,Ok) and all(pair==base for pair in seen) and cut[0].epoch=='changed' and cut[1].function_oid==999)
for stage in (1,2):
 r,ev,seen,out,err,cut=invoke(fail_at=stage)
 check('source qualification '+str(stage)+' refusal prevents sink',isinstance(r,Error) and not out and str(err[-1])=='Original executor source epoch and DDL barrier refused')
 check('source qualification '+str(stage)+' expected downstream work',ev.count('key')==(0 if stage==1 else 2) and ev.count('evaluate')==(0 if stage==1 else 1))
for label,cut in [('None',None),('list',list(base)),('empty',()),('one',(base[0],)),('reversed',base[::-1]),('foreign',(object(),base[1]))]:
 r,ev,seen,out,err,cut=invoke(cut=cut);check(label+' source cut refuses before inspector/host',r is None and not ev and not out and isinstance(err[0],ValueError))
r,ev,seen,out,err,cut=invoke(rels=None);check('mandatory missing fact guard never downgrades',r is None and not ev and not out)
for label,change in [
 ('missing descriptor',lambda c:setattr(c,'description',None)),
 ('wrong OID',lambda c:setattr(c.description[0],'type_code',19)),
 ('extra descriptor',lambda c:c.description.append(SimpleNamespace(type_code=25))),
 ('wrong installation',lambda c:setattr(c,'rows',[('other',)])),
 ('empty row',lambda c:setattr(c,'rows',[])),
 ('duplicate row',lambda c:setattr(c,'rows',[('installation',)]*2)),
 ('null',lambda c:setattr(c,'rows',[(None,)]))]:
 for stage in (1,2):
  def mutate(c,n,stage=stage,change=change):
   if n==stage:change(c)
  r,ev,seen,out,err,cut=invoke(audience_mutation=mutate)
  check('audience '+label+' at qualification '+str(stage)+' refuses with no sink',isinstance(r,Error) and not out and ev.count('key')==(0 if stage==1 else 2))
record={'scope':'Actual new orchestration and shape checks with synthetic native epoch, helper, inspector, key producer, evaluator and host shells; no native or semantic refinement claim','controls':records,'sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['scripts/security_catalog_subject_read.py','packages/python/src/truss/_psycopg_epoch_cut.py']}}
(OUT/'results.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'count':len(records),'passed':True}))
