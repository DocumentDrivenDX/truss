"""Bounded offline registered Subject composition controls; no native execution."""
from pathlib import Path
from dataclasses import replace
from hashlib import sha256
from contextlib import nullcontext
from unittest.mock import patch
from types import SimpleNamespace
import json
from truss._security_graph_source import PreparedGraphSecuritySource
from truss._security_graph_epoch_read import GraphEpochReadContext,PendingGraphEpochReadCut,_DIGEST
from truss._psycopg_epoch_cut import _EpochComparison
from truss.psycopg_host import PsycopgHost
import truss._security_graph_subject_installation as m
import security_ontology_native_subject_read as api
root=Path('/private/tmp/truss-security-main-integration');e=root/'docs/helix/04-build/evidence/security-graph-subject-registration-20261014';out=Path(__file__).resolve().parent
native=json.loads((e/'native-source-epoch.json').read_bytes());source=PreparedGraphSecuritySource(*((e/f).read_bytes() for f in ('physical-request.json','compiler-output.json','accepted-catalog.json','compiler-request.json')),native_guard=(native['installation'].encode(),b'original authored profile',1))
script=root/'scripts/security_ontology_native_subject_read.py';current_script=script.read_bytes();profile=json.loads((e/'issued-profile.json').read_bytes());profile['subjectHelperSha256']=sha256(current_script).hexdigest()
context=GraphEpochReadContext(source,_EpochComparison(native['installation'],native['epoch'],native['incarnation'],json.dumps(profile).encode(),source.accepted_catalog_assessment),PendingGraphEpochReadCut(native['installation'],10,12345,_DIGEST),current_script)
subjects=m.PendingGraphSubjects(native['installation'],100,m.derive_graph_subject_profile(source),((123,'Alice'),));results=[]
def require(v):assert v
def check(name,fn):fn();results.append({'name':name,'passed':True})
def refuse(fn,msg=None):
 try:fn()
 except ValueError as ex:
  if msg is not None:assert str(ex)==msg,(str(ex),msg)
  return
 raise AssertionError('Required refusal missing')
check('derived profile equals exact retained registration bytes',lambda:require(subjects.profile_bytes==(e/'subject-profile.json').read_bytes()))
class EnteredHost(Exception):pass
caller=object.__new__(PsycopgHost);executor=object.__new__(PsycopgHost)
def preflight(reg=subjects,ctx=context,binds=subjects.bindings,expected=ValueError):
 with patch.object(api,'_HostPairReservation',return_value=nullcontext()),patch.object(PsycopgHost,'_run_published_operation',side_effect=EnteredHost) as host:
  try:api.publish_native_ontology_resource_read(caller,None,executor,None,source.original_request,binds,lambda b:None,compiler=lambda *a:{},cut_issuer=(10,12345),source_epoch=ctx,subject_registration=reg)
  except expected:
   if expected is ValueError:host.assert_not_called()
   return
  raise AssertionError('Unexpected preflight result')
check('matching source profile reaches host boundary',lambda:preflight(expected=EnteredHost))
check('registered composition without source epoch refuses before host',lambda:preflight(ctx=None))
check('different registered binding refuses before host',lambda:preflight(binds=((123,'Bob'),)))
for field in ('physicalRequestSha256','acceptedCatalogSha256','graphBindingSha256','ontologySha256','policySha256','nativeTypeId','nativePropertyId','version','physicalPin'):
 data=json.loads(subjects.profile_bytes);data[field]='changed';bad=replace(subjects,profile_bytes=json.dumps(data,sort_keys=True,separators=(',',':')).encode())
 check('different registration '+field+' refuses before host',lambda bad=bad:preflight(reg=bad))
check('legacy unregistered diagnostic path preserved',lambda:preflight(reg=None,ctx=None,expected=EnteredHost))
home=[('100','r','p','false','false','false','true')];row=[(subjects.installation_id,subjects.profile_bytes.hex())];installation=[(subjects.installation_id,'100')]
def verify(h=home,r=row,i=installation,pid=42):
 with patch.object(m,'verify_graph_subject_issuer_with_cursor',return_value=4242),patch.object(m,'_text_rows',side_effect=[h,r,i]) as query:
  result=m.verify_registered_graph_subjects_with_cursor(None,subjects,caller_pid=pid)
  sql=query.call_args_list[0].args[1];assert all(s in sql for s in ('l.pid','l.database','l.relation','l.granted',"'relation'","'ShareLock'"));assert query.call_args_list[0].args[2]==(42,)
  return result
