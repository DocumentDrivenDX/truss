"""Core-driven review diagram; never a native/schema equivalence verdict."""
from pathlib import Path
import json,hashlib,html,sys
root=Path(__file__).resolve().parents[3]
p=root/'02-design/models/truss-layout-core-relational-0.1.proposal.umf.json'
validation=json.loads((root/'04-build/evidence/design-audit/core-relational-layout-validation.json').read_text())
assert validation['modelSha256']==hashlib.sha256(p.read_bytes()).hexdigest(), 'validation/model drift'
d=json.loads(p.read_text());m=next(x for x in d['modules'] if x['id']=='truss-layout')
fields={x['id']:x for x in m['elements'] if x.get('kind')=='field'}
records=[x for x in m['elements'] if x.get('kind')=='record'];ids={x['id']:'T'+str(i) for i,x in enumerate(records)}
lines=['flowchart LR','  REVIEW["DRAFT CORE STRUCTURE — native key interpretation unresolved"]']
nodeinventory=[];edgeinventory=[]
for record in records:
 rows=[];keyfields={}
 for k in record.get('keys',[]):
  for f in k['fields']:keyfields.setdefault(f['element'],set()).add('PK' if k.get('primary') else 'UK')
 for f in record['members']:
  field=fields[f['element']];assert f['module']==m['id']
  keys='/'.join(sorted(keyfields.get(field['id'],[])))
  rows.append(html.escape(field['name']+' : '+field.get('scalarType','unknown')+(' ['+keys+']' if keys else ''),quote=True))
 label=html.escape(record['name'],quote=True)+'<br/>'+'<br/>'.join(rows)
 lines.append('  '+ids[record['id']]+'["'+label+'"]')
 nodeinventory.append({'record':record['id'],'fields':[f['element'] for f in record['members']],'keys':[k['id'] for k in record.get('keys',[])]})
for r in m['relationships']:
 assert len(r['source'])==len(r['target'])==1
 source=r['source'][0];target=r['target'][0]
 assert source['module']==target['module']==m['id']
 owner=next(x for x in records if x['id']==target['element']);assert any(k['id']==target['key'] for k in owner.get('keys',[]))
 # Association arrows deliberately do not encode nullable/deferred FK cardinality.
 lines.append('  '+ids[source['element']]+' -->|"'+html.escape(r['name'],quote=True)+'"| '+ids[target['element']])
 edgeinventory.append({'relationship':r['id'],'source':source,'target':target,'fieldCorrespondence':r['fieldCorrespondence']})
assert len(records)==46 and len(fields)==442 and len(edgeinventory)==61
text='\n'.join(lines)+'\n';out=root/'02-design/models/truss-layout-core-relational-0.1.review.mmd'
receipt={'scope':'Diagram generated only from core candidate structure; no native extension tree traversal, DDL or semantic qualification','modelSha256':hashlib.sha256(p.read_bytes()).hexdigest(),'modelValid':validation['valid'],'status':'draft-unresolved-native-key-interpretation','records':nodeinventory,'relationships':edgeinventory,'diagramSha256':hashlib.sha256(text.encode()).hexdigest()}
rout=root/'04-build/evidence/design-audit/core-layout-er-source.json';rtext=json.dumps(receipt,separators=(',',':'))+'\n'
if '--check' in sys.argv:assert out.read_text()==text and rout.read_text()==rtext
else:out.write_text(text);rout.write_text(rtext)
print('Core-only diagram: 46 Records, 442 Fields, 59 Keys, 61 associations; draft, not native-qualified.')
