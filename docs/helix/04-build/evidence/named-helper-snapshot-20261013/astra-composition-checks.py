from pathlib import Path
import sys,json,hashlib,subprocess,copy
from dataclasses import asdict,replace
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path('/private/tmp/truss-security-main-integration');OUT=Path(__file__).parent;BASE=ROOT/'docs/helix/04-build/evidence/security-named-source-profile'
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'packages/python/src'),'/private/tmp/subject-consumer-python']
import security_owned_read as owned
import weft
from truss.psycopg_host import PsycopgHost
from truss._psycopg_subject_observation import _SubjectSelection
from truss._psycopg_dependency_fact_cut import _OriginalFactSources,_DependencyRelationCells,_DependencyFactProvider
from truss._psycopg_fact_cut import _FactRelationComparison,_FactColumnComparison
from truss._psycopg_epoch_cut import _EpochComparison
import truss._umf_key_tuples as codec
assert Path(weft.__file__).resolve()==Path('/private/tmp/subject-consumer-python/weft.so')
checks=[]
def check(name,ok):assert ok,name;checks.append({'name':name,'passed':True})
# Original producer replay with output destination relocated; imports unchanged.
producer=(ROOT/'scripts/produce-security-named-source.ts').read_text();old="const base='docs/helix/04-build/evidence/security-named-source-profile';";assert producer.count(old)==1
(OUT/'produce-relocated.ts').write_text(producer.replace(old,"const base='/private/tmp/named-helper-review-20261013/generated';"))
(OUT/'security-named-source-fixture.ts').write_bytes((ROOT/'scripts/security-named-source-fixture.ts').read_bytes())
r=subprocess.run(['/opt/homebrew/bin/bun',str(OUT/'produce-relocated.ts')],cwd=ROOT,capture_output=True,text=True,timeout=10);assert r.returncode==0,r.stderr
for n in ('document','policy','resolution','transport','requirements','mapping-request'):check('exact original producer packet '+n,(OUT/'generated'/(n+'.json')).read_bytes()==(BASE/(n+'.json')).read_bytes())
request=(BASE/'mapping-request.json').read_bytes();document=(BASE/'document.json').read_bytes();raw=(BASE/'requirements.json').read_bytes();sources=_OriginalFactSources((BASE/'policy.json').read_bytes(),(BASE/'resolution.json').read_bytes())
p=json.loads(request);resolution=json.loads(sources.resolution);profile=json.loads(p['queryProfileJson'])
check('selected source bytes exactly document packet',p['modules'][0]['documentJson'].encode()==document)
check('original resolution contains same whole document object',resolution['documents'][0]['document']==json.loads(document))
check('minimal Resource identity query has no broader bindings',p['sql']=='SELECT r.resourceId FROM Resource r' and profile['bindings']==[])
probe=json.dumps({'sourceSha256':hashlib.sha256(document).hexdigest(),'identity':{'module':'m','element':'Staff','key':'pk'}})
check('genuine Weft shared named subject inspected',json.loads(weft.inspect_security_mapping_subject_key_json(request.decode(),probe))=={'interfaceVersion':'weft-security-subject-selection/0.1.0','status':'inspected','securityReady':False})
# Actual source recipe, subject observer, original codecs and evaluator; native cut/row shell is synthetic.
cells_json=json.loads(Path('/private/tmp/resource-list-review-20261013/baseline.json').read_bytes())['cells'];cells=[];providers=[]
for i,g in enumerate(cells_json,10):
 rel=_FactRelationComparison('truss','sec_staff' if g['relation'][1]=='Staff' else g['relation'][1],i,20,'trusted fixture guard')
 fields=[]
 for ref,num,oid in g['fields']:
  c=_FactColumnComparison('staff_id' if ref[2]=='staffId' else ref[2],num,oid,-1,True,0);providers.append(_DependencyFactProvider('field',tuple(ref),rel,c));fields.append((tuple(ref),num,oid))
 for ref in g['associations']:providers.append(_DependencyFactProvider('association',tuple(ref),rel))
 cells.append(_DependencyRelationCells(('truss',g['relation'][1],i),tuple(fields),tuple(tuple(r) for r in g['associations']),tuple(tuple(r) for r in g['rows'])))
