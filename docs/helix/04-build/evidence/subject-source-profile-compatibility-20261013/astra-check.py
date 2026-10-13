from pathlib import Path
from types import SimpleNamespace
from hashlib import sha256
import sys,json
root=Path('/private/tmp/truss-security-main-integration');out=Path('/private/tmp/subject-source-profile-review-20261013')
sys.path[:0]=[str(root/'packages/python/src'),'/private/tmp/truss-psycopg-baseline-env/lib/python3.11/site-packages']
from truss.psycopg_host import PsycopgHost,PsycopgProfile
from truss._psycopg_epoch_cut import _run_fenced_epoch_operation,_EpochComparison
names=('installation_id','source_epoch','target_incarnation','profile_hex','evidence_hex','evidence_sha256','actual_writer_xid','actual_database_oid','actual_backend_pid','original_actor','effective_actor','cut_scope')
expected=('fixture','1','target','01','02',sha256(b'\x02').hexdigest(),'77','88','55','alice','alice','transaction_epoch_state_fence_only')
class Cursor:
 def __init__(self,kind):self.kind=kind;self.stage=0;self.fetches=0;self.adapters=SimpleNamespace(register_dumper=lambda *_:None)
 def execute(self,*a,**kw):
  self.stage+=1;ns=names if self.stage==2 else ('xid','db','pid','actor','effective');self.description=[SimpleNamespace(name=n,type_code=25)for n in ns]
  if self.stage==2:
   if self.kind=='wrong-oid':self.description[0].type_code=19
   if self.kind=='wrong-name':self.description[0].name='foreign'
   if self.kind=='extra-descriptor':self.description.append(SimpleNamespace(name='foreign',type_code=25))
   if self.kind=='missing-descriptors':self.description=None
 def fetchmany(self,n):
  if self.stage==1:return [('77','88','55','alice','alice')]
  self.fetches+=1
  if self.kind=='wrong-value':return [('foreign',*expected[1:])]
  if self.kind=='no-rows':return []
  if self.kind=='two-rows':return [expected,expected]
  return [expected]
results=[]
for kind in ['match','wrong-oid','wrong-name','extra-descriptor','missing-descriptors','wrong-value','no-rows','two-rows']:
 cursor=Cursor(kind);called=[];host=object.__new__(PsycopgHost);host._profile=PsycopgProfile(server=180006)
 host._run_operation=lambda tx,cb:cb(cursor,(('55','vxid','read_committed','read_write'),'77','2000'))
 try:
  result=_run_fenced_epoch_operation(host,object(),_EpochComparison('fixture','1','target',b'\x01',b'\x02'),lambda *_:called.append(True));refused=False
 except ValueError:refused=True
 assert refused==(kind!='match') and called==([True]if kind=='match'else[])
 if kind in ['wrong-oid','wrong-name','extra-descriptor','missing-descriptors']:assert cursor.fetches==0
 results.append({'case':kind,'passed':True,'helperRowFetches':cursor.fetches,'callbackInvocations':len(called)})
(out/'decoder-results.json').write_text(json.dumps({'scope':'Actual epoch helper callback decoder with synthetic cursor/host operation; not native SQL or custody qualification.','count':len(results),'results':results,'sourceSha256':sha256(root.joinpath('packages/python/src/truss/_psycopg_epoch_cut.py').read_bytes()).hexdigest()},indent=2)+'\n');print('Passed',len(results),'bounded descriptor/row controls')
