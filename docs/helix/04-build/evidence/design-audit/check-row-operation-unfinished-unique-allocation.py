"""Source identity/predicate correspondence only; no installation or native enforcement."""
from pathlib import Path
import json,hashlib,copy
R=Path(__file__).resolve().parents[3];B=Path(__file__).parent
P=R/'02-design/models/truss-row-operation-unfinished-unique.physical-ids.proposal.json'
def require(ok,message):
 if not ok:raise ValueError(message)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def file(p):return R.parent.parent/ p if p.startswith('docs/helix/') else R/p
def unpack(n):
 if n['kind']=='object':return {k:unpack(v) for k,v in n['members'].items()}
 if n['kind']=='array':return [unpack(v) for v in n['items']]
 return n.get('value')
def pointer(d,p):
 for k in p.split('/')[1:]:d=d[int(k)] if isinstance(d,list) else d[k]
 return d
def strip(v):
 if isinstance(v,dict):return {k:strip(x) for k,x in v.items() if k!='location'}
 if isinstance(v,list):return [strip(x) for x in v]
 return v
def strings(*values):return [{'String':{'sval':v}} for v in values]
a=json.loads(P.read_text());require(len(a['entries'])==1,'one created identity required');e=a['entries'][0];s=a['sources'][0]
source=file(s['source']);model=file(s['model']);require(sha(source)==s['sourceSha256'] and sha(model)==s['modelSha256'],'original source/model pins')
r=json.loads((B/'row-operation-unfinished-unique-source.json').read_text());require(r['sourceSha256']==sha(source) and r['artifactSha256']==sha(model),'source receipt pins')
d=json.loads(model.read_text());node=pointer(d,e['capturedModelLocator']['jsonPointer']);require(node==e['originalNativeNode'],'full original node correspondence');require(e['capturedModelLocator']['modelSha256']==sha(model),'locator pin')
raw=unpack(node)
expected={'idxname':'row_home_operation_unfinished_xid','relation':{'schemaname':'truss','relname':'row_home_operation','inh':True,'relpersistence':'p'},'accessMethod':'btree','indexParams':[{'IndexElem':{'name':'original_writer_xid','ordering':'SORTBY_DEFAULT','nulls_ordering':'SORTBY_NULLS_DEFAULT'}}],'whereClause':{'A_Expr':{'kind':'AEXPR_OP','name':strings('pg_catalog','<>'),'lexpr':{'ColumnRef':{'fields':strings('phase')}},'rexpr':{'A_Const':{'sval':{'sval':'application_finalized'}}}}},'unique':True}
def validate(v):require(strip(v)==expected,'exact index/predicate grammar')
validate(raw)
ref=a['referencedAllocation'];parent=file(ref['path']);require(sha(parent)==ref['sha256'],'parent allocation pin');p=json.loads(parent.read_text());entries={x['entryId']:x for x in p['entries']}
require(e['entryId']=='truss.row-home.index.row_home_operation_unfinished_xid' and e['nativeName']==raw['idxname'] and e['objectKind']=='index','authored identity/name/kind')
require(e['parentEntryId']==ref['tableEntryId']=='truss.row-home.table.row_home_operation','original parent identity')
require(ref['columnEntryIds']==['truss.row-home.column.row_home_operation.original_writer_xid','truss.row-home.column.row_home_operation.phase'],'exact referenced columns')
for id in [ref['tableEntryId'],*ref['columnEntryIds']]:
 x=entries[id];loc=x['capturedModelLocator'];m=file(loc['modelPath']);require(sha(m)==loc['modelSha256'],'parent model pin');require(pointer(json.loads(m.read_text()),loc['jsonPointer'])==x['originalNativeNode'],'parent original node')
for source_pin in p['sources']:
 require(sha(file(source_pin['source']))==source_pin['sourceSha256'] and sha(file(source_pin['model']))==source_pin['modelSha256'],'parent source/archive pins')
table=unpack(entries[ref['tableEntryId']]['originalNativeNode']);require(table['relation']['schemaname']=='truss' and table['relation']['relname']=='row_home_operation','qualified registry parent')
for name,typ in [('original_writer_xid','xid8'),('phase','text')]:
 c=next(x['ColumnDef'] for x in table['tableElts'] if x.get('ColumnDef',{}).get('colname')==name)
 require(unpack(entries['truss.row-home.column.row_home_operation.'+name]['originalNativeNode'])==c,'referenced column table membership')
 require(c['typeName']['names']==strings(typ),'original registry type');require(any(x['Constraint']['contype']=='CONSTR_NOTNULL' for x in c['constraints']),'nonnull xid/phase')
controls=[]
for name,change in [('nonunique',lambda v:v.update(unique=False)),('wrong-key',lambda v:v['indexParams'][0]['IndexElem'].update(name='operation_ordinal')),('reversed-predicate',lambda v:v['whereClause']['A_Expr'].update(name=strings('pg_catalog','='))),('unqualified-predicate-operator',lambda v:v['whereClause']['A_Expr'].update(name=strings('<>'))),('wrong-parent',lambda v:v['relation'].update(relname='row_home_scalar')),('concurrent-creation',lambda v:v.update(concurrent=True))]:
 v=copy.deepcopy(raw);change(v)
 try:validate(v)
 except ValueError:controls.append(name)
 else:raise RuntimeError('accepted substituted index: '+name)
receipt={'status':'pass','scope':'one original source-bound partial index identity, full selected predicate grammar and existing registry table/column source correspondence; no actual native dependency/grant/definition/adoption or enforcement','allocationSha256':sha(P),'createdEntries':1,'referencedEntries':3,'expectedRefusals':controls,'nativeExecution':False,'installable':False}
(B/'row-operation-unfinished-unique-allocation.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
