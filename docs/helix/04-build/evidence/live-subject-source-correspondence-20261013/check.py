"""Readonly original Weft fixture-source probes; no database or authority."""
import hashlib,json,os,sys
from pathlib import Path
root=Path(__file__).resolve().parents[5]
module_dir=Path(os.environ['TRUSS_SUBJECT_OWNER_MODULE_DIR'])
sys.path.insert(0,str(module_dir));import weft
assert Path(weft.__file__).resolve()==(module_dir/'weft.so').resolve()
original=json.loads((root/'packages/python/tests/fixtures/security-mapping-request.json').read_text())
resolution=json.loads((root/'docs/helix/04-build/evidence/security-identity-requirements/resolution.json').read_text())
results=[]
for mode in ['original','module-pin-only','both-model-pins','hypothetical-named-document']:
 request=json.loads(json.dumps(original))
 if mode!='original':
  document=json.loads(json.dumps(resolution['documents'][0]['document']))
  if mode=='hypothetical-named-document':
   for element in document['modules'][0]['elements']:element['name']=element['id']
  source=json.dumps(document,separators=(',',':'))
  digest=hashlib.sha256(source.encode()).hexdigest()
  request['modules'][0]['documentJson']=source;request['modules'][0]['pin']['sha256']=digest
  if mode in ('both-model-pins','hypothetical-named-document'):
   profile=json.loads(request['queryProfileJson']);profile['modelPins'][0]['sha256']=digest
   request['queryProfileJson']=json.dumps(profile,separators=(',',':'))
 probe={'sourceSha256':request['modules'][0]['pin']['sha256'],'identity':{'module':'m','element':'Staff','key':'pk'}}
 result=json.loads(weft.inspect_security_mapping_subject_key_json(json.dumps(request),json.dumps(probe)))
 assert result['securityReady'] is False
 if mode in ('original','hypothetical-named-document'):assert result['status']=='inspected'
 else:
  assert result['status']=='refused'
  expected='WFT-SECURITY-QUERY-PROFILE' if mode=='module-pin-only' else 'WFT-NAME-MISSING'
  assert expected in [d['code'] for d in result['diagnostics']]
 results.append({'mode':mode,'result':result})
print(json.dumps({'extensionSha256':hashlib.sha256((module_dir/'weft.so').read_bytes()).hexdigest(),'cases':results},indent=2))
