"""Actual registered read orchestration with explicit synthetic native seams."""
from pathlib import Path
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import patch
from contextlib import ExitStack
import hashlib,json
import security_catalog_subject_read as read
import truss._psycopg_epoch_cut as epoch
import truss._psycopg_fact_cut as fact
import truss._security_catalog_source_installation as archive
import truss._security_catalog_subject_installation as registered
from truss.execution import Ok,Error,ExecutionFailure
from truss.psycopg_host import PsycopgHost
ROOT=Path('/private/tmp/truss-security-main-integration');OUT=Path(__file__).parent;checks=[]
request=b'original request';mapping=read.PreparedSecurityMapping(request,b'{}',accepted_catalog_assessment=b'original assessment')
selection=read._SubjectSelection(request,(read.BASE/'document.json').read_bytes(),'m','Staff','pk','consumer','truss','catalog_subject_current',('staff_id',))
relations=(fact._FactRelationComparison('truss','object',10,12,'guard'),fact._FactRelationComparison('truss','catalog_subject_map',11,12,'guard'))
barrier=epoch._DDLBarrierComparison(12,13,'ddl source',True,True,True)
cut=(epoch._EpochComparison('installation','epoch','incarnation',read.derive_catalog_source_epoch_profile(mapping,relations,barrier),mapping.accepted_catalog_assessment),barrier)
subjects=registered.PendingCatalogSubjects('installation',registered._SOURCE_SHA256,((21,'s1'),(22,'s2'),(23,'s3')))
def invoke(*,registration='default',source_cut=cut,facts=relations,fail_registered=0,role='21',subject='s1',mutate_at=None,late_subject=None,legacy=False):
 original=replace(subjects) if registration=='default' else registration
 caller=object.__new__(PsycopgHost);executor=object.__new__(PsycopgHost);events=[];errors=[];delivered=[];seen=[];fences=[];counters={'source':0,'registered':0,'subject':0}
 class Cursor:
  def __init__(self,audience=False):self.audience=audience
  def execute(self,q,*a,**kw):
   self.context='catalog_subject_context' in q
   names=('installation_id',) if self.audience else (('installation_id','database_oid','role_oid') if self.context else ('installation_id','database_oid'))
   self.description=[SimpleNamespace(name=n,type_code=25) for n in names]
  def fetchmany(self,n):return [('installation',)] if self.audience else [('installation','db',role) if self.context else ('installation','db')]
 cursor=Cursor()
 def mutate():
  object.__setattr__(original,'installation_id','changed');object.__setattr__(original,'bindings',((99,'changed'),))
 original_read=Path.read_bytes
 def file_read(path):
  if mutate_at=='file' and path==read.BASE/'document.json':mutate()
  return original_read(path)
 def prepare(host,sel,inspector,produce,profiles):
  events.append('inspector')
  if mutate_at=='inspector':mutate()
  def observe(c,o):
   counters['subject']+=1;events.append('subject'+str(counters['subject']));value=late_subject if counters['subject']==2 and late_subject is not None else subject
   return produce(SimpleNamespace(identity=('m','Staff','pk'),values=(value,)))
  return observe
 def operation(host,tx,callback):
  events.append('caller' if host is caller else 'environment')
  try:return Ok(callback(cursor,None))
  except Exception as e:errors.append(str(e));return Error(ExecutionFailure('execution_obligation',str(e)))
 def published(host,tx,callback,publisher):
  result=operation(host,tx,callback)
  if isinstance(result,Ok):publisher(result.value)
  return result
 def epoch_run(host,tx,comp,b,callback):
  assert host is executor;counters['source']+=1;events.append('source'+str(counters['source']))
  try:return Ok(callback(Cursor(True)))
  except Exception as e:errors.append(str(e));return Error(ExecutionFailure('execution_obligation',str(e)))
 def fact_prepare(recipes,callback,*,existing_locks=False):
  def acquire(c):fences.append((existing_locks,tuple((r.schema,r.name) for r in recipes)));events.append('fact-held' if existing_locks else 'fact-acquire');return callback(c)
  return acquire
 def verify(c,r,src):
  counters['registered']+=1;events.append('registered'+str(counters['registered']));seen.append(r)
  assert src==original_read(ROOT/'scripts/security-catalog-subject.sql')
  if counters['registered']==fail_registered:raise ValueError('synthetic registered refusal')
 def helper(c,src,*,expected_callers):
  events.append('helper');assert expected_callers==(None if legacy else (21,22,23))
 def evaluate(*a,**kw):
  events.append('evaluate');assert tuple(r.name for r in kw['fact_relations'])==('object',);return Ok({'kind':'synthetic fixture','rows':[]})
 def encoder(*a,**kw):events.append('key');return SimpleNamespace(tuple_bytes=b'key')
 def sink(raw):events.append('publish');delivered.append(raw)
 patches=[(Path,'read_bytes',file_read),(read,'_prepare_subject_operation',prepare),(read,'_pin_cursor',lambda c:None),(read,'_verify_helpers',helper),(read,'encode_literal_key_tuple',encoder),(read,'run_owned_catalog_resource_read',evaluate),(epoch,'_run_ddl_fenced_epoch_operation',epoch_run),(fact,'_prepare_fenced_fact_cut',fact_prepare),(archive,'verify_catalog_source_archive_with_cursor',lambda *a:None),(registered,'verify_registered_catalog_subjects_with_cursor',verify),(PsycopgHost,'_run_operation',operation),(PsycopgHost,'_run_published_operation',published),(PsycopgHost,'_observe',lambda *a:None)]
 with ExitStack() as p:
  for obj,name,value in patches:p.enter_context(patch.object(obj,name,value))
  try:
   if legacy:result=read.publish_ddl_epoch_guarded_native_catalog_resource_read(caller,None,executor,None,mapping,selection,lambda *a:None,facts,source_cut,sink)
   else:result=read.publish_registered_ddl_epoch_guarded_native_catalog_resource_read(caller,None,executor,None,mapping,selection,lambda *a:None,facts,source_cut,original,sink)
  except Exception as e:errors.append(str(e));result=None
 return result,events,errors,delivered,seen,fences,original

