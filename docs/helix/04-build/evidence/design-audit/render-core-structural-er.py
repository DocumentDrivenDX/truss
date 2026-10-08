"""Render validated core structure and explicit physical-FK references; no DDL."""
from pathlib import Path
import hashlib,html,json,subprocess,sys
root=Path(__file__).resolve().parents[3]
modelpath=root/'02-design/models/truss-layout-core-structural-0.2.proposal.umf.json'
validation=json.loads((root/'04-build/evidence/design-audit/core-structural-layout-validation.json').read_text())
assert validation['valid'] and validation['modelSha256']==hashlib.sha256(modelpath.read_bytes()).hexdigest()
module=next(m for m in json.loads(modelpath.read_text())['modules'] if m['id']=='truss-layout')
fields={e['id']:e for e in module['elements'] if e.get('kind')=='field'}
records=[e for e in module['elements'] if e.get('kind')=='record']
ids={r['id']:'T'+str(i) for i,r in enumerate(records)}
fieldowners={member['element']:record['id'] for record in records for member in record['members']}
assert len(fieldowners)==len(fields)==442
edges=[]
for rel in module['relationships']:
 source=rel['source'][0];target=rel['target'][0]
 assert len(rel['source'])==len(rel['target'])==1 and source['module']==target['module']==module['id']
 edges.append({'id':rel['id'],'name':rel['name'],'source':source['element'],'target':target['element'],'fields':rel['fieldCorrespondence'],'kind':'core relationship'})
for record in records:
 for ref in record.get('references',[]):
  if not ref['role'].startswith('physical-fk:'):continue
  assert ref['module']==module['id'] and ref['element'] in ids
  pairs=[]
  for member in record['members']:
   for target in fields[member['element']].get('references',[]):
    if target['role']==ref['role']:
     assert target['module']==module['id'] and fieldowners[target['element']]==ref['element']
     pairs.append({'source':member,'target':{'module':target['module'],'element':target['element']}})
  assert pairs
  edges.append({'id':ref['role'].split(':',1)[1],'name':ref['role'],'source':record['id'],'target':ref['element'],'fields':pairs,'kind':'physical FK reference; native semantics unresolved'})
assert len(records)==46 and len(edges)==len({e['id'] for e in edges})==61
# Independent original association inventory: never redefine missing edges away.
original=json.loads((root/'02-design/models/truss-layout-core-relational-0.1.proposal.umf.json').read_text())
originalmod=next(m for m in original['modules'] if m['id']==module['id'])
expected={e['id']:(e['source'][0]['element'],e['target'][0]['element'],e['fieldCorrespondence']) for e in originalmod['relationships']}
assert {e['id']:(e['source'],e['target'],e['fields']) for e in edges}==expected
lines=['digraph layout {','graph [rankdir=LR, pack=true, packmode="array_u4", bgcolor="white", label="Historical 0.12 core structure — native-only key semantics retained separately", labelloc=t, fontname="Helvetica"];','node [shape=plain,fontname="Helvetica"];','edge [fontname="Helvetica",fontsize=9];']
for record in records:
 keyfields={}
 for key in record.get('keys',[]):
  for ref in key['fields']:keyfields.setdefault(ref['element'],[]).append('PK' if key.get('primary') else 'UK')
 rows=[]
 for ref in record['members']:
  assert ref['module']==module['id'];field=fields[ref['element']]
  label=field['name']+' : '+field.get('scalarType','unknown')+' ('+field['nullability']+')'
  if ref['element'] in keyfields:label+=' ['+'/'.join(sorted(set(keyfields[ref['element']])))+']'
  rows.append('<TR><TD ALIGN="LEFT">'+html.escape(label)+'</TD></TR>')
 label='<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0"><TR><TD BGCOLOR="#e9eef5"><B>'+html.escape(record['name'])+'</B></TD></TR>'+''.join(rows)+'</TABLE>'
 lines.append(ids[record['id']]+' [label=<'+label+'>];')
for edge in edges:
 native=edge['kind'].startswith('physical');label=edge['name']+(' (native)' if native else '')
 lines.append(ids[edge['source']]+' -> '+ids[edge['target']]+' [label='+json.dumps(label)+(', style=dashed' if native else '')+'];')
lines.append('}');text='\n'.join(lines)+'\n'
dotpath=root/'02-design/models/truss-layout-core-structural-0.2.review.dot'
svgpath=root/'02-design/models/truss-layout-core-structural-0.2.review.svg'
receiptpath=root/'04-build/evidence/design-audit/core-structural-er-source.json'
receipt={'modelSha256':validation['modelSha256'],'valid':validation['valid'],'complete':validation['complete'],'recordCount':len(records),'fieldCount':len(fields),'portableKeyCount':sum(len(r.get('keys',[])) for r in records),'associationCount':len(edges),'associations':edges,'dotSha256':hashlib.sha256(text.encode()).hexdigest(),'scope':'Historical core/explicit-reference diagram. All original associations compared independently; no native key interpretation, current-layout parity, DDL or installed support.'}
if '--check' in sys.argv:
 assert dotpath.read_text()==text
 retained=json.loads(receiptpath.read_text());assert all(retained[k]==v for k,v in receipt.items())
 assert retained['svgSha256']==hashlib.sha256(svgpath.read_bytes()).hexdigest()
else:
 dotpath.write_text(text);subprocess.run(['/opt/homebrew/bin/dot','-Tsvg',str(dotpath),'-o',str(svgpath)],check=True)
 receipt['svgSha256']=hashlib.sha256(svgpath.read_bytes()).hexdigest();receipt['renderer']=subprocess.check_output(['/opt/homebrew/bin/dot','-V'],stderr=subprocess.STDOUT,text=True).strip()
 receiptpath.write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:receipt[k] for k in ['recordCount','fieldCount','portableKeyCount','associationCount','valid','complete']}))
