from pathlib import Path
from types import SimpleNamespace
from dataclasses import replace
from unittest.mock import patch
import sys,json,hashlib
ROOT=Path('/private/tmp/truss-security-main-integration');OUT=Path(__file__).parent
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'packages/python/src'),'/private/tmp/subject-consumer-python']
import security_catalog_subject_read as read
from truss._psycopg_subject_observation import _SubjectSelection
from truss._security_mapping import PreparedSecurityMapping
from truss.psycopg_host import PsycopgHost
from truss.execution import Ok,Error,ExecutionFailure
import weft
SOURCE=(ROOT/'scripts/security-catalog-subject.sql').read_text()
BODIES=[part.split('$$;',1)[0] for part in SOURCE.split('AS $$')[1:]]
OWNER='16385';CONTEXT=('fixture-installation','16384','16390')
FUNCTIONS={
 'catalog_subject_current':(OWNER,'plpgsql','f','1','25','25','true','false','true','v','u','false','0','["search_path=pg_catalog, pg_temp"]',BODIES[0],'["actor", "staff_id"]','["i", "t"]','["25", "25"]','true'),
 'catalog_subject_context':(OWNER,'sql','f','1','25','2249','true','false','true','v','u','false','0','["search_path=pg_catalog, pg_temp"]',BODIES[1],'["actor", "installation_id", "database_oid", "role_oid"]','["i", "t", "t", "t"]','["25", "25", "25", "25"]','true')}
checks=[]
def check(n,p):
 assert p,n
 checks.append({'name':n,'passed':True})
class Cursor:
 def __init__(self,change=None):self.change=change;self.stage=None;self.fetches=[];self.after=False
 def execute(self,statement,args=(),**kw):
  text=statement if type(statement) is str else statement.as_string()
  if text.startswith('SELECT c.relowner'):stage='owner';rows=[(OWNER,'false','false','false')];names=['owner','login','super','bypass']
  elif 'FROM pg_catalog.pg_proc p' in text:stage=args[0];rows=[FUNCTIONS[stage]];names=['f'+str(i) for i in range(19)]
  elif text.startswith('SELECT SESSION_USER'):stage='principal';rows=[('consumer','consumer','false','false','UTF8')];names=['p'+str(i) for i in range(5)]
  elif 'catalog_subject_current' in text:stage='subject';rows=[('s1',)];names=['staff_id']
  elif 'catalog_subject_context' in text:stage='context';rows=[CONTEXT];names=['installation_id','database_oid','role_oid']
  elif text.startswith('SELECT i.installation_id'):stage='environment';rows=[CONTEXT[:2]];names=['installation_id','database_oid']
  else:raise AssertionError(text)
  self.stage=stage;self.rows=rows;self.description=[SimpleNamespace(name=n,type_code=25) for n in names]
  if self.change:self.change(self,stage)
 def fetchmany(self,n):self.fetches.append(self.stage);return self.rows[:n]
read._verify_helpers(Cursor(),SOURCE);check('exact selected helper metadata accepted',True)
for function in FUNCTIONS:
 for index in range(19):
  def mutation(c,s,function=function,index=index):
   if s==function:r=list(c.rows[0]);r[index]='changed';c.rows=[tuple(r)]
  c=Cursor(mutation)
  try:read._verify_helpers(c,SOURCE)
  except ValueError as e:check(function+' field '+str(index)+' drift refused',str(e)=='Exact installed catalog subject helper snapshot required')
  else:raise AssertionError((function,index))
for stage,width,message in [('owner',4,'Exact native helper owner descriptors required'),('catalog_subject_current',19,'Exact native helper TEXT descriptors required'),('catalog_subject_context',19,'Exact native helper TEXT descriptors required')]:
 for change in ('foreign','short'):
  def mutation(c,s,stage=stage,change=change):
   if s==stage:
    if change=='foreign':c.description[0].type_code=19
    else:c.description.pop()
  c=Cursor(mutation)
  try:read._verify_helpers(c,SOURCE)
  except ValueError as e:check(stage+' '+change+' descriptors refuse before fetch',str(e)==message and stage not in c.fetches)
  else:raise AssertionError((stage,change))
for index in range(1,4):
 def mutation(c,s,index=index):
  if s=='owner':r=list(c.rows[0]);r[index]='true';c.rows=[tuple(r)]
 try:read._verify_helpers(Cursor(mutation),SOURCE)
 except ValueError as e:check('owner role flag '+str(index)+' refuses',str(e)=='Original non-login ordinary helper owner required')
 else:raise AssertionError(index)
for stage in ('owner','catalog_subject_current','catalog_subject_context'):
 for delta in ('missing','duplicate'):
  def mutation(c,s,stage=stage,delta=delta):
   if s==stage:c.rows=[] if delta=='missing' else c.rows*2
  try:read._verify_helpers(Cursor(mutation),SOURCE)
  except ValueError:check(stage+' '+delta+' rows refuse',True)
  else:raise AssertionError((stage,delta))
# Genuine original source inspector and encoder; native/host shells are explicitly synthetic.
E=ROOT/'docs/helix/04-build/evidence/accepted-catalog-policy-read-20261013'
request=(E/'request.json').read_bytes();mapping=PreparedSecurityMapping(request,(E/'owner-response.json').read_bytes(),accepted_catalog_assessment=(E/'assessment.json').read_bytes())
selection=_SubjectSelection(request,(read.BASE/'document.json').read_bytes(),'m','Staff','pk','consumer','truss','catalog_subject_current',('staff_id',))
DECISION=json.loads((E/'decision.json').read_bytes())
OBSERVED=(('123','1/2','read_committed','read_write'),None,'2000')

