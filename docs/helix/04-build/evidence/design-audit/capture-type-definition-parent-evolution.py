"""Full parent source review candidate, not identity adoption or native migration."""
import hashlib,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[5]
B='docs/helix/04-build/evidence/design-audit/'
if len(sys.argv)>2:raise SystemExit('usage: capture-type-definition-parent-evolution.py [type_def|rel_def|module_access|schema_rev|journal|key_tombstone]')
table=sys.argv[1] if len(sys.argv)==2 else 'type_def'
if table not in ('type_def','rel_def','module_access','schema_rev','journal','key_tombstone'):raise ValueError('unreviewed parent selection')
identity='truss.layout.table.'+table
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
e=next(x for x in d['entries'] if x['authoredId']==identity)
m,mh=load(e['originalLocator']['modelPath'])
if mh!=e['originalLocator']['modelSha256']:raise ValueError('original model drift')
tagged=at(m,e['originalLocator']['jsonPointer'])
def decode(v):
 if v['kind']=='object':return {k:decode(x) for k,x in v['members'].items()}
 if v['kind']=='array':return [decode(x) for x in v['items']]
 return json.loads(v['value']) if v['kind']=='number' else v.get('value')
if decode(tagged)!=e['originalNativeDefinition']:raise ValueError('original decoded parent mismatch')
# Original diagnostic keeps decoded semantics; retain original tagged bytes too.
a,ah=load(B+'reference-history-layout-native-ast.json')
composition,cph=load(B+'reference-history-layout-model-source.json')
selected_model,smh=load(composition['modelPath'])
if smh!=composition['modelSha256']:raise ValueError('selected model source drift')
selected_tree=at(selected_model,'/modules/0/elements/0/extensions/umf.postgresql/root/members/stmts')
if decode(selected_tree)!=a:raise ValueError('selected AST/model semantic correspondence mismatch')
column_inventory,cih=load('docs/helix/02-design/contracts/weft-review-columns-v0.12.proposal.json')
if column_inventory['astPath']!=B+'reference-history-layout-native-ast.json' or column_inventory['astSha256']!=ah:raise ValueError('selected column inventory custody mismatch')
candidates=[(i,x['stmt']['CreateStmt']) for i,x in enumerate(a) if 'CreateStmt' in x['stmt'] and x['stmt']['CreateStmt']['relation'].get('schemaname')=='truss' and x['stmt']['CreateStmt']['relation']['relname']==table]
if len(candidates)!=1:raise ValueError('selected qualified parent count')
i,new=candidates[0];old=e['originalNativeDefinition']
def columns(v):return {x['ColumnDef']['colname']:x['ColumnDef'] for x in v['tableElts'] if 'ColumnDef' in x}
o,n=columns(old),columns(new)
rows=[{'name':name,'state':'added' if name not in o else 'removed' if name not in n else 'same_definition_except_parser_positions' if strip(o[name])==strip(n[name]) else 'definition_changed','original':o.get(name),'selected':n.get(name)} for name in sorted(set(o)|set(n))]
effects=[{'statementIndex':j,'kind':kind,'definition':v} for j,x in enumerate(a) for kind,v in x['stmt'].items() if isinstance(v,dict) and v.get('relation',{}).get('schemaname')=='truss' and v.get('relation',{}).get('relname')==table]
if table=='type_def' and [x['kind'] for x in effects]!=['CreateStmt','IndexStmt','AlterTableStmt']:raise ValueError('direct table effect inventory drift')
original_effect_ids=[];catalog_pins={}
for file in ['truss-layout-0.2.constraint-ids.draft.json','truss-layout-0.2.supporting-index-ids.draft.json']:
 path='docs/helix/02-design/models/'+file;catalog,ch=load(path);catalog_pins[path]=ch
 for item in catalog['entries']:
  if item.get('parentId')!=identity:continue
  loc=item['capturedModelLocator']
  if loc['modelSha256']!=mh or loc['modelPath']!=e['originalLocator']['modelPath']:raise ValueError('effect source custody mismatch')
  node=at(m,loc['jsonPointer'])
  if item['objectKind']=='constraint' and node!=item['originalNativeNode']:raise ValueError('original constraint mismatch')
  original_effect_ids.append(item)
if table=='type_def' and len(original_effect_ids)!=7:raise ValueError('original effect identity inventory drift')
out={'originalEffectIdentities':original_effect_ids,'originalEffectCatalogPins':catalog_pins,'scope':'explicit qualified '+table+' parent evolution review candidate; complete direct qualified relation CREATE/index/ALTER source effects, implicit/transitive/native dependencies remain open','selectedDirectEffects':effects,'authoredId':e['authoredId'],'originalLocator':e['originalLocator'],'selectedLocator':{'astPath':B+'reference-history-layout-native-ast.json','jsonPointer':'/'+str(i)+'/stmt/CreateStmt'},'sourcePins':{'diagnostic':dh,'originalModel':mh,'selectedAst':ah,'selectedModel':smh,'compositionReceipt':cph,'columnInventory':cih,'producer':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},'originalTaggedParent':tagged,'originalNativeParent':old,'selectedNativeParent':new,'columnComparisons':rows,'parentIdentityAdopted':False,'nativeQualified':False}
(R/(B+('type-definition' if table=='type_def' else table)+'-parent-evolution-review.json')).write_text(json.dumps(out,separators=(',',':'))+'\n')
print(json.dumps({'table':table,'directStatements':len(effects),'originalEffectIds':len(original_effect_ids),'columns':{x:sum(r['state']==x for r in rows) for x in sorted({r['state'] for r in rows})}}))