def check(n,fn):fn();checks.append({'name':n,'passed':True})
def good():
 result,events,errors,out,seen,fences,original=invoke();assert isinstance(result,Ok),errors
 assert events.index('registered1')<events.index('subject1')<events.index('evaluate')<events.index('subject2')<events.index('registered2')<events.index('publish'),events
 assert len(out)==1 and type(out[0]) is bytes and json.loads(out[0])=={'kind':'synthetic fixture','rows':[]}
 assert len(seen)==2 and all(s==subjects and s is not original for s in seen)
 both=(('truss','object'),('truss','catalog_subject_map'));assert fences.count((False,both))==2 and fences.count((True,both))==2,fences
check('full registered qualification/order/captured set/both fact cuts/publication',good)
for where in ('file','inspector'):
 def probe(where=where):
  result,events,errors,out,seen,fences,original=invoke(mutate_at=where);assert isinstance(result,Ok),errors;assert original.installation_id=='changed';assert all(s==subjects for s in seen)
 check('original registration replacement at '+where+' cannot rebind',probe)
for stage in (1,2):
 def probe(stage=stage):
  result,events,errors,out,seen,fences,original=invoke(fail_registered=stage);assert isinstance(result,Error) and not out
  assert events.count('evaluate')==(0 if stage==1 else 1)
  assert events.count('key')==(0 if stage==1 else 2)
 check('registered refusal stage '+str(stage)+' prevents sink',probe)
for role,subject in [('21','s1'),('22','s2'),('23','s3')]:
 check('original role/key pair '+role+'/'+subject,lambda r=role,s=subject: isinstance(invoke(role=r,subject=s)[0],Ok) or (_ for _ in ()).throw(AssertionError('Expected Ok')))
for role,subject in [('21','s2'),('22','s1'),('99','s1')]:
 def probe(role=role,subject=subject):
  result,events,errors,out,*rest=invoke(role=role,subject=subject);assert isinstance(result,Error) and not out and 'evaluate' not in events;assert 'Original registered native caller Subject required' in errors
 check('mismatched role/key pair '+role+'/'+subject,probe)
for kwargs,label in [({'registration':None},'missing registration'),({'registration':object()},'foreign registration'),({'facts':None},'missing fact cuts'),({'source_cut':None},'missing source cut')]:
 def probe(kwargs=kwargs):
  result,events,errors,out,*rest=invoke(**kwargs);assert result is None and not events and not out
 check(label+' refuses before inspector/host',probe)
def late():
 result,events,errors,out,*rest=invoke(late_subject='s2');assert isinstance(result,Error) and not out and 'Original native Subject changed during delegated evaluation' in errors
check('late Subject change refuses before publication',late)
def legacy():
 result,events,errors,out,seen,fences,original=invoke(legacy=True);assert isinstance(result,Ok),errors;assert not seen and events.count('helper')==2 and len(out)==1
check('legacy wrapper preserves single-caller checker selection',legacy)
record={'scope':'Actual new orchestration with synthetic host, epoch/archives, fact lock/metadata, native context, helper, codec and evaluator seams. Verifies composition order and refusal/custody only; not native locking, semantics or source/issuer authentication.','count':len(checks),'passed':True,'controls':checks,'sourceSha256':hashlib.sha256((ROOT/'scripts/security_catalog_subject_read.py').read_bytes()).hexdigest()}
(OUT/'orchestration-results.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'count':len(checks),'passed':True}))
