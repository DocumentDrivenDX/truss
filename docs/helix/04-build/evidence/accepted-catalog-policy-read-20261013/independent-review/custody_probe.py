from pathlib import Path
from types import ModuleType
from unittest.mock import patch
import sys,json,hashlib
ROOT=Path('/private/tmp/truss-security-main-integration');OUT=Path(__file__).parent;E=ROOT/'docs/helix/04-build/evidence/accepted-catalog-policy-read-20261013'
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'packages/python/src')]
import security_catalog_read as current
from truss._security_mapping import PreparedSecurityMapping
old=ModuleType('review_catalog_at_dispatch');old.__file__=str(ROOT/'scripts/security_catalog_read.py')
exec(compile((OUT/'source-at-dispatch.py').read_bytes(),str(OUT/'source-at-dispatch.py'),'exec'),old.__dict__)
request=(E/'request.json').read_bytes();response=(E/'owner-response.json').read_bytes();original=(E/'assessment.json').read_bytes();rows=json.loads((E/'capture.json').read_bytes())[0]['rows']
changed=json.loads(original);changed['revision']=str(int(changed['revision'])+1);changed=json.dumps(changed,sort_keys=True,separators=(',',':')).encode()
class Cursor:
 def execute(self,*a,**k):pass
class Host:
 def __init__(self):self.entered=0
 def _run_operation(self,t,fn):self.entered+=1;return fn(Cursor(),None)
real_run=current.subprocess.run
outputs=[]
def invoke(mod,mutable,drift):
 carrier=bytearray(original) if mutable else original;host=Host();calls=[]
 mapping=PreparedSecurityMapping(request,response,accepted_catalog_assessment=carrier)
 def capture(c,r):calls.append(True);return changed if drift and len(calls)==2 else original
 def evaluate(*a,**kw):
  out=real_run(*a,**kw)
  if drift and mutable:carrier[:]=changed
  return out
 try:
  with patch.object(mod,'_pin_cursor',lambda c:None),patch.object(mod,'capture_accepted_catalog',capture),patch.object(mod,'_text_rows',lambda *a:rows),patch.object(mod.subprocess,'run',evaluate):
   result=mod.run_owned_catalog_resource_read(host,None,mapping,'s1')
  outcome='published'
 except ValueError as e:outcome=str(e);result=None
 return {'mutable':mutable,'nativeCatalogDrifts':drift,'outcome':outcome,'hostEntries':host.entered,'captureCalls':len(calls),'result':result}
for mutable,drift in ((False,False),(False,True),(True,False),(True,True)):
 r=invoke(old,mutable,drift);outputs.append(r)
assert outputs[0]['outcome']=='published' and outputs[1]['outcome']=='Accepted catalog changed during owned evaluation'
assert outputs[2]['outcome']=='published' and outputs[3]['outcome']=='published'
record={'scope':'Actual captured pre-fix wrapper/recipe/row projection and genuine original UMF evaluator; native recapture and host/cursor shells replaced. Retained actual native assessment and rows are replayed. Demonstrates mutable expected carrier custody only, not a native catalog attack.','sourceAtDispatchSha256':hashlib.sha256((OUT/'source-at-dispatch.py').read_bytes()).hexdigest(),'observations':outputs}
(OUT/'custody-probe.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'prechangeCounterexample':True,'cases':4}))