def invoke(mutation=None,selected=selection,inspection=None,decline_evaluator=False):
 caller=object.__new__(PsycopgHost);executor=object.__new__(PsycopgHost);caller._review_cursor=Cursor(mutation);executor._review_cursor=Cursor(mutation)
 events=[];errors=[];inspections=[]
 def inspector(request,probe):
  inspections.append(True)
  return weft.inspect_security_mapping_subject_key_json(request,probe) if inspection is None else inspection
 def operation(host,tx,callback):
  events.append('caller-entry' if host is caller else 'executor-environment')
  try:return Ok(callback(host._review_cursor,OBSERVED))
  except Exception as e:errors.append(e);return Error(ExecutionFailure('execution_obligation','synthetic shell contains error'))
 def evaluator(host,tx,m,subject):
  assert host is executor and m.original_request==mapping.original_request
  events.append(('evaluate',subject));caller._review_cursor.after=True
  return Error(ExecutionFailure('execution_obligation','synthetic evaluator refusal')) if decline_evaluator else Ok(DECISION)
 with patch.object(PsycopgHost,'_run_operation',operation),patch.object(PsycopgHost,'_observe',lambda self,c:OBSERVED),patch.object(read,'_pin_cursor',lambda c:None),patch.object(read,'run_owned_catalog_resource_read',evaluator):
  try:r=read.run_owned_native_catalog_resource_read(caller,object(),executor,object(),mapping,selected,inspector)
  except Exception as e:errors.append(e);r=None
 return r,events,errors,caller._review_cursor,executor._review_cursor,inspections
r,e,errors,c,x,i=invoke();check('genuine inspector and original key encoder complete both subject observations',isinstance(r,Ok) and r.value==DECISION and e==['caller-entry','executor-environment',('evaluate','s1')] and c.fetches.count('subject')==2 and len(i)==1)
for which in (0,1):
 def mutation(c,s,which=which):
  if s=='environment':r=list(c.rows[0]);r[which]='other';c.rows=[tuple(r)]
 r,e,errors,c,x,i=invoke(mutation);check(('installation' if which==0 else 'database')+' mismatch refuses before evaluator',isinstance(r,Error) and not any(type(v) is tuple for v in e) and str(errors[-1])=='Original caller/executor installation correspondence required')
for stage in ('context','environment'):
 def mutation(c,s,stage=stage):
  if s==stage:c.description[0].type_code=19
 r,e,errors,c,x,i=invoke(mutation);check(stage+' foreign descriptor refuses before fetch and evaluator',isinstance(r,Error) and stage not in c.fetches+x.fetches and not any(type(v) is tuple for v in e))
for label,stage,alter,expected in [
 ('late helper body','catalog_subject_current',lambda c: setattr(c,'rows',[tuple('altered' if j==14 else v for j,v in enumerate(c.rows[0]))]),'Exact installed catalog subject helper snapshot required'),
 ('late subject key','subject',lambda c:setattr(c,'rows',[('s2',)]),'Original native Subject changed during delegated evaluation'),
 ('late principal','principal',lambda c:setattr(c,'rows',[('consumer','other','false','false','UTF8')]),'Pinned original ordinary caller required')]:
 def mutation(c,s,stage=stage,alter=alter):
  if c.after and s==stage:alter(c)
 r,e,errors,c,x,i=invoke(mutation);check(label+' refuses after delegated evaluation',isinstance(r,Error) and ('evaluate','s1') in e and str(errors[-1])==expected)
for label,rows in [('missing',[]),('duplicate',[('s1',),('s1',)])]:
 def mutation(c,s,rows=rows):
  if s=='subject':c.rows=rows
 r,e,errors,c,x,i=invoke(mutation);check(label+' native subject refuses before executor',isinstance(r,Error) and e==['caller-entry'] and str(errors[-1])=='Exact original native TEXT subject tuple required')
r,e,errors,c,x,i=invoke(decline_evaluator=True);check('delegated refusal emits no outer result',isinstance(r,Error) and str(errors[-1])=='Original native Subject catalog evaluation refused')
for label,selected in [('wrong routine',replace(selection,routine='other')),('wrong record',replace(selection,record='Resource')),('mutable source',replace(selection,original_request=bytearray(request)))]:
 r,e,errors,c,x,i=invoke(selected=selected);check(label+' refuses before host and inspection',r is None and not e and not i)
r,e,errors,c,x,i=invoke(inspection='{"interfaceVersion":"weft-security-subject-selection/0.1.0","status":"refused","securityReady":false}');check('owner inspector refusal occurs before host',r is None and not e and len(i)==1)
def pin(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
record={'count':len(checks),'controls':checks,'scope':'Current helper metadata and composite orchestration with synthetic native rows, exact-type host shells and a synthetic delegated evaluator; actual original Weft subject inspector and original UMF tuple encoder execute. Does not prove native privileges, locks, host containment or complete authority. Those remain separately scoped parent native evidence.','sourcePins':[pin(ROOT/n) for n in ['scripts/security_catalog_subject_read.py','scripts/security-catalog-subject.sql','packages/python/src/truss/_psycopg_subject_observation.py','packages/python/src/truss/_umf_key_tuples.py']]+[pin(Path(__file__)),pin(Path(weft.__file__))],'retainedInputPins':[pin(E/n) for n in ['request.json','assessment.json','owner-response.json','decision.json']]}
(OUT/'results.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'controls':len(checks),'passed':True}))
