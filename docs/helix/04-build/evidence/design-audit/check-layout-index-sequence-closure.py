"""Explicit source index/sequence references; not native dependency resolution."""
import hashlib,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[5]
version=sys.argv[1] if len(sys.argv)>1 else '0.9'
if version not in ('0.9','0.10','0.11','0.12'):raise ValueError('unsupported inventory version')
P=R/f'docs/helix/02-design/contracts/weft-review-columns-v{version}.proposal.json'
inv=json.loads(P.read_bytes());astbytes=(R/inv['astPath']).read_bytes()
if hashlib.sha256(astbytes).hexdigest()!=inv['astSha256']:raise ValueError('stale AST')
ast=json.loads(astbytes);tables={t['name']:{c['name'] for c in t['columns']} for t in inv['tables']}
def walk(v):
 if isinstance(v,dict):
  yield v
  for x in v.values():yield from walk(x)
 elif isinstance(v,list):
  for x in v:yield from walk(x)
indexes=[]
for item in inv['indexes']:
 d=item['definition'];t=d['relation']
 if t.get('schemaname') not in (None,'truss') or t['relname'] not in tables:raise ValueError('foreign/missing index parent')
 cols=tables[t['relname']];refs=[]
 for node in walk(d):
  if 'IndexElem' in node and node['IndexElem'].get('name'):refs.append(node['IndexElem']['name'])
  if 'ColumnRef' in node:
   fields=node['ColumnRef']['fields']
   if len(fields)!=1 or 'String' not in fields[0]:raise ValueError('unsupported qualified/exotic index reference')
   refs.append(fields[0]['String']['sval'])
 if any(c not in cols for c in refs):raise ValueError('missing index column')
 indexes.append({'index':d['idxname'],'table':t['relname'],'columnReferences':sorted(set(refs))})
sequences={(n['stmt']['CreateSeqStmt']['sequence'].get('schemaname','truss'),n['stmt']['CreateSeqStmt']['sequence']['relname']) for n in ast if 'CreateSeqStmt' in n['stmt']}
defaults=[]
for t in inv['tables']:
 for c in t['columns']:
  for node in walk(c['constraints']):
   f=node.get('FuncCall')
   if not f:continue
   fn=[x['String']['sval'] for x in f['funcname']]
   if fn[-1]!='nextval':continue
   if len(f.get('args',[]))!=1:raise ValueError('unsupported nextval arity')
   arg=f['args'][0]
   if 'TypeCast' in arg:arg=arg['TypeCast']['arg']
   name=arg.get('A_Const',{}).get('sval',{}).get('sval')
   if not isinstance(name,str):raise ValueError('dynamic sequence reference unresolved')
   parts=name.split('.')
   key=tuple(parts) if len(parts)==2 else ('truss',name)
   if key not in sequences:raise ValueError('missing sequence '+name)
   defaults.append({'table':t['name'],'column':c['name'],'sequence':name})
receipt={'scope':f'all explicit index columns/expressions/predicates and literal nextval defaults resolve in declared {version} source; no native opclass/type/collation/OID/search-path or runtime routine-body dependency qualification','inventorySha256':hashlib.sha256(P.read_bytes()).hexdigest(),'indexes':indexes,'declaredSequences':sorted(sequences),'sequenceDefaults':defaults,'nativeQualified':False}
(R/('docs/helix/04-build/evidence/design-audit/layout-index-sequence-closure'+('' if version=='0.9' else '-v'+version)+'.json')).write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'explicitIndexes':len(indexes),'declaredSequences':len(sequences),'sequenceDefaults':len(defaults),'sourceClosure':True,'nativeQualified':False}))