check('exact reserved caller profile cut and installation accepts',lambda:require(verify()==4242))
for label,index,value in [('wrong owner',0,'999'),('view home',1,'v'),('temporary home',2,'t'),('RLS home',3,'true'),('FORCE RLS home',4,'true'),('inheritance',5,'true'),('missing caller ShareLock',6,'false')]:
 bad=list(home[0]);bad[index]=value;check(label+' refuses',lambda bad=bad:refuse(lambda:verify(h=[tuple(bad)])))
check('different stored profile refuses',lambda:refuse(lambda:verify(r=[(subjects.installation_id,'00')])));
check('different native installation refuses',lambda:refuse(lambda:verify(i=[('other','100')])));
for label,pid in [('bool',True),('text','42'),('zero',0),('overflow',2147483648)]:check(label+' verifier PID refuses before query',lambda pid=pid:refuse(lambda:m.verify_registered_graph_subjects_with_cursor(None,subjects,caller_pid=pid)))
identity=('5','123','Alice');observed=[('Alice',subjects.installation_id,'5','123',sha256(subjects.profile_bytes).hexdigest())]
def own(rows):
 with patch.object(m,'verify_graph_subject_issuer_with_cursor',return_value=4242),patch.object(m,'_text_rows',return_value=rows):return m.read_own_graph_subject_with_cursor(None,subjects,identity)
check('own-session exact native tuple accepts',lambda:require(own(observed)=='Alice'))
for label,index in [('key',0),('installation',1),('database',2),('role',3),('profile',4)]:
 bad=list(observed[0]);bad[index]='other';check('different own-session '+label+' refuses',lambda bad=bad:refuse(lambda:own([tuple(bad)])))
check('duplicate own-session tuple refuses',lambda:refuse(lambda:own(observed*2)))
check('missing own-session tuple refuses',lambda:refuse(lambda:own([])))
class Foreign:
 description=[SimpleNamespace(type_code=19)]
 fetched=0
 def execute(self,*a,**kw):pass
 def fetchmany(self,n):self.fetched+=1;raise AssertionError('Foreign row decoded')
f=Foreign()
with patch.object(m,'verify_graph_subject_issuer_with_cursor',return_value=4242):check('foreign own-session descriptor refuses before fetch',lambda:refuse(lambda:m.read_own_graph_subject_with_cursor(f,subjects,identity)))
assert f.fetched==0
# Actual route query receives only the verified function OID, with legacy zero.
def route(oid,unsafe=False):
 rows=[[('100','5')],[('100','r','p','false','false','false','true')],[('123','Alice')],[('123','true','false','false','false','false','false','false')],[('123','false','false','false')],[('123','true' if unsafe else 'false','false')]]
 with patch.object(api,'_text_rows',side_effect=rows) as query:
  value=api._registered_subject(None,identity,subjects.bindings,12345,oid)
  assert query.call_args_list[-1].args[2]==(oid or 0,[123]);assert 'p.oid OPERATOR(pg_catalog.<>) %s::pg_catalog.oid' in query.call_args_list[-1].args[1]
  return value
check('sole verified issuer OID exclusion selected',lambda:require(route(4242)=='Alice'))
check('legacy route scanner has no native OID exclusion',lambda:require(route(None)=='Alice'))
check('other reachable export route refuses',lambda:refuse(lambda:route(4242,unsafe=True)))
result={'scope':'Offline actual preflight/native-row comparisons with trusted comparison context and host sentinel. Retained original inputs plus reauthored current-script hash are comparison fixtures, not native issued authority. No new native execution.','passed':len(results),'failed':0,'sourceSha256':{p:sha256((root/p).read_bytes()).hexdigest() for p in ('packages/python/src/truss/_security_graph_subject_installation.py','scripts/security_ontology_native_subject_read.py')},'controls':results}
(out/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(str(len(results))+' bounded controls passed')
