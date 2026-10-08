"""Full parent source review candidate, not identity adoption or native migration."""
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[5]
B='docs/helix/04-build/evidence/design-audit/'
def load(p):
 raw=(R/p).read_bytes();return json.loads(raw),hashlib.sha256(raw).hexdigest()
def strip(v):
 if isinstance(v,list):return [strip(x) for x in v]
 if isinstance(v,dict):return {k:strip(x) for k,x in v.items() if k not in ('location','stmt_location','stmt_len')}
 return v
def at(v,p):
 for k in p.split('/')[1:]:v=v[int(k)] if isinstance(v,list) else v[k.replace('~1','/').replace('~0','~')]
 return v
d,dh=load(B+'review011-unmatched-identity-diagnostics.json')
e=next(x for x in d['entries'] if x['authoredId']=='truss.layout.table.type_def')
m,mh=load(e['originalLocator']['modelPath'])
if mh!=e['originalLocator']['modelSha256']:raise ValueError('original model drift')
tagged=at(m,e['originalLocator']['jsonPointer'])
# Original diagnostic keeps decoded semantics; retain original tagged bytes too.
a,ah=load(B+'reference-history-layout-native-ast.json')
candidates=[(i,x['stmt']['CreateStmt']) for i,x in enumerate(a) if 'CreateStmt' in x['stmt'] and x['stmt']['CreateStmt']['relation'].get('schemaname')=='truss' and x['stmt']['CreateStmt']['relation']['relname']=='type_def']
if len(candidates)!=1:raise ValueError('selected qualified parent count')
i,new=candidates[0];old=e['originalNativeDefinition']
def columns(v):return {x['ColumnDef']['colname']:x['ColumnDef'] for x in v['tableElts'] if 'ColumnDef' in x}
o,n=columns(old),columns(new)
rows=[{'name':name,'state':'added' if name not in o else 'removed' if name not in n else 'same_definition_except_parser_positions' if strip(o[name])==strip(n[name]) else 'definition_changed','original':o.get(name),'selected':n.get(name)} for name in sorted(set(o)|set(n))]
effects=[{'statementIndex':j,'kind':kind,'definition':v} for j,x in enumerate(a) for kind,v in x['stmt'].items() if isinstance(v,dict) and v.get('relation',{}).get('schemaname')=='truss' and v.get('relation',{}).get('relname')=='type_def']
if [x['kind'] for x in effects]!=['CreateStmt','IndexStmt','AlterTableStmt']:raise ValueError('direct table effect inventory drift')
out={'scope':'explicit qualified type_def parent evolution review candidate; complete direct qualified relation CREATE/index/ALTER source effects, implicit/transitive/native dependencies remain open','selectedDirectEffects':effects,'authoredId':e['authoredId'],'originalLocator':e['originalLocator'],'selectedLocator':{'astPath':B+'reference-history-layout-native-ast.json','jsonPointer':'/'+str(i)+'/stmt/CreateStmt'},'sourcePins':{'diagnostic':dh,'originalModel':mh,'selectedAst':ah,'producer':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},'originalTaggedParent':tagged,'originalNativeParent':old,'selectedNativeParent':new,'columnComparisons':rows,'parentIdentityAdopted':False,'nativeQualified':False}
(R/(B+'type-definition-parent-evolution-review.json')).write_text(json.dumps(out,separators=(',',':'))+'\n')
print(json.dumps({x:sum(r['state']==x for r in rows) for x in sorted({r['state'] for r in rows})}))
