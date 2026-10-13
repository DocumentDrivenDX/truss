"""Synthetic cursor/host control of the real factory; no native atomicity claim."""
from pathlib import Path
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import patch
from contextlib import ExitStack
import hashlib,json
from truss import _security_catalog_source_epoch as m
from truss import _psycopg_fact_cut as fact
from truss._security_mapping import PreparedSecurityMapping
from truss.execution import Ok,Error,ExecutionFailure
ROOT=Path('/private/tmp/truss-security-main-integration');OUT=Path(__file__).parent
checks=[]
def check(n,fn):fn();checks.append({'name':n,'passed':True})
def eq(a,b):assert a==b,(a,b)
manifest={'releaseId':'review-release'};digest='a'*64;identity='review-installation'
request=b'original-request';response=b'original-response';assessment=b'original-assessment';deps=b'original-dependencies';guard=(identity.encode(),b'original-profile',1)
incarnation=json.dumps({'interfaceVersion':'truss-catalog-source-target/0.1.0','databaseOid':'1','schemaOid':'2'},sort_keys=True,separators=(',',':')).encode()
sources=m._sources();body=dict(sources)['routine-ddl-barrier.sql'].split('AS $$',1)[1].split('$$;',1)[0]
def inputs():
 mapping=PreparedSecurityMapping(request,response,accepted_catalog_assessment=assessment,native_dependencies=deps,native_guard=guard)
 marker=m.PendingCatalogSourceMarker(identity,digest,hashlib.sha256(assessment).hexdigest(),incarnation)
 barrier=m._DDLBarrierComparison(42,700,body,True,True,True)
 infra=m.PendingSourceEpochInfrastructure(identity,m._MANIFEST_SHA256,barrier)
 relation=fact._FactRelationComparison('truss','object',30,42,'original guard',(fact._FactColumnComparison('id',1,25,-1,True,0),))
 return dict(mapping=mapping,marker=marker,infrastructure=infra,fact_relations=(relation,),subject_source=b'original-helper')
class Cursor:
 def __init__(self,changes,events):self.changes=changes;self.events=events;self.counts={};self.fetches={};self.issued=None;self.description=None;self.rows=[]
 def execute(self,sql,params=(),**kw):
  q=str(sql)
  if "current_setting('search_path')" in q:key='path';rows=[('original, pg_catalog',)];names=['path'];codes=[25]
  elif "current_setting('server_version_num')" in q:key='settings';rows=[('180006','read committed','off','on')];names=['v','i','r','e'];codes=[25]*4
  elif 'FROM truss.catalog_runtime_installation' in q:key='installation';rows=[(identity,42)];names=['installation_id','owner_oid'];codes=[25,26]
  elif 'runtime_current_installation' in q:key='release';rows=[(manifest['releaseId'],digest)];names=['release_id','release_sha256'];codes=[25]*2
  elif 'policy_generation_guard' in q:key='guard';rows=[guard];names=['installation_identity_bytes','policy_profile_bytes','generation'];codes=[17,17,20]
  elif 'pg_catalog.pg_database' in q:key='target';rows=[('1','2','db')];names=['db','schema','name'];codes=[25]*3
  elif 'FROM truss.installation_marker' in q:key='marker';rows=[(identity,manifest['releaseId'],digest,'truss-accepted-catalog/0.1.0',hashlib.sha256(assessment).hexdigest(),'truss','{"databaseName":"db","databaseOid":"1"}')];names=list('abcdefg');codes=[25]*7
  elif 'count(*) FROM truss.source_epoch_current' in q:key='counts';rows=[('0','0')];names=['current','registry'];codes=[25]*2
  elif 'SELECT truss.runtime_issue_source_epoch' in q:
   key='issue';self.issued=params;rows=[('native-epoch',)];names=['runtime_issue_source_epoch'];codes=[25]
  elif 'FROM truss.source_epoch_current c JOIN' in q:
   key='readback';i,t,p,a=self.issued;rows=[(i,'native-epoch',t,p.hex(),a.hex(),None,'initial')];names=list('abcdefg');codes=[25]*7
  elif "set_config('search_path',%s" in q:key='restore';rows=[(params[0],)];names=['set_config'];codes=[25]
  elif 'set_config' in q:key='pin';rows=[('pg_catalog, pg_temp',)];names=['set_config'];codes=[25]
  elif 'LOCK TABLE' in q:key='write-lock';rows=[];names=[];codes=[]
  else:raise AssertionError(q)
  self.counts[key]=self.counts.get(key,0)+1;phase=f'{key}:{self.counts[key]}';self.phase=phase;self.events.append(phase)
  change=self.changes.get(phase,{})
  self.rows=change.get('rows',rows);codes=change.get('codes',codes);names=change.get('names',names)
  self.description=None if codes is None else [SimpleNamespace(name=n,type_code=c) for n,c in zip(names,codes)]
 def fetchmany(self,n):self.fetches[self.phase]=self.fetches.get(self.phase,0)+1;return self.rows