base_profile={'kind':'truss-flat-fact-provider-fixture/0.3','requirementsSha256':hashlib.sha256(raw).hexdigest(),'policyUtf8':sources.policy.decode(),'resolutionUtf8':sources.resolution.decode(),'providers':[asdict(x) for x in providers],'caller':{'sessionRoleOid':'20','effectiveRoleOid':'20','subjectKey':[{'string':'s1'}]}}
sel=_SubjectSelection(request,document,'m','Staff','pk','fact_cut_actor','truss','named_subject_current',('staff_id',))
original_encoder=codec.encode_literal_key_tuple
class Cursor:
 def __init__(self,events,principal='fact_cut_actor',value='s1',oid=25):self.events=events;self.principal=principal;self.value=value;self.oid=oid;self.description=None;self.rows=None
 def execute(self,statement,*a,**kw):
  sql=statement.as_string() if hasattr(statement,'as_string') else str(statement)
  if 'p.proowner::pg_catalog.text' in sql:
   body=(ROOT/'scripts/security-named-subject.sql').read_text().split('AS $$',1)[1].split('$$;',1)[0]
   names=['c'+str(i) for i in range(19)];self.rows=[('20','sql','f','1','25','25','true','false','false','v','u','false','0','["search_path=pg_catalog"]',body,'["actor", "staff_id"]','["i", "t"]','["25", "25"]','true')];self.events.append('helper-snapshot')
  elif 'session_role_oid' in sql:names=['session_role_oid','effective_role_oid'];self.rows=[('20','20')];self.events.append('caller')
  elif 'rolbypassrls' in sql:names=['s','c','super','bypass','enc'];self.rows=[(self.principal,self.principal,'false','false','UTF8')];self.events.append('principal')
  elif 'named_subject_current' in sql:names=['staff_id'];self.rows=[(self.value,)];self.events.append('helper')
  else:raise AssertionError(sql)
  self.description=[SimpleNamespace(name=n,type_code=self.oid if names==['staff_id'] else 25) for n in names]
 def fetchmany(self,n):self.events.append('fetch');return self.rows

def invoke(selection=sel,claimed='s1',inspector=None,principal='fact_cut_actor',value='s1',oid=25,source=sources,old_wrapper=False,kind='truss-flat-fact-provider-fixture/0.3'):
 events=[];host=object.__new__(PsycopgHost);cursor=Cursor(events,principal,value,oid)
 value_profile=copy.deepcopy(base_profile);value_profile['caller']['subjectKey']=[{'string':claimed}];value_profile['kind']=kind
 epoch=_EpochComparison('fixture','epoch','target',json.dumps(value_profile).encode(),b'evidence')
 def inspect(a,b):events.append('inspector');return (inspector or weft.inspect_security_mapping_subject_key_json)(a,b)
 def cut(h,t,e,r,d,p,callback):events.append('held-cuts');return callback(cursor)
 def capture(c,g):events.append('capture');return tuple(cells)
 def encode(*a,**kw):events.append('encode');return original_encoder(*a,**kw)
 try:
  with patch.object(owned,'_run_dependency_fact_operation',cut),patch.object(owned,'_capture_dependency_relation_cells',capture),patch.object(PsycopgHost,'_observe',lambda h,c:(('123','1/2','read_committed','read_write'),'5','2000')),patch.object(codec,'encode_literal_key_tuple',encode):
   if old_wrapper:result=owned._run_owned_identity_read(host,None,epoch,raw,source,resource_list=True,source_profile='named',native_subject=selection,original_inspector=inspect)
   else:result=owned.run_named_subject_resource_read(host,None,epoch,raw,source,selection,inspect)
  return result,events,None
 except ValueError as e:return None,events,str(e)
result,events,error=invoke();check('actual composition positive',error is None and result['rows'][0]['key']==[{'string':'r1'}] and len(result['rows'])==1)
check('synthetic guards precede helper; both original encodings precede capture',events.index('held-cuts')<events.index('helper')<events.index('encode')<events.index('capture') and events.count('encode')==2)
r,e,error=invoke(claimed='s2');check('live/profile key mismatch refuses before capture',error=='Original native subject/profile key correspondence required' and 'capture' not in e)
r,e,error=invoke(selection=None);check('None selection refuses before inspector or cut',error=='Required exact native subject selection' and not e)
r,e,error=invoke(selection=None,old_wrapper=True);check('reconstructed prior wrapper demonstrates missing-live-subject downgrade',error is None and r['rows'][0]['key']==[{'string':'r1'}] and 'inspector' not in e and 'helper' not in e and 'encode' not in e)
for name,selection in [('wrong record',replace(sel,record='Project')),('legacy document',replace(sel,original_document=json.loads((ROOT/'packages/python/tests/fixtures/security-mapping-request.json').read_bytes())['modules'][0]['documentJson'].encode())),('legacy request',replace(sel,original_request=(ROOT/'packages/python/tests/fixtures/security-mapping-request.json').read_bytes())),('wrong columns',replace(sel,columns=('other',)))]:
 r,e,error=invoke(selection=selection);check(name+' refuses before inspection/cut',error=='Exact shared named fixture subject source required' and not e)
