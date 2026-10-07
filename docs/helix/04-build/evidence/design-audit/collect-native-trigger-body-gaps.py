"""Custom trigger source references versus selected declarations, not native lookup."""
import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[5]
def decode(n):
 if n['kind']=='object':return {k:decode(v) for k,v in n['members'].items()}
 if n['kind']=='array':return [decode(v) for v in n['items']]
 if n['kind']=='number':return json.loads(n['value'])
 return n.get('value')
def names(v):return '.'.join(x['String']['sval'] for x in v)
receipt=json.loads((R/'docs/helix/04-build/evidence/design-audit/complete-feed-layout-profile-composition.json').read_text());b=(R/receipt['astPath']).read_bytes()
if hashlib.sha256(b).hexdigest()!=receipt['astSha256']:raise ValueError('stale selected AST')
a=json.loads(b);provided={names(n['stmt']['CreateFunctionStmt']['funcname']) for n in a if 'CreateFunctionStmt' in n['stmt']};refs=[];pins=[]
for file in ['row-home-triggers-v0.1.proposal.umf.json','edge-limit-triggers-v0.1.proposal.umf.json','feed-current-union-triggers-v0.1.proposal.umf.json']:
 path='docs/helix/02-design/contracts/'+file;data=(R/path).read_bytes();pins.append({'path':path,'sha256':hashlib.sha256(data).hexdigest()});d=json.loads(data)
 for i,n in enumerate(decode(d['modules'][0]['elements'][0]['extensions']['umf.postgresql']['root'])['stmts']):
  t=n['stmt'].get('CreateTrigStmt')
  if not t:raise ValueError('unexpected trigger source')
  refs.append({'source':path,'ordinal':i,'trigger':t['trigname'],'relation':t['relation'],'routine':names(t['funcname']),'bodyDeclaredInSelectedModel':names(t['funcname']) in provided,'requiredReturnType':'trigger','arguments':t.get('args',[])})
result={'scope':'Original custom trigger references only; no builtin type/operator/function resolver, native OID admission or body semantics','selectedAstPath':receipt['astPath'],'selectedAstSha256':receipt['astSha256'],'triggerSources':pins,'providedRoutineNames':sorted(provided),'references':refs,'missingBodyNames':sorted({r['routine'] for r in refs if not r['bodyDeclaredInSelectedModel']}),'nativeQualified':False}
(R/'docs/helix/04-build/evidence/design-audit/native-trigger-body-gaps.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'references':len(refs),'missingBodyNames':result['missingBodyNames'],'nativeQualified':False}))