def run(changes=None,kw=None,mutate=None):
 kw=inputs() if kw is None else kw;events=[];cur=Cursor(changes or {},events);state={'hostCalls':0,'error':None,'archive':0,'catalog':0,'verify':0};host=object.__new__(m.PsycopgHost)
 def op(self,tx,callback):
  state['hostCalls']+=1
  if mutate:mutate(kw)
  try:return Ok(callback(cur,None))
  except Exception as e:state['error']=e;return Error(ExecutionFailure('execution_obligation',str(e)))
 def archive(c,captured,i):
  state['archive']+=1;events.append('archive:'+str(state['archive']));eq((captured.original_request,captured.original_response,captured.accepted_catalog_assessment,captured.native_dependencies),(request,response,assessment,deps));eq(i,identity)
  if (changes or {}).get('archive:'+str(state['archive'])):raise ValueError('archive drift')
 def capture(c,r):
  eq(r,request);state['catalog']+=1;events.append('catalog:'+str(state['catalog']));return b'changed-assessment' if (changes or {}).get('catalog:'+str(state['catalog'])) else assessment
 def verify(c,s,a):
  eq(s,sources);eq(a,42);state['verify']+=1;events.append('verify:'+str(state['verify']));b=inputs()['infrastructure'].barrier
  return replace(b,function_oid=701) if (changes or {}).get('verify:'+str(state['verify'])) else b
 def prepare(relations,callback,**opts):
  # Run real structural validation only. The native fact qualifiers are independently tested elsewhere.
  fact._prepare_fenced_fact_cut(relations,callback,**opts)
  eq(relations,inputs()['fact_relations'])
  def invoke(c):events.append('fact-qualified-seam');return callback(c)
  return invoke
 with ExitStack() as p:
  for name,new in [('_pin_cursor',lambda c:None),('_release',lambda:(manifest,digest,None)),('installation_administrator_with_cursor',lambda c,o:(42,'admin',True,True)),('verify_catalog_source_archive_with_cursor',archive),('capture_accepted_catalog',capture),('_verify',verify),('_prepare_fenced_fact_cut',prepare)]:p.enter_context(patch.object(m,name,new))
  p.enter_context(patch.object(m.PsycopgHost,'_run_operation',op))
  result=m.issue_initial_catalog_source_epoch_in_transaction(host,object(),**kw)
 return result,state,cur,events

def positive():
 result,state,cur,events=run();assert isinstance(result,Ok),state['error']
 eq((result.value.status,result.value.security_ready),('pending_commit',False));eq(result.value.comparison.epoch,'native-epoch')
 eq(result.value.comparison.evidence,assessment)
 eq(json.loads(result.value.comparison.profile)['sourceEpochManifestSha256'],m._MANIFEST_SHA256)
 assert events.index('catalog:1')<events.index('guard:1')<events.index('verify:1')<events.index('fact-qualified-seam')<events.index('issue:1')<events.index('readback:1')<events.index('guard:2')<events.index('verify:2')<events.index('archive:2')<events.index('catalog:2')<events.index('restore:1'),events