oldbase=ROOT/'docs/helix/04-build/evidence/security-identity-requirements';oldsources=_OriginalFactSources((oldbase/'policy.json').read_bytes(),(oldbase/'resolution.json').read_bytes())
r,e,error=invoke(source=oldsources);check('legacy policy/resolution refuses selected named mode',error=='Exact selected original fixture source bytes required' and not e)
r,e,error=invoke(principal='bob');check('wrong native principal refuses before helper',error=='Pinned original ordinary caller required' and 'helper' not in e and 'capture' not in e)
r,e,error=invoke(oid=19);check('foreign subject OID refuses before helper fetch/codec',error=='Exact original native TEXT descriptors required' and e[-1]=='helper' and 'encode' not in e and 'capture' not in e)
r,e,error=invoke(value=None);check('null subject refuses before codec',error=='Exact original native TEXT subject tuple required' and 'encode' not in e and 'capture' not in e)
mutable=replace(sel)
def mutate_original(a,b):
 object.__setattr__(mutable,'original_document',b'{}');object.__setattr__(mutable,'routine','changed');return weft.inspect_security_mapping_subject_key_json(a,b)
r,e,error=invoke(selection=mutable,inspector=mutate_original);check('selection snapshot survives original carrier mutation during inspection',error is None and r==result)
r,e,error=invoke(inspector=lambda a,b:'{}');check('malformed inspector refuses before cut',error=='Original non-ready subject inspection required' and 'held-cuts' not in e)
# Named evaluator preserves legacy CLI and rejects unknown CLI modes.
payload=Path('/private/tmp/resource-list-review-20261013/baseline.json').read_text()
for args,name,success in [([], 'legacy mode',True),(['--named-source'],'named mode',True),(['--unknown'],'unknown mode',False),(['--named-source','extra'],'extra mode',False)]:
 proc=subprocess.run(['/opt/homebrew/bin/bun',str(ROOT/'scripts/evaluate-security-captured-identity-fixture.ts'),*args],cwd=ROOT,input=payload,capture_output=True,text=True,timeout=10)
 check(name+' CLI',proc.returncode==0 and json.loads(proc.stdout)==result if success else proc.returncode!=0 and proc.stdout=='')
original_execute=Cursor.execute
for late_check in (2,3):
 def changed_caller(self,statement,*a,**kw):
  original_execute(self,statement,*a,**kw)
  if self.events[-1]=='caller' and self.events.count('caller')==late_check:self.rows=[('20','21')]
 with patch.object(Cursor,'execute',changed_caller):r,e,error=invoke()
 check('late caller OID drift refuses at checkpoint '+str(late_check),error=='Original native caller/profile correspondence required' and (('capture' in e)==(late_check==3)))
r,e,error=invoke();check('snapshot occurs inside cut before subject helper',error is None and e.index('held-cuts')<e.index('helper-snapshot')<e.index('helper'))
for name,selection in [('schema',replace(sel,schema='other')),('routine',replace(sel,routine='other')),('actor carrier',replace(sel,actor_carrier='name'))]:
 r,e,error=invoke(selection=selection);check('fixed '+name+' selection refuses before inspector',error=='Exact shared named fixture subject source required' and not e)
def changed_helper(self,statement,*a,**kw):
 original_execute(self,statement,*a,**kw)
 if self.events[-1]=='helper-snapshot':self.rows=[self.rows[0][:8]+('true',)+self.rows[0][9:]]
with patch.object(Cursor,'execute',changed_helper):r,e,error=invoke()
check('drifted helper snapshot refuses before helper or encoders',error=='Exact installed named subject helper snapshot required' and 'helper' not in e and 'encode' not in e and 'capture' not in e)
def pin(p):b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
paths=[ROOT/'scripts/security_owned_read.py',ROOT/'scripts/security-named-source-fixture.ts',ROOT/'scripts/produce-security-named-source.ts',ROOT/'scripts/evaluate-security-captured-identity-fixture.ts',ROOT/'packages/python/src/truss/_psycopg_subject_observation.py',ROOT/'packages/python/src/truss/_umf_key_tuples.py',Path(weft.__file__),Path(__file__),ROOT/'scripts/security-named-subject.sql']+list(sorted(BASE.glob('*.json')))
(OUT/'results.json').write_text(json.dumps({'count':len(checks),'controls':checks,'sourcePins':[pin(p) for p in paths],'positiveEvents':events,'scope':'Actual original Weft/UMF source, codec and evaluator; actual composed Python preparation/observer/execute logic, with synthetic host observation, native cursor rows and enclosing native-cut shell. No native privilege/locking proof. Missing-selection predecessor is a faithful reconstruction via current unchanged internal helper, not a replay of an archived whole file.'},indent=2)+'\n')
print(json.dumps({'controls':len(checks),'pass':True}))
