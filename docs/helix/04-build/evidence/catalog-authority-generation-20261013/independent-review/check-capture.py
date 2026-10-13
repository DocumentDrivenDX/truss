"""Actual wrapper snapshots native comparison before source file callbacks."""
from pathlib import Path
from hashlib import sha256
from unittest.mock import patch
import inspect,json
import security_catalog_read as m
ROOT=Path('/private/tmp/truss-security-main-integration')
request=(m.BASE/'mapping-request.json').read_bytes()
assessment=(ROOT/'docs/helix/04-build/evidence/accepted-catalog-policy-read-20261013/assessment.json').read_bytes()
original=(b'original',b'profile',1)
mapping=m.PreparedSecurityMapping(request,b'',accepted_catalog_assessment=assessment,native_guard=original)
class Host:
 def _run_operation(self,transaction,execute):
  guard=inspect.getclosurevars(execute).nonlocals['guard']
  return inspect.getclosurevars(guard).nonlocals['expected_guard']
read=Path.read_bytes;entered=[]
def reading(path):
 if not entered:
  entered.append(str(path));object.__setattr__(mapping,'native_guard',(b'replaced',b'profile',2))
 return read(path)
with patch.object(Path,'read_bytes',reading):result=m.run_owned_catalog_resource_read(Host(),object(),mapping,'s1')
assert result==original and mapping.native_guard!=original and len(entered)==1
source=ROOT/'scripts/security_catalog_read.py'
result={'scope':'Actual wrapper with synthetic host handoff; mutation via source-read callback. No native database or authority proof.','sourceSha256':sha256(source.read_bytes()).hexdigest(),'passed':1,'control':'original native guard retained across post-snapshot mapping replacement','enteredSourceRead':entered[0]}
Path(__file__).with_name('capture-results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