check('positive pending; captured manifest and exact ordering',positive)
for phase,change in [
 ('settings:1',{'rows':[('180006','repeatable read','off','on')]}),('settings:1',{'rows':[('180006','read committed','on','on')]}),('settings:1',{'rows':[('180006','read committed','off','off')]}),
 ('installation:1',{'rows':[('foreign',42)]}),('release:1',{'rows':[('other',digest)]}),('target:1',{'rows':[('3','2','db')]}),('marker:1',{'rows':[]}),('counts:1',{'rows':[('0','1')]}),
 ('guard:1',{'rows':[(guard[0],guard[1],2)]}),('guard:2',{'rows':[(guard[0],guard[1],2)]}),('guard:1',{'codes':[17,17,1700]}),('guard:2',{'codes':[17,17,1700]}),('guard:1',{'rows':[(guard[0],guard[1],True)]}),
 ('issue:1',{'codes':[19]}),('issue:1',{'rows':[]}),('issue:1',{'rows':[('x'*257,)]}),('readback:1',{'rows':[]}),('restore:1',{'rows':[('wrong',)]}),
 ('archive:1',True),('archive:2',True),('catalog:1',True),('catalog:2',True),('verify:1',True),('verify:2',True)]:
 def probe(p=phase,ch=change):
  result,state,cur,events=run({p:ch});assert isinstance(result,Error),(p,result);assert state['error'] is not None
  if isinstance(ch,dict) and 'codes' in ch:eq(cur.fetches.get(p,0),0)
  if p in ('guard:1','archive:1','catalog:1','verify:1','settings:1','installation:1','release:1','target:1','marker:1','counts:1'):eq(cur.issued,None)
 check('refuse '+phase+' '+str(change),probe)
for attr,value in [('original_request',bytearray(b'x')),('original_request',b''),('original_response',b''),('accepted_catalog_assessment',memoryview(b'x')),('native_dependencies',b''),('native_guard',(guard[0],guard[1],True)),('native_guard',(guard[0],guard[1],0)),('native_guard',(bytearray(b'x'),guard[1],1))]:
 def probe(a=attr,v=value):
  kw=inputs();kw['mapping']=replace(kw['mapping'],**{a:v});result,state,cur,events=run(kw=kw);assert isinstance(result,Error);eq(state['hostCalls'],0)
 check('preflight mapping '+attr+' '+type(value).__name__,probe)
for field,value in [('status','committed'),('security_ready',True),('target_incarnation',bytearray(b'x'))]:
 def probe(f=field,v=value):
  kw=inputs();kw['marker']=replace(kw['marker'],**{f:v});result,state,cur,events=run(kw=kw);assert isinstance(result,Error);eq(state['hostCalls'],0)
 check('preflight marker '+field,probe)
for key,value in [('fact_relations',[]),('fact_relations',()),('subject_source',bytearray(b'x')),('subject_source',b'x'*65537)]:
 def probe(k=key,v=value):
  kw=inputs();kw[k]=v;result,state,cur,events=run(kw=kw);assert isinstance(result,Error);eq(state['hostCalls'],0)
 check('preflight '+key+' '+str(type(value)),probe)
def mutation(kw):
 object.__setattr__(kw['mapping'],'original_request',b'changed');object.__setattr__(kw['mapping'],'native_guard',(b'other',b'other',2))
 object.__setattr__(kw['marker'],'installation_id','other');object.__setattr__(kw['infrastructure'].barrier,'function_oid',999)
 object.__setattr__(kw['fact_relations'][0],'oid',999);object.__setattr__(kw['fact_relations'][0].columns[0],'name','changed')
def custody():
 result,state,cur,events=run(mutate=mutation);assert isinstance(result,Ok),state['error'];eq(result.value.comparison.installation,identity)
check('host-entry replacement cannot rebind captured original inputs',custody)
output={'count':len(checks),'passed':True,'scope':'Actual factory with synthetic supported-host callback and native rows; structural recipe validation actual, native fact acquisition/archive/catalog verifier dependencies replaced by explicit seams. No native failure atomicity or issuer authentication claim.','controls':checks,'sourceSha256':hashlib.sha256((ROOT/'packages/python/src/truss/_security_catalog_source_epoch.py').read_bytes()).hexdigest()}
(OUT/'factory-results.json').write_text(json.dumps(output,indent=2)+'\n');print(json.dumps({'count':len(checks),'passed':True}))
