"""Offline current graph epoch read review; no native calls or compiler execution."""
from pathlib import Path
from dataclasses import replace
from hashlib import sha256
from contextlib import nullcontext
from unittest.mock import patch
from types import SimpleNamespace
import ast,json
from truss._security_graph_source import PreparedGraphSecuritySource
import truss._security_graph_epoch_read as m
from truss._psycopg_epoch_cut import _EpochComparison
from truss.psycopg_host import PsycopgHost
import security_ontology_native_subject_read as api
root=Path(__file__).resolve().parents[6];e=Path(__file__).resolve().parent.parent
native=json.loads((e/'native-source-epoch.json').read_bytes())
source=PreparedGraphSecuritySource(*((e/f).read_bytes() for f in ('physical-request.json','compiler-output.json','accepted-catalog.json','compiler-request.json')),native_guard=(native['installation'].encode(),b'original authored profile',1))
script=root/'scripts/security_ontology_native_subject_read.py';subject_source=script.read_bytes()
profile=json.loads((e/'issued-profile.json').read_bytes());assert profile['subjectHelperSha256']==sha256(subject_source).hexdigest()
context=m.GraphEpochReadContext(source,_EpochComparison(native['installation'],native['epoch'],native['incarnation'],json.dumps(profile).encode(),source.accepted_catalog_assessment),m.PendingGraphEpochReadCut(native['installation'],10,12345,m._DIGEST),subject_source)
results=[]
def check(name,fn):fn();results.append({'name':name,'passed':True})
def require(v):assert v
def refusal(fn,message=None):
 try:fn()
 except ValueError as ex:
  if message is not None:assert str(ex)==message,(str(ex),message)
  return
 raise AssertionError('Refusal required')
check('original fixed SQL byte digest',lambda:require(sha256(m._source()).hexdigest()==m._DIGEST))
check('matching copied epoch context',lambda:require(m.snapshot_graph_epoch_read_context(context)==context))
for name,bad in [('Boolean guard generation',replace(context,source=replace(source,native_guard=(source.native_guard[0],source.native_guard[1],True)))),('mutable profile bytes',replace(context,comparison=replace(context.comparison,profile=bytearray(context.comparison.profile)))),('different issuer installation',replace(context,issuer=replace(context.issuer,installation_id='other'))),('different assessment bytes',replace(context,comparison=replace(context.comparison,evidence=b'{}'))),('different Subject source digest',replace(context,subject_source=b'other'))]:check(name,lambda bad=bad:refusal(lambda:m.snapshot_graph_epoch_read_context(bad)))
class EnteredHost(Exception):pass
caller=object.__new__(PsycopgHost);executor=object.__new__(PsycopgHost)
def preflight(selected=context,compiler=lambda *a:{},cut=(10,12345),expected=ValueError):
 try:
  with patch.object(api,'_HostPairReservation',return_value=nullcontext()),patch.object(PsycopgHost,'_run_published_operation',side_effect=EnteredHost):
   api.publish_native_ontology_resource_read(caller,None,executor,None,source.original_request,((123,'s1'),),lambda b:None,compiler=compiler,cut_issuer=cut,source_epoch=selected)
 except expected:return
 raise AssertionError('Unexpected host preflight completion')
check('valid epoch path reaches reserved host boundary',lambda:preflight(expected=EnteredHost))
check('legacy no-epoch diagnostic preflight retained',lambda:preflight(selected=None,compiler=None,cut=None,expected=EnteredHost))
check('epoch without compiler refuses before host',lambda:preflight(compiler=None))
for name,cut in [('empty issuer tuple',()),('short issuer tuple',(10,)),('list issuer',[10,12345]),('Boolean issuer OID',(True,12345)),('issuer same owner and caller',(10,10))]:check(name,lambda cut=cut:preflight(cut=cut))
other_profile=dict(profile,subjectHelperSha256=sha256(b'other Subject source').hexdigest());other=replace(context,subject_source=b'other Subject source',comparison=replace(context.comparison,profile=json.dumps(other_profile).encode()))
check('self-consistent prior Subject source refuses current file',lambda:preflight(selected=other))
# Invoke the actual nested compiler correspondence wrapper without running SQL.
tree=ast.parse(subject_source);function=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='epoch_compiler');code=compile(ast.fix_missing_locations(ast.Module(body=[function],type_ignores=[])),str(script),'exec')
def invoke(receipt):
 ns={'compiler':lambda *args:receipt,'source_epoch':context};exec(code,ns);return ns['epoch_compiler'](None,None,None,None,None)
