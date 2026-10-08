"""Original parent-bounded constraint declarations; no effect identity or native adoption."""
from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parents[5]/'docs/helix'
base='04-build/evidence/design-audit/'
def decode(v):
 if v['kind']=='object':return {k:decode(x) for k,x in v['members'].items()}
 if v['kind']=='array':return [decode(x) for x in v['items']]
 return json.loads(v['value']) if v['kind']=='number' else v.get('value')
def strip(v):
 if isinstance(v,list):return [strip(x) for x in v]
 if isinstance(v,dict):return {k:strip(x) for k,x in v.items() if k not in ('location','stmt_location','stmt_len')}
 return v
def constraints(v,p='',column=None):
 if isinstance(v,list):
  for i,x in enumerate(v):yield from constraints(x,p+'/'+str(i),column)
 elif isinstance(v,dict):
  for k,x in v.items():
   if k=='Constraint':yield p+'/'+k,x,column
   else:yield from constraints(x,p+'/'+k,x.get('colname') if k=='ColumnDef' and isinstance(x,dict) else column)
rows=[];pins=[]
for name in ['type-definition','rel_def','module_access','schema_rev','journal','key_tombstone','object_key']:
 source=base+name+'-parent-evolution-review.json';raw=(root/source).read_bytes();review=json.loads(raw)
 pins.append({'path':source,'sha256':hashlib.sha256(raw).hexdigest()})
 selected=[]
 for effect in review['selectedDirectEffects']:
  for pointer,node,column in constraints(effect['definition']):
   selected.append({'statementIndex':effect['statementIndex'],'statementKind':effect['kind'],'definitionPointer':pointer,'declaringColumn':column,'definition':node})
 for original in review['originalEffectIdentities']:
  row={'originalParentId':review['authoredId'],'originalEffectId':original['entryId'],'objectKind':original['objectKind'],'originalLocator':original['capturedModelLocator'],'parentIdentityAdopted':False,'nativeQualified':False}
  if original['objectKind']=='constraint':
   node=decode(original['originalNativeNode']);original_context=[column for _,n,column in constraints(review['originalNativeParent']) if n==node]
   if len(original_context)!=1:raise ValueError('ambiguous original declaration context')
   column=original_context[0];candidates=[c for c in selected if c['definition'].get('contype')==node.get('contype')]
   row.update({'originalDefinition':node,'originalDeclaringColumn':column,'sameKindSelectedDeclarations':candidates,'equalNodeExceptPositions':[c['statementIndex'].__str__()+':'+c['definitionPointer'] for c in candidates if c['declaringColumn']==column and strip(c['definition'])==strip(node)],'interpretation':'Node equality is source comparison only; parent, column/context, referenced owner/operator/type/collation and transitive native correspondence remain required.'})
  else:row.update({'creatingConstraintId':original['creatingConstraintId'],'interpretation':'Original creator provenance only. No observed supporting-index definition or target identity is inferred from constraint equality.'})
  rows.append(row)
if len({r['originalEffectId'] for r in rows})!=len(rows):raise ValueError('duplicate original effects')
result={'scope':__doc__,'sourcePins':pins,'rows':rows,'nativeQualified':False,'installerReady':False,'comparisonRule':'Only original selected parent direct CREATE/ALTER source constraints; preserve names and all declaration content, strip parser positions only. Split object_key targets are explicitly distinct parents, never identity matches.'}
(root/(base+'parent-constraint-source-comparisons.json')).write_text(json.dumps(result,indent=2)+'\n')
print('Original constraints and creator-index provenance compared for seven reviewed parent units; no identities adopted.')
