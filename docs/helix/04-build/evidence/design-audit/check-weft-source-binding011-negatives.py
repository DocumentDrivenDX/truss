"""Independent damaged packet copies; no compiler/native qualification."""
import base64,hashlib,json,shutil,subprocess,sys,tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[5]
if len(sys.argv)>2:raise SystemExit('usage: check-weft-source-binding011-negatives.py [packet-directory]')
P=Path(sys.argv[1]) if len(sys.argv)==2 else R/'docs/helix/04-build/evidence/weft-source-binding011'
C=Path(__file__).with_name('check-weft-source-binding011.py')
def raw(v):return json.dumps(v,ensure_ascii=False,separators=(',',':')).encode()
def change_artifact(a,v):
 b=raw(v);a['bytesBase64']=base64.b64encode(b).decode();a['sha256']=hashlib.sha256(b).hexdigest()
cases=[]
for name in ['payload_corruption','profile_authority','missing_column','wrong_original_model','wrong_layout_sql','duplicate_physical_identity','wrong_table_pointer','wrong_value_family','wrong_value_root','wrong_presence_profile','wrong_codec_family','unknown_packet_version','mixed_packet_version']:
 with tempfile.TemporaryDirectory() as tmp:
  p=Path(tmp)/'packet';shutil.copytree(P,p)
  b=json.loads((p/'binding.json').read_bytes())
  if name=='unknown_packet_version':b['bindingProfileId']='truss-postgresql-source-review/0.99.0-fixture'
  elif name=='mixed_packet_version':b['bindingProfileId']='truss-postgresql-source-review/0.11.0-fixture' if '/0.12.' in b['bindingProfileId'] else 'truss-postgresql-source-review/0.12.0-fixture'
  elif name=='payload_corruption':b['entities'][0]['source']['sha256']='0'*64
  elif name=='profile_authority':
   profiles=json.loads((p/'profile-definitions.json').read_bytes())
   profiles[b['bindingProfile']['identity']]['registered']=True
   (p/'profile-definitions.json').write_bytes(raw(profiles))
  elif name=='missing_column':
   a=b['basis']['layoutInventory'];v=json.loads(base64.b64decode(a['bytesBase64']));v['tables'][0]['columns'].pop();change_artifact(a,v)
  elif name=='wrong_original_model':(p/'original-model.json').write_bytes(b'{}')
  elif name=='wrong_layout_sql':change_artifact(b['basis']['layoutSql'],{'wrong':'sql'})
  elif name in ('wrong_value_family','wrong_value_root','wrong_codec_family'):
   a=b['properties'][0]['valueDefinition'];v=json.loads(base64.b64decode(a['bytesBase64']))
   if name=='wrong_value_family':v['nodes'][0]['shape']['family']='decimal'
   elif name=='wrong_value_root':v['rootNodeId']='foreign-root'
   else:
    ca=v['nodes'][0]['codecDefinition'];cv=json.loads(base64.b64decode(ca['bytesBase64']));cv['rule']['family']='boolean';change_artifact(ca,cv)
   change_artifact(a,v)
  elif name=='wrong_presence_profile':
   a=b['properties'][0]['presenceDefinition'];v=json.loads(base64.b64decode(a['bytesBase64']));v['profile']=b['basis']['layoutProfile'];change_artifact(a,v)
  else:
   a=b['basis']['layoutInventory'];v=json.loads(base64.b64decode(a['bytesBase64']))
   if name=='duplicate_physical_identity':v['tables'][1]['physicalIdentity']=v['tables'][0]['physicalIdentity']
   else:v['tables'][0]['createPointer']='/wrong'
   change_artifact(a,v)
  (p/'binding.json').write_bytes(raw(b))
  result=subprocess.run([sys.executable,str(C),str(p)],capture_output=True,text=True)
  if result.returncode==0:raise ValueError('damaged packet accepted: '+name)
  cases.append({'case':name,'rejected':True})
receipt={'scope':'thirteen deliberately corrupted source packet copies rejected by independent integrity/source validator; no compiler/native execution','cases':cases,'nativeQualified':False}
(P/'negative-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
