"""Independent original-input composition check; no database or semantic resolver."""
import json,hashlib,copy
from pathlib import Path
R=Path(__file__).resolve().parents[5]
def decode(n):
 if n['kind']=='object':return {k:decode(v) for k,v in n['members'].items()}
 if n['kind']=='array':return [decode(x) for x in n['items']]
 if n['kind']=='number':return json.loads(n['value'])
 return n.get('value')
def strip(x):
 if isinstance(x,dict):return {k:strip(v) for k,v in x.items() if k not in ('location','stmt_location','stmt_len')}
 if isinstance(x,list):return [strip(v) for v in x]
 return x
p=R/'docs/helix/04-build/evidence/design-audit/weft-review-layout-composition.json';receipt=json.loads(p.read_text());groups=[]
for pin in receipt['inputs']:
 b=(R/pin['path']).read_bytes()
 if hashlib.sha256(b).hexdigest()!=pin['sha256']:raise ValueError('stale input')
 d=json.loads(b);groups.append(decode(d['modules'][0]['elements'][0]['extensions']['umf.postgresql']['root'])['stmts'])
expected=copy.deepcopy(groups[0]);owner={n['stmt']['CreateStmt']['relation']['relname']:n for n in groups[1] if 'CreateStmt' in n['stmt']}
for i,n in enumerate(expected):
 c=n['stmt'].get('CreateStmt')
 if c and c['relation']['relname'] in owner:expected[i]=owner.pop(c['relation']['relname'])
 if 'CommentStmt' in n['stmt'] and n['stmt']['CommentStmt']['objtype']=='OBJECT_SCHEMA':n['stmt']['CommentStmt']['comment']='truss-layout weft-review-0.3 REVIEW ONLY - unqualified'
if owner:raise ValueError('unmatched replacements')
expected.extend(n for n in groups[1] if 'CreateStmt' not in n['stmt'])
for group in groups[2:]:expected.extend(group)
b=(R/receipt['astPath']).read_bytes()
if hashlib.sha256(b).hexdigest()!=receipt['astSha256']:raise ValueError('stale saved AST')
actual=json.loads(b)
if strip(expected)!=strip(actual):raise ValueError('complete ordered native AST mismatch')
for path,hashkey in [('sqlPath','sqlSha256'),('modelPath','modelSha256')]:
 if hashlib.sha256((R/receipt[path]).read_bytes()).hexdigest()!=receipt[hashkey]:raise ValueError('stale output')
print(json.dumps({'scope':'Complete ordered saved native AST versus eight pinned original source models, except source locations; not native execution or binding adoption','statements':len(actual),'tables':sum('CreateStmt' in n['stmt'] for n in actual),'exactOrderedSourceComposition':True}))
