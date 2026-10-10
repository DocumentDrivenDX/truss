"""Preserve native-only key meaning while authoring a core structural projection."""
from pathlib import Path
import copy,hashlib,json,sys
root=Path(__file__).resolve().parents[3]
source=root/'02-design/models/truss-layout-core-relational-0.1.proposal.umf.json'
gaps=root/'04-build/evidence/design-audit/core-relational-key-gaps.json'
model=json.loads(source.read_text()); original=copy.deepcopy(model)
entries=json.loads(gaps.read_text())['entries']; unsupported={(e['record'],e['key']) for e in entries}
module=next(m for m in model['modules'] if m['id']=='truss-layout')
residuals=[]
for record in module['elements']:
 if record.get('kind')!='record':continue
 retained=[]
 for key in record.get('keys',[]):
  if (record['id'],key['id']) not in unsupported:retained.append(key);continue
  residual={'originalKey':key,'unsupportedComponents':[e for e in entries if (e['record'],e['key'])==(record['id'],key['id'])],'interpretation':'native physical key descriptor; portable tuple generation unavailable'}
  record['extensions'].setdefault('truss.layout.native',{}).setdefault('physicalKeys',[]).append(residual)
  residuals.append({'record':record['id'],'key':key['id'],'fields':key['fields']})
 if retained:record['keys']=retained
 else:record.pop('keys',None)
portable_relationships=[]
for relationship in module['relationships']:
 if any((t['element'],t.get('key')) in unsupported for t in relationship['target']):
  owner=next(e for e in module['elements'] if e['id']==relationship['source'][0]['element'])
  owner['extensions'].setdefault('truss.layout.native',{}).setdefault('physicalForeignKeys',[]).append(copy.deepcopy(relationship))
  owner['references'].append({'role':'physical-fk:'+relationship['id'],'module':module['id'],'element':relationship['target'][0]['element']})
  for pair in relationship['fieldCorrespondence']:
   field=next(e for e in module['elements'] if e['id']==pair['source']['element'])
   field.setdefault('references',[]).append({'role':'physical-fk:'+relationship['id'],**pair['target']})
 else:portable_relationships.append(relationship)
module['relationships']=portable_relationships
model['id']='truss-layout-core-structural-0.2-review'
model['extensions']['truss.layout.native']['structuralProjection']={'sourceModel':str(source.relative_to(root)),'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'gapInventorySha256':hashlib.sha256(gaps.read_bytes()).hexdigest(),'scope':'Historical 0.12 core column/association projection with all native-only keys retained explicitly; no complete native interpretation, current 0.15 mapping or DDL equivalence.'}
# Verify every removed core key survives byte-equivalent as an ordered descriptor.
oldmod=next(m for m in original['modules'] if m['id']=='truss-layout')
for item in residuals:
 old=next(r for r in oldmod['elements'] if r['id']==item['record'])
 new=next(r for r in module['elements'] if r['id']==item['record'])
 oldkey=next(k for k in old['keys'] if k['id']==item['key'])
 assert any(r['originalKey']==oldkey for r in new['extensions']['truss.layout.native']['physicalKeys'])
for relationship in oldmod['relationships']:
 if any((t['element'],t.get('key')) in unsupported for t in relationship['target']):
  owner=next(e for e in module['elements'] if e['id']==relationship['source'][0]['element'])
  assert relationship in owner['extensions']['truss.layout.native']['physicalForeignKeys']
  assert {'role':'physical-fk:'+relationship['id'],'module':module['id'],'element':relationship['target'][0]['element']} in owner['references']
  for pair in relationship['fieldCorrespondence']:
   field=next(e for e in module['elements'] if e['id']==pair['source']['element'])
   assert {'role':'physical-fk:'+relationship['id'],**pair['target']} in field['references']
 else:assert relationship in module['relationships']
assert len(residuals)==11 and len(module['relationships'])==57
out=root/'02-design/models/truss-layout-core-structural-0.2.proposal.umf.json'
text=json.dumps(model,separators=(',',':'),ensure_ascii=False)+'\n'
if '--check' in sys.argv:assert out.read_text()==text
else:out.write_text(text)
print(json.dumps({'nativeKeysPreserved':len(residuals),'portableKeys':sum(len(e.get('keys',[])) for e in module['elements']),'scope':'structural projection only'}))
