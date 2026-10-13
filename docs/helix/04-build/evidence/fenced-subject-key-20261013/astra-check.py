from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from dataclasses import replace
import sys,json,hashlib
root=Path('/private/tmp/truss-security-main-integration');out=Path('/private/tmp/fenced-subject-review-20261013')
sys.path[:0]=[str(root/'packages/python/src'),'/private/tmp/truss-psycopg-baseline-env/lib/python3.11/site-packages','/private/tmp/subject-consumer-python']
import weft
from truss.psycopg_host import PsycopgHost,PsycopgProfile
from truss._psycopg_epoch_cut import _EpochComparison
from truss._psycopg_fact_cut import _FactRelationComparison,_FactColumnComparison
from truss._psycopg_subject_observation import _SubjectSelection,_observe_fenced_subject_key,_observe_ordinary_subject_key
from truss._umf_key_tuples import encode_literal_key_tuple
request=root.joinpath('packages/python/tests/fixtures/security-mapping-request.json').read_bytes();source=json.loads(request)['modules'][0]['documentJson'].encode();selection=_SubjectSelection(request,source,'m','Staff','pk','alice','truss','subject_current',('staff_id',))
epoch=_EpochComparison('fixture','1','target',b'\x01',b'\x02');relation=_FactRelationComparison('truss','subject_fact',123,456,'originalbody',(_FactColumnComparison('staff_id',1,25,-1,True,100),))
names=('installation_id','source_epoch','target_incarnation','profile_hex','evidence_hex','evidence_sha256','actual_writer_xid','actual_database_oid','actual_backend_pid','original_actor','effective_actor','cut_scope')
results=[]
class Cursor:
 def __init__(self,kind):self.kind=kind;self.stage=0;self.events=[];self.adapters=SimpleNamespace(register_dumper=lambda *_:None)
 def execute(self,*a,**k):
  self.stage+=1;self.events.append('execute'+str(self.stage));stage=self.stage
  counts={1:5,2:12,4:7,5:12,6:9,7:6,8:5,9:1,10:5,11:5}
  count=counts.get(stage,0);labels=names if stage==2 else ('staff_id',)if stage==9 else tuple('c'+str(i)for i in range(count))
  self.description=[SimpleNamespace(name=n,type_code=25)for n in labels]
  if stage==3 and self.kind=='lock-refusal':raise ValueError('synthetic lock refused')
  if stage==9 and self.kind=='wrong-subject-oid':self.description[0].type_code=19
 def fetchmany(self,n):
  self.events.append('fetch'+str(self.stage));stage=self.stage
  if stage==1:return [('77','88','55','alice','alice')]
  if stage==2:return [('fixture','1','target','01','02',hashlib.sha256(b'\x02').hexdigest(),'77','88','55','alice','alice','transaction_epoch_state_fence_only')]
  if stage==4:return [('999' if self.kind=='wrong-relation'else'123','456','r','p','false','false','false')]
  if stage==5:return [('D'if self.kind=='disabled-guard'else'A','62','0','','false','true','456','false','v','["search_path=pg_catalog, pg_temp"]','originalbody','false')]
  if stage==6:return [('staff_id','1','25','-1','false'if self.kind=='wrong-column'else'true','100','','','false')]
  if stage==7:return [('55','1/1','read committed','on'if self.kind=='read-only'else'off','77','2000')]
  if stage in (8,10,11):return [('alice','foreign'if stage==11 and self.kind=='late-principal'else'alice','false','false','UTF8')]
  if stage==9:return [('fresh',)]
  raise AssertionError(stage)
for kind in ['match','wrong-relation','disabled-guard','wrong-column','lock-refusal','read-only','wrong-subject-oid','late-principal']:
 c=Cursor(kind);host=object.__new__(PsycopgHost);host._profile=PsycopgProfile(server=180006);state={'operations':0,'active':False,'encoded':0}
 def op(tx,cb):
  state['operations']+=1;state['active']=True
  try:return cb(c,(('55','1/1','read_committed','read_write'),'77','2000'))
  finally:state['active']=False
 host._run_operation=op
 def encoder(*args,**kwargs):
  assert state['active'] and c.stage==10
  assert all('execute'+str(i) in c.events for i in range(1,11));state['encoded']+=1;c.events.append('encode')
  return encode_literal_key_tuple(*args,**kwargs)
 try:
  with patch('truss._umf_key_tuples.encode_literal_key_tuple',side_effect=encoder):r=_observe_fenced_subject_key(host,object(),selection,weft.inspect_security_mapping_subject_key_json,('string',),epoch,(relation,),bun_executable='/opt/homebrew/bin/bun')
  refused=False
 except ValueError:refused=True
 assert refused==(kind!='match') and state['operations']==1 and not state['active']
 assert state['encoded']==(1 if kind in ('match','late-principal') else 0)
 if kind=='match':assert json.loads(r.original_receipt_bytes)['values']==[{'string':'fresh'}] and r.observation.values==('fresh',)
 if kind=='wrong-subject-oid':assert 'fetch9'not in c.events
 results.append({'name':kind,'passed':True,'hostOperations':state['operations'],'encoded':state['encoded'],'events':c.events})
(out/'results.json').write_text(json.dumps({'status':'passed','count':len(results),'results':results,'sourceSha256':hashlib.sha256(root.joinpath('packages/python/src/truss/_psycopg_subject_observation.py').read_bytes()).hexdigest(),'scope':'Actual subject, fact and epoch composition plus genuine Weft/UMF; synthetic cursor and host-operation shell. Establishes code ordering/one-cursor delegation only; not native locking or guard/source authentication.'},indent=2)+'\n');print('Passed',len(results),'composed ordering controls')
