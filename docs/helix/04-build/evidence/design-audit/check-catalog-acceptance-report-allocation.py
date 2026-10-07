"""Conditional report source identities only; no complete layout/native qualification."""
from pathlib import Path
from collections import Counter
import json,hashlib
R=Path(__file__).resolve().parents[5]
P=R/'docs/helix/02-design/models/truss-catalog-acceptance-report.physical-ids.proposal.json'
a=json.loads(P.read_text());assert a['profile']=='truss-conditional-report-physical-allocation/0.1.0' and a['complete'] is False
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def at(x,p):
 for k in p.strip('/').split('/'):
  k=k.replace('~1','/').replace('~0','~');x=x[int(k)] if isinstance(x,list) else x[k]
 return x
assert len(a['sources'])==1
s=a['sources'][0];assert sha(R/s['source'])==s['sourceSha256'] and sha(R/s['model'])==s['modelSha256']
receipt=json.loads((Path(__file__).parent/'catalog-acceptance-report-source.json').read_text())
assert s['sourceSha256']==receipt['sourceSha256'] and s['modelSha256']==receipt['artifactSha256']
x=json.loads((R/s['model']).read_text());entries=a['entries'];ids={e['entryId']:e for e in entries}
assert len(entries)==len(ids)==8
assert Counter(e['objectKind'] for e in entries)=={'table':1,'column':2,'constraint':4,'supporting-index':1}
for e in entries:
 assert e['nativeBinding']=={'state':'unresolved'}
 loc=e['capturedModelLocator'];assert loc['modelPath']==s['model'] and loc['modelSha256']==s['modelSha256']
 assert at(x,loc['jsonPointer'])==e['originalNativeNode']
 if e['objectKind']!='table':assert ids[e['parentEntryId']]['objectKind']=='table'
table=ids['truss.catalog-report.table.catalog_acceptance_report']
base='/modules/0/elements/0/extensions/umf.postgresql/root/members/stmts/items/0/members/stmt/members/CreateStmt'
assert table['capturedModelLocator']['jsonPointer']==base and table['objectKind']=='table'
assert table['nativeName']=='catalog_acceptance_report'
relation=table['originalNativeNode']['members']['relation']['members']
assert relation['schemaname']['value']=='truss' and relation['relname']['value']=='catalog_acceptance_report'
expected={('table',base)}
for i,element in enumerate(table['originalNativeNode']['members']['tableElts']['items']):
 prefix=base+'/members/tableElts/items/'+str(i)+'/members/'
 if 'ColumnDef' in element['members']:
  column=element['members']['ColumnDef'];pointer=prefix+'ColumnDef'
  expected.add(('column',pointer))
  for j,constraint in enumerate(column['members'].get('constraints',{}).get('items',[])):
   node=constraint['members']['Constraint'];kind=node['members']['contype']['value']
   cp=pointer+'/members/constraints/items/'+str(j)+'/members/Constraint'
   if kind in ['CONSTR_PRIMARY','CONSTR_FOREIGN','CONSTR_CHECK','CONSTR_UNIQUE']:
    expected.add(('constraint',cp))
    if kind in ['CONSTR_PRIMARY','CONSTR_UNIQUE']:expected.add(('supporting-index',cp))
 else:
  assert element['members']['Constraint']['members']['contype']['value']=='CONSTR_CHECK'
  expected.add(('constraint',prefix+'Constraint'))
actual={(e['objectKind'],e['capturedModelLocator']['jsonPointer']) for e in entries}
assert len(actual)==len(entries) and actual==expected
for e in entries:
 node=e['originalNativeNode']['members']
 if e['objectKind']=='column':
  assert e['nativeName']==node['colname']['value']
  assert e['entryId']=='truss.catalog-report.column.'+node['colname']['value']
 if e['objectKind']=='constraint':
  assert e['nativeName']==(node['conname']['value'] if 'conname' in node else None)
index=ids['truss.catalog-report.index.primary-support'];creator=ids[index['creatorEntryId']]
assert creator['objectKind']=='constraint' and creator['originalNativeNode']['members']['contype']['value']=='CONSTR_PRIMARY'
assert index['capturedModelLocator']==creator['capturedModelLocator'] and index['originalNativeNode']==creator['originalNativeNode']
ref=a['referencedAllocation'];assert sha(R/ref['path'])==ref['sha256']
original=json.loads((R/ref['path']).read_text());baseline={e['entryId']:e for e in original['entries']}
for e in ref['entries']:
 assert baseline[e['entryId']]==e
 loc=e['capturedModelLocator'];assert sha(R/loc['modelPath'])==loc['modelSha256']
 captured=at(json.loads((R/loc['modelPath']).read_text()),loc['jsonPointer'])
 if e['objectKind']=='table':
  relation=captured['members']['relation']['members']
  assert relation['schemaname']['value']=='truss' and relation['relname']['value']=='schema_rev'
 else:assert captured['members']['colname']['value']=='rev' and e['parentEntryId']=='truss.layout.table.schema_rev'
fk=ids['truss.catalog-report.constraint.revision-parent']
assert fk['referencedTableEntryId']=='truss.layout.table.schema_rev'
assert fk['referencedColumnEntryIds']==['truss.layout.column.schema_rev.rev']
assert fk['referencingColumnEntryIds']==['truss.catalog-report.column.rev']
n=fk['originalNativeNode']['members'];assert n['contype']['value']=='CONSTR_FOREIGN'
assert n['pktable']['members']['schemaname']['value']=='truss' and n['pktable']['members']['relname']['value']=='schema_rev'
assert [i['members']['String']['members']['sval']['value'] for i in n['pk_attrs']['items']]==['rev']
report={'status':'pass','scope':'complete selected table/column/catalog-constraint/PK-index source-node coverage for eight conditional identities; baseline revision table/column reference source correspondence; native naming/dependency/guard/grant/adoption/installation incomplete','entries':8,'allocationSha256':sha(P),'installable':False,'nativeExecution':False}
Path(__file__).with_name('catalog-acceptance-report-allocation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
