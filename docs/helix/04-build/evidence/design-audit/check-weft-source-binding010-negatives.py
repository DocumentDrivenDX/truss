"""Independent damaged packet copies; no compiler/native qualification."""
import base64,hashlib,json,shutil,subprocess,sys,tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[5]
P=R/'docs/helix/04-build/evidence/weft-source-binding010'
C=Path(__file__).with_name('check-weft-source-binding010.py')
def raw(v):return json.dumps(v,ensure_ascii=False,separators=(',',':')).encode()
def change_artifact(a,v):
 b=raw(v);a['bytesBase64']=base64.b64encode(b).decode();a['sha256']=hashlib.sha256(b).hexdigest()
cases=[]
for name in ['payload_corruption','profile_authority','missing_column','wrong_original_model']:
 with tempfile.TemporaryDirectory() as tmp:
  p=Path(tmp)/'packet';shutil.copytree(P,p)
  b=json.loads((p/'binding.json').read_bytes())
  if name=='payload_corruption':b['entities'][0]['source']['sha256']='0'*64
  elif name=='profile_authority':
   profiles=json.loads((p/'profile-definitions.json').read_bytes())
   profiles[b['bindingProfile']['identity']]['registered']=True
   (p/'profile-definitions.json').write_bytes(raw(profiles))
  elif name=='missing_column':
   a=b['basis']['layoutInventory'];v=json.loads(base64.b64decode(a['bytesBase64']));v['tables'][0]['columns'].pop();change_artifact(a,v)
  else:(p/'original-model.json').write_bytes(b'{}')
  (p/'binding.json').write_bytes(raw(b))
  result=subprocess.run([sys.executable,str(C),str(p)],capture_output=True,text=True)
  if result.returncode==0:raise ValueError('damaged packet accepted: '+name)
  cases.append({'case':name,'rejected':True})
receipt={'scope':'four deliberately corrupted source packet copies rejected by independent integrity/source validator; no compiler/native execution','cases':cases,'nativeQualified':False}
(P/'negative-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
