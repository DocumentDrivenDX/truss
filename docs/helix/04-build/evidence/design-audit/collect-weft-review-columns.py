"""Selected authored declaration effects only; never a PostgreSQL resolver."""
import json,hashlib,sys
from pathlib import Path
R=Path(__file__).resolve().parents[5]
migration_profile='--migration-homes' in sys.argv
lifecycle_profile='--key-lifecycle' in sys.argv or migration_profile
operation_profile='--operation-uniqueness' in sys.argv or lifecycle_profile
recovery_profile='--feed-recovery' in sys.argv or operation_profile
feed_profile='--complete-feed' in sys.argv or recovery_profile
metadata_profile='--installation-metadata' in sys.argv
key_profile='--key-profile' in sys.argv
version='0.10' if migration_profile else '0.9' if lifecycle_profile else '0.8' if operation_profile else '0.7' if recovery_profile else '0.6' if feed_profile else '0.5' if metadata_profile else '0.4' if key_profile else '0.3'
receipt_name='migration-homes-layout-profile-composition.json' if migration_profile else 'key-lifecycle-layout-profile-composition.json' if lifecycle_profile else 'operation-uniqueness-layout-profile-composition.json' if operation_profile else 'feed-recovery-layout-profile-composition.json' if recovery_profile else 'complete-feed-layout-profile-composition.json' if feed_profile else 'installation-metadata-profile-composition.json' if metadata_profile else 'weft-key-profile-composition.json' if key_profile else 'weft-review-layout-composition.json'
receipt=json.loads((R/'docs/helix/04-build/evidence/design-audit'/receipt_name).read_text())
b=(R/receipt['astPath']).read_bytes()
if hashlib.sha256(b).hexdigest()!=receipt['astSha256']:raise ValueError('stale AST')
a=json.loads(b);tables={};indexes=[];other=[]
def column(c,ptr):return {'name':c['colname'],'definitionPointer':ptr,'declaredType':c['typeName'],'collation':c.get('collClause'),'constraints':c.get('constraints',[])}
for i,n in enumerate(a):
 s=n['stmt'];ptr=f'/{i}/stmt'
 if 'CreateStmt' in s:
  t=s['CreateStmt'];name=t['relation']['relname']
  if name in tables:raise ValueError('duplicate table')
  tables[name]={'name':name,'createPointer':ptr+'/CreateStmt','columns':[],'constraints':[]}
  for j,e in enumerate(t['tableElts']):
   p=ptr+f'/CreateStmt/tableElts/{j}'
   if 'ColumnDef' in e:tables[name]['columns'].append(column(e['ColumnDef'],p+'/ColumnDef'))
   elif 'Constraint' in e:tables[name]['constraints'].append({'pointer':p+'/Constraint','definition':e['Constraint']})
   else:raise ValueError('unclassified table element')
 elif 'AlterTableStmt' in s:
  t=s['AlterTableStmt'];name=t['relation']['relname']
  if name not in tables:raise ValueError('foreign ALTER target')
  for j,cmd in enumerate(t['cmds']):
   c=cmd['AlterTableCmd'];p=ptr+f'/AlterTableStmt/cmds/{j}/AlterTableCmd'
   if c['subtype']=='AT_AddColumn':
    col=column(c['def']['ColumnDef'],p+'/def/ColumnDef')
    if any(x['name']==col['name'] for x in tables[name]['columns']):raise ValueError('duplicate added column')
    tables[name]['columns'].append(col)
   elif c['subtype']=='AT_AddConstraint':tables[name]['constraints'].append({'pointer':p+'/def/Constraint','definition':c['def']['Constraint']})
   elif c['subtype']=='AT_AlterColumnType':
    matches=[x for x in tables[name]['columns'] if x['name']==c['name']]
    if len(matches)!=1:raise ValueError('ambiguous column alteration')
    col=matches[0];definition=c['def']['ColumnDef'];col['typeAlterationPointer']=p+'/def/ColumnDef';col['declaredType']=definition['typeName'];col['collation']=definition.get('collClause')
   else:raise ValueError('unclassified ALTER effect')
 elif 'IndexStmt' in s:indexes.append({'pointer':ptr+'/IndexStmt','definition':s['IndexStmt']})
 else:other.append({'pointer':ptr,'statementKind':list(s)})
result={'interfaceVersion':f'truss-weft-review-columns/{version}.0-proposal','scope':'Ordered explicit CREATE/ALTER column and constraint effects in the selected review AST; other statements retained by pointer; no native type/dependency resolution or implicit effect completeness','astPath':receipt['astPath'],'astSha256':receipt['astSha256'],'nativeQualified':False,'tables':list(tables.values()),'indexes':indexes,'otherStatements':other}
base=R/'docs/helix/02-design/contracts';(base/f'weft-review-columns-v{version}.proposal.json').write_text(json.dumps(result,indent=2)+'\n')
lines=[f'# Selected review layout columns ({version} proposal)','','Companion to [CONTRACT-012](CONTRACT-012-weft-storage-handoff.md).',f'This is the selected {len(a)}-statement review composition, including explicit ADD COLUMN and column-type changes.','Baseline 0.2 remains a separate profile. Native installation and compiler binding adoption remain unqualified.','Nullability reports explicit NOT NULL/PRIMARY KEY effects only; CHECK expressions and protected guards may reject NULL independently.',
f'The [source-effect inventory](weft-review-columns-v{version}.proposal.json) pins the complete native AST and original definition pointers.','','| Table | Columns |','| --- | --- |']
for name,t in tables.items():lines.append(f'| `{name}` | {len(t["columns"])} |')
feed_lines=[f'# Feed and lifecycle columns ({version} proposal)','',f'Companion to [full column index](weft-review-columns-v{version}.proposal.md).','']
if feed_profile:lines.extend(['',f'Complete-feed table column definitions are in the [feed chapter](weft-review-columns-v{version}.feed.proposal.md).'])
for name,t in tables.items():
 target=feed_lines if feed_profile and (name.startswith('feed_') and name!='feed_consumer' or name.startswith('complete_feed_') or name in ('key_lifecycle_history','installation_admission','key_migration_receipt')) else lines
 target.extend(['',f'## {name}','','| Column | Declared native type | SQL NULL allowed by declaration |','| --- | --- | --- |'])
 pk={k['String']['sval'] for c in t['constraints'] if c['definition']['contype']=='CONSTR_PRIMARY' for k in c['definition']['keys']}
 for c in t['columns']:
  typ='.'.join(n['String']['sval'] for n in c['declaredType']['names'])
  if c['declaredType'].get('arrayBounds'):typ+='[]'
  if c['declaredType'].get('typmods'):typ+=' (see original modifiers)'
  cons=[x['Constraint'] for x in c['constraints']]
  nn=c['name'] in pk or any(x['contype'] in ('CONSTR_PRIMARY','CONSTR_NOTNULL') for x in cons)
  target.append(f'| `{c["name"]}` | `{typ}` | {"no" if nn else "yes"} |')
if feed_profile:(base/f'weft-review-columns-v{version}.feed.proposal.md').write_text('\n'.join(feed_lines)+'\n')
if len(lines)>=500:raise ValueError('reference exceeds single-edit size')
(base/f'weft-review-columns-v{version}.proposal.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({'tables':len(tables),'columns':sum(len(t['columns']) for t in tables.values()),'explicitIndexes':len(indexes),'markdownLines':len(lines),'nativeQualified':False}))