valid={'request':source.native_dependencies.decode(),'output':source.original_response.decode()}
check('exact original compiler request and output accepts',lambda:require(invoke(valid) is valid))
for name,bad in [('different compiler request',dict(valid,request='{}')),('different compiler output',dict(valid,output='{}')),('nonstring request',dict(valid,request=1)),('nondict receipt',None)]:check(name,lambda bad=bad:refusal(lambda:invoke(bad)))
class Text(str):pass
check('compiler receipt string subclass refuses',lambda:refusal(lambda:invoke(dict(valid,request=Text(valid['request'])))))
def generator_closed():
 cleanup=[]
 def body():
  try:yield None
  finally:cleanup.append('closed')
 g=body();next(g);refusal(lambda:invoke(g));require(g.gi_frame is None and cleanup==['closed'])
check('started returned generator closes before refusal',generator_closed)
def coroutine_closed():
 async def body():raise AssertionError('Must stay cold')
 c=body();refusal(lambda:invoke(c));require(c.cr_frame is None)
check('cold returned coroutine closes before refusal',coroutine_closed)
rows=[(name,'r','p','false','false','false','true') for name in sorted(m._TABLES)]
with patch.object(m,'_text_rows',return_value=rows):check('four exact unfiltered held homes accepts',lambda:m._verify_homes(None,held=True))
for name,col,value in [('RLS enabled',3,'true'),('FORCE RLS enabled',4,'true'),('inheritance present',5,'true'),('missing held ShareLock',6,'false'),('temporary home',2,'t')]:
 bad=list(rows);row=list(bad[0]);row[col]=value;bad[0]=tuple(row)
 with patch.object(m,'_text_rows',return_value=bad):check(name,lambda:refusal(lambda:m._verify_homes(None,held=True)))
class Cursor:
 description=[SimpleNamespace(type_code=19)]
 fetched=0
 def execute(self,*a,**kw):pass
 def fetchmany(self,n):self.fetched+=1;raise AssertionError('Foreign descriptor decoded')
c=Cursor();check('foreign home descriptor refuses before fetch',lambda:refusal(lambda:m._verify_homes(c,held=True)));assert c.fetched==0
# Added read-only and issuer-owner reachability comparison controls.
class PermissionCursor:
 def __init__(self,rows,oid=25):self.rows=rows;self.description=[SimpleNamespace(type_code=oid)];self.fetched=0
 def execute(self,query,params=(),**kw):
  assert "pg_catalog.has_any_column_privilege" in query
  assert params[0]==list(m._TABLES) and params[1:]==(12345,)*6
 def fetchmany(self,n):self.fetched+=1;return self.rows
check('exact native readonly true text accepts',lambda:m._verify_private_permissions(PermissionCursor([('true',)]),12345))
for name,rows in [('native readonly false', [('false',)]),('native readonly NULL',[(None,)]),('native readonly Boolean loader value',[(True,)]),('native readonly no row',[]),('native readonly duplicate rows',[('true',),('true',)])]:
 check(name,lambda rows=rows:refusal(lambda:m._verify_private_permissions(PermissionCursor(rows),12345)))
p=PermissionCursor([('true',)],oid=19)
check('readonly foreign descriptor refuses before fetch',lambda:refusal(lambda:m._verify_private_permissions(p,12345)));assert p.fetched==0
body=m._source().decode().split('AS $$',1)[1].split('$$;',1)[0]
definition=[('10','plpgsql','f','0','','2278','false','false','true','v','u','false','0','["search_path=pg_catalog, pg_temp"]',body,'true')]
acl=[('10','10','EXECUTE','false'),('12345','10','EXECUTE','false')]
for name,role,accept in [('excluded privileged issuer owner',[('true','false')],True),('issuer owner membership refuses',[('true','true')],False),('unprivileged issuer owner refuses',[('false','false')],False)]:
 with patch.object(m,'_text_rows',side_effect=[definition,acl,role]):
  if accept:check(name,lambda:m._verify_issuer(None,context.issuer))
  else:check(name,lambda:refusal(lambda:m._verify_issuer(None,context.issuer),'Original excluded privileged graph epoch cut owner required'))

for file in ('packages/python/src/truss/_security_graph_epoch_read.py','scripts/security_ontology_native_subject_read.py'):
 ast.parse((root/file).read_bytes())
result={'scope':'Offline selected source, preflight, held-home descriptor and extracted exact wrapper controls. No native lifecycle or arbitrary configured-code containment claim.','passed':len(results),'failed':0,'sourceSha256':{f:sha256((root/f).read_bytes()).hexdigest() for f in ('packages/python/src/truss/_security_graph_epoch_read.py','packages/python/src/truss/_security_bootstrap/graph-epoch-read-cut.sql','scripts/security_ontology_native_subject_read.py')},'controls':results}
Path(__file__).with_name('r6-results.json').write_text(json.dumps(result,indent=2)+'\n');print(str(len(results))+' bounded controls passed')
