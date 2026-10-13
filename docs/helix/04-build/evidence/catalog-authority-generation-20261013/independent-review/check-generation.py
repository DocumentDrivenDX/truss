"""Actual Bun evaluator protocol replay over retained historical native cells."""
from pathlib import Path
from hashlib import sha256
import json,subprocess
from security_catalog_read import _catalog_record_cells
ROOT=Path('/private/tmp/truss-security-main-integration')
SOURCE=ROOT/'scripts/evaluate-security-captured-identity-fixture.ts'
CAPTURE=ROOT/'docs/helix/04-build/evidence/accepted-catalog-policy-read-20261013/capture.json'
before=sha256(SOURCE.read_bytes()).hexdigest()
capture=json.loads(CAPTURE.read_bytes())[0]
base={'cells':_catalog_record_cells(capture['recipes'],capture['rows']),'subjectKey':[{'string':'s1'}],'resultMode':'resources'}
results=[]
def check(name,generation,valid,include=True):
 packet=dict(base)
 if include:packet['authorityGeneration']=generation
 result=subprocess.run(['/opt/homebrew/bin/bun',str(SOURCE),'--named-source'],cwd=ROOT,input=json.dumps(packet),capture_output=True,text=True,timeout=4)
 if valid:
  assert result.returncode==0,(name,result.stderr)
  decision=json.loads(result.stdout)
  assert [r['key'] for r in decision['rows']]==[[{'string':'r1'}]]
  assert decision['rows'][0]['output'][0]['disposition']=='withheld'
 else:
  assert result.returncode!=0 and result.stdout==''
  assert 'Exact bounded native authority generation required' in result.stderr
 results.append({'control':name,'passed':True,'returnCode':result.returncode})
check('legacy-optional-absent',None,True,False)
for g in ('1','2','9223372036854775807'):check('accepted:'+g,g,True)
for g in (0,True,None,{},[],0.5,'','0','01','-1','+1','1.0','1e0','9223372036854775808','1'*20,'1\n',' 1'):
 check('refused:'+repr(g),g,False)
assert before==sha256(SOURCE.read_bytes()).hexdigest()
result={'scope':'Actual Bun evaluator over historical native captured cells; protocol grammar and selected original decisions only, no current native capture/authority proof.','sourceSha256':before,'captureSha256':sha256(CAPTURE.read_bytes()).hexdigest(),'passed':len(results),'controls':results}
Path(__file__).with_name('generation-results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'passed':len(results),'sourceSha256':before}))
