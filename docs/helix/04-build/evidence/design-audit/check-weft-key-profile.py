"""Independent expected source edits, not installed storage qualification."""
import json,hashlib,copy
from pathlib import Path
R=Path(__file__).resolve().parents[5]
def decode(n):
 if n['kind']=='object':return {k:decode(v) for k,v in n['members'].items()}
 if n['kind']=='array':return [decode(v) for v in n['items']]
 if n['kind']=='number':return json.loads(n['value'])
 return n.get('value')
def strip(n):
 if isinstance(n,dict):return {k:strip(v) for k,v in n.items() if k not in ('location','stmt_location','stmt_len')}
 if isinstance(n,list):return [strip(v) for v in n]
 return n
r=json.loads((R/'docs/helix/04-build/evidence/design-audit/weft-key-profile-composition.json').read_text())
parent=json.loads((R/'docs/helix/04-build/evidence/design-audit/weft-review-layout-composition.json').read_text())
for pin in r['inputs']:
 if hashlib.sha256((R/pin['path']).read_bytes()).hexdigest()!=pin['sha256']:raise ValueError('stale input')
if r['inputs'][0]['sha256']!=parent['modelSha256']:raise ValueError('parent model mismatch')
b=(R/parent['astPath']).read_bytes()
if hashlib.sha256(b).hexdigest()!=parent['astSha256']:raise ValueError('parent AST changed')
expected=[]
for n in json.loads(b):
 c=n['stmt'].get('CreateStmt')
 if c and c['relation']['relname']=='object_key':continue
 if c and c['relation']['relname']=='schema_rev':c['tableElts']=[e for e in c['tableElts'] if e.get('ColumnDef',{}).get('colname')!='report']
 if c and c['relation']['relname']=='key_tombstone':
  col=next(e['ColumnDef'] for e in c['tableElts'] if e.get('ColumnDef',{}).get('colname')=='entity_kind')
  check=next(e['Constraint'] for e in col['constraints'] if e['Constraint']['contype']=='CONSTR_CHECK')
  check['raw_expr']['A_Expr']['rexpr']['List']['items']=[{'A_Const':{'sval':{'sval':'e'}}}]
 if n['stmt'].get('CommentStmt',{}).get('objtype')=='OBJECT_SCHEMA':n['stmt']['CommentStmt']['comment']='truss-layout weft-review-0.4 REVIEW ONLY - unqualified'
 expected.append(n)
for pin in r['inputs'][1:]:
 d=json.loads((R/pin['path']).read_text());expected.extend(decode(d['modules'][0]['elements'][0]['extensions']['umf.postgresql']['root'])['stmts'])
for path,key in [('modelPath','modelSha256'),('sqlPath','sqlSha256'),('astPath','astSha256')]:
 if hashlib.sha256((R/r[path]).read_bytes()).hexdigest()!=r[key]:raise ValueError('stale output')
actual=json.loads((R/r['astPath']).read_text())
if strip(expected)!=strip(actual):raise ValueError('complete source edit/ordered addition mismatch')
print(json.dumps({'statements':len(actual),'tables':sum('CreateStmt' in n['stmt'] for n in actual),'completeSourceEditsMatch':True,'nativeQualified':False}))
