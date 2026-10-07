"""Independent exact artifact/profile/source closure checks, not native admission."""
import json,hashlib,base64,sys
from pathlib import Path
R=Path(__file__).resolve().parents[5];P=Path(sys.argv[1]) if len(sys.argv)>1 else R/'docs/helix/04-build/evidence/weft-source-binding08'
def raw(v):return json.dumps(v,ensure_ascii=False,separators=(',',':')).encode()
def sha(b):return hashlib.sha256(b).hexdigest()
binding_bytes=(P/'binding.json').read_bytes();b=json.loads(binding_bytes);profiles=json.loads((P/'profile-definitions.json').read_bytes());count=0;decoded_bytes=0
if len(binding_bytes)>4194304:raise ValueError('binding ceiling')
def visit(v):
 global count,decoded_bytes
 if isinstance(v,list):
  for x in v:visit(x)
 elif isinstance(v,dict):
  if 'bytesBase64' in v:
   data=base64.b64decode(v['bytesBase64'],validate=True)
   if base64.b64encode(data).decode()!=v['bytesBase64'] or sha(data)!=v['sha256']:raise ValueError('artifact corruption')
   count+=1;decoded_bytes+=len(data)
   try:tree=json.loads(data)
   except (ValueError,UnicodeDecodeError):tree=None
   if tree is not None:visit(tree)
  elif set(v)=={'identity','version','sha256'}:
   body=profiles.get(v['identity'])
   if body is None or v['version']!=body['version'] or sha(raw(body))!=v['sha256']:raise ValueError('unknown/stale profile')
   if body['registered'] or body['nativeQualified']:raise ValueError('fabricated profile authority')
  for k,x in v.items():
   if k!='bytesBase64':visit(x)
visit(b)
if decoded_bytes>4194304:raise ValueError('recursive decoded closure ceiling')
def decode(a):return base64.b64decode(a['bytesBase64'],validate=True)
model_bytes=(P/'original-model.json').read_bytes();doc=json.loads(model_bytes);record,field=doc['modules'][0]['elements'];entity=b['entities'][0];prop=b['properties'][0]
if decode(entity['source'])!=model_bytes or decode(prop['source'])!=model_bytes:raise ValueError('original source byte mismatch')
if json.loads(decode(entity['acceptedDefinition']))!=record or json.loads(decode(prop['acceptedDefinition']))!=field:raise ValueError('original definition mismatch')
bundle=json.loads(decode(b['basis']['modelBundle']))
if bundle[0]['documentJson'].encode()!=model_bytes or bundle[0]['pin']['sha256']!=sha(model_bytes):raise ValueError('original model pin mismatch')
inv=json.loads(decode(b['basis']['layoutInventory']));source=(R/inv['sourceInventory']['path']).read_bytes()
if sha(source)!=inv['sourceInventory']['sha256']:raise ValueError('stale inventory source')
layout=json.loads(source)
if sha((R/inv['astPath']).read_bytes())!=inv['astSha256']:raise ValueError('stale AST')
expected={(t['name'],c['name'],c['definitionPointer']) for t in layout['tables'] for c in t['columns']}
observed={(t['name'],c['name'],c['definitionPointer']) for t in inv['tables'] for c in t['columns']}
if expected!=observed or len(observed)!=386:raise ValueError('incomplete column selection')
home=json.loads(decode(prop['homeDefinition']))
if decode(home['layoutInventory'])!=decode(b['basis']['layoutInventory']):raise ValueError('mixed inventories')
if home['ownerCatalogId']!=entity['typeId'] or home['propertyCatalogId']!=prop['propertyId'] or prop['ownerTypeId']!=entity['typeId']:raise ValueError('mixed typed owner')
cols={c['physicalIdentity']:(t['name'],c['name']) for t in inv['tables'] for c in t['columns']}
if cols.get(home['propsColumnPhysicalIdentity'])!=('object','props') or cols.get(home['discriminatorColumnPhysicalIdentity'])!=('object','type_id'):raise ValueError('wrong physical selector')
qualification=json.loads(decode(b['qualification'][0]))
if qualification['nativeQualified'] or qualification['bindingAdopted'] or qualification['queryExecuted']:raise ValueError('unsupported support claim')
receipt={'scope':'Exact original source/profile/artifact closure and complete declared column-map correspondence only; no compiler execution, native catalog or registry admission','bindingSha256':sha(binding_bytes),'bindingBytes':len(binding_bytes),'recursiveArtifactOccurrences':count,'decodedOccurrenceBytes':decoded_bytes,'declaredColumns':len(observed),'nativeQualified':False}
(P/'integrity-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
