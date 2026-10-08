"""Independent exact artifact/profile/source closure checks, not native admission."""
import json,hashlib,base64,sys
from pathlib import Path
R=Path(__file__).resolve().parents[5];P=Path(sys.argv[1]) if len(sys.argv)>1 else R/'docs/helix/04-build/evidence/weft-source-binding011'
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
layout_sql='docs/helix/04-build/evidence/design-audit/truss-layout-reference-history-0.12.owner-export.sql' if b['bindingProfileId']=='truss-postgresql-source-review/0.12.0-fixture' else 'docs/helix/02-design/models/truss-layout-weft-review-0.11.proposal.sql'
if decode(b['basis']['layoutSql'])!=(R/layout_sql).read_bytes():raise ValueError('wrong layout SQL')
if [(t['name'],t['createPointer']) for t in inv['tables']]!=[(t['name'],t['createPointer']) for t in layout['tables']]:raise ValueError('table custody/order mismatch')
physical_ids=[t['physicalIdentity'] for t in inv['tables']]+[c['physicalIdentity'] for t in inv['tables'] for c in t['columns']]
if len(physical_ids)!=len(set(physical_ids)):raise ValueError('duplicate source physical identity')
if sum(len(t['columns']) for t in inv['tables'])!=442:raise ValueError('duplicate or missing declared columns')
expected={(t['name'],c['name'],c['definitionPointer']) for t in layout['tables'] for c in t['columns']}
observed={(t['name'],c['name'],c['definitionPointer']) for t in inv['tables'] for c in t['columns']}
if expected!=observed or len(observed)!=442:raise ValueError('incomplete column selection')
home=json.loads(decode(prop['homeDefinition']))
if decode(home['layoutInventory'])!=decode(b['basis']['layoutInventory']):raise ValueError('mixed inventories')
if home['ownerCatalogId']!=entity['typeId'] or home['propertyCatalogId']!=prop['propertyId'] or prop['ownerTypeId']!=entity['typeId']:raise ValueError('mixed typed owner')
cols={c['physicalIdentity']:(t['name'],c['name']) for t in inv['tables'] for c in t['columns']}
if cols.get(home['propsColumnPhysicalIdentity'])!=('object','props') or cols.get(home['discriminatorColumnPhysicalIdentity'])!=('object','type_id'):raise ValueError('wrong physical selector')
value=json.loads(decode(prop['valueDefinition']))
presence=json.loads(decode(prop['presenceDefinition']))
if value['profile']!=prop['valueProfile'] or presence['profile']!=prop['presenceProfile'] or home['valueProfile']!=prop['valueProfile'] or home['presenceProfile']!=prop['presenceProfile']:raise ValueError('mixed value/presence profiles')
if value['rootNodeId']!='label' or len(value['nodes'])!=1:raise ValueError('wrong fixture root')
node=value['nodes'][0]
if node['nodeId']!=value['rootNodeId'] or node['authoredIdentity']!=prop['logical']:raise ValueError('wrong original value node')
for a in [value['acceptedDefinition'],presence['acceptedDefinition'],node['authoredDefinition']]:
 if json.loads(decode(a))!=field:raise ValueError('mixed original field definitions')
codec=json.loads(decode(node['codecDefinition']))
if codec['profile']!=node['codecProfile'] or json.loads(decode(codec['authoredDefinition']))!=field:raise ValueError('mixed original codec custody')
if node['shape']!={'kind':'scalar','family':field['scalarType'],'storageRepresentation':'json-string'} or codec['rule']!={'family':field['scalarType'],'storageRepresentation':'json-string','encoding':'preserve-unicode-scalars','decodedCarrierKind':field['scalarType']}:raise ValueError('fixture scalar/codec family mismatch')
qualification=json.loads(decode(b['qualification'][0]))
if qualification['nativeQualified'] or qualification['bindingAdopted'] or qualification['queryExecuted']:raise ValueError('unsupported support claim')
receipt={'scope':'Exact original source/profile/artifact closure, original single-string root/field/presence/codec correspondence and complete declared column-map correspondence only; no compiler execution, native catalog or registry admission','bindingSha256':sha(binding_bytes),'bindingBytes':len(binding_bytes),'recursiveArtifactOccurrences':count,'decodedOccurrenceBytes':decoded_bytes,'declaredColumns':len(observed),'nativeQualified':False}
(P/'integrity-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
