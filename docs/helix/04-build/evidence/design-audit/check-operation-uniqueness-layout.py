"""Independent ordered source addition check; no native installer qualification."""
import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[5]
def decode(n):
 if n['kind']=='object':return {k:decode(v) for k,v in n['members'].items()}
 if n['kind']=='array':return [decode(v) for v in n['items']]
 if n['kind']=='number':return json.loads(n['value'])
 return n.get('value')
def strip(v):
 if isinstance(v,dict):return {k:strip(x) for k,x in v.items() if k not in ('location','stmt_location','stmt_len')}
 if isinstance(v,list):return [strip(x) for x in v]
 return v
r=json.loads((R/'docs/helix/04-build/evidence/design-audit/operation-uniqueness-layout-profile-composition.json').read_text());parent=json.loads((R/'docs/helix/04-build/evidence/design-audit/feed-recovery-layout-profile-composition.json').read_text())
for p in r['inputs']:
 if hashlib.sha256((R/p['path']).read_bytes()).hexdigest()!=p['sha256']:raise ValueError('stale input')
if r['inputs'][0]['sha256']!=parent['modelSha256']:raise ValueError('wrong parent model')
b=(R/parent['astPath']).read_bytes()
if hashlib.sha256(b).hexdigest()!=parent['astSha256']:raise ValueError('stale parent AST')
expected=json.loads(b)
for n in expected:
 if n['stmt'].get('CommentStmt',{}).get('objtype')=='OBJECT_SCHEMA':n['stmt']['CommentStmt']['comment']='truss-layout weft-review-0.8 REVIEW ONLY - unqualified'
for pin in r['inputs'][1:]:
 d=json.loads((R/pin['path']).read_text());expected.extend(decode(d['modules'][0]['elements'][0]['extensions']['umf.postgresql']['root'])['stmts'])
for path,key in [('modelPath','modelSha256'),('sqlPath','sqlSha256'),('astPath','astSha256')]:
 if hashlib.sha256((R/r[path]).read_bytes()).hexdigest()!=r[key]:raise ValueError('stale output')
actual=json.loads((R/r['astPath']).read_text())
if strip(expected)!=strip(actual):raise ValueError('ordered AST addition mismatch')
print(json.dumps({'statements':len(actual),'tables':sum('CreateStmt' in n['stmt'] for n in actual),'exactSourceComposition':True,'nativeQualified':False}))
