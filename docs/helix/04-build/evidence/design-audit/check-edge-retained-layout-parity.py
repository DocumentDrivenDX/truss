"""Independent source-tree correspondence; no native catalog/behavior qualification."""
import copy,hashlib,json
from pathlib import Path

def require(ok,message):
    if not ok: raise ValueError(message)
def plain(n):
    k=n['kind']
    if k=='object': return {key:plain(value) for key,value in n['members'].items()}
    if k=='array': return [plain(v) for v in n['items']]
    if k=='number': return int(n['value'])
    if k=='null': return None
    return n['value']
def load(path):
    m=json.loads(Path(path).read_text())
    return m,plain(m['modules'][0]['elements'][0]['extensions']['umf.postgresql']['root'])
def without_offsets(x):
    if isinstance(x,dict): return {k:without_offsets(v) for k,v in x.items() if k not in ('location','stmt_location','stmt_len')}
    if isinstance(x,list): return [without_offsets(v) for v in x]
    return x
receipt_path=Path('docs/helix/04-build/evidence/design-audit/edge-retained-layout-model-source.json')
r=json.loads(receipt_path.read_text())
for item in r['inputs']+[{'path':r['modelPath'],'sha256':r['modelSha256']},{'path':r['exportPath'],'sha256':r['exportSha256']}]:
    require(hashlib.sha256(Path(item['path']).read_bytes()).hexdigest()==item['sha256'],'stale evidence '+item['path'])
b,bt=load(r['inputs'][0]['path']);f,ft=load(r['inputs'][1]['path']);c,ct=load(r['modelPath'])
expected=copy.deepcopy(bt)
comments=[x['stmt']['CommentStmt'] for x in expected['stmts'] if 'CommentStmt' in x['stmt'] and x['stmt']['CommentStmt']['objtype']=='OBJECT_SCHEMA']
require(len(comments)==1 and comments[0]['comment']=='truss-layout 0.2','original marker')
comments[0]['comment']='truss-layout edge-retained REVIEW ONLY - unqualified'
expected['stmts']+=ft['stmts']
require(without_offsets(ct)==without_offsets(expected),'unexpected candidate changes')
require(len(bt['stmts'])==35 and len(ft['stmts'])==2 and len(ct['stmts'])==37,'statement count')
for statement in ft['stmts']:
    table=statement['stmt']['AlterTableStmt']
    require(table['relation']['schemaname']=='truss' and table['relation']['relname']=='edge' and len(table['cmds'])==1,'alter target')
column=ft['stmts'][0]['stmt']['AlterTableStmt']['cmds'][0]['AlterTableCmd']
require(column['subtype']=='AT_AddColumn','column action')
definition=column['def']['ColumnDef']
require(definition['colname']=='retained' and [x['String']['sval'] for x in definition['typeName']['names']]==['pg_catalog','jsonb'],'column name/type')
require(not any(k in definition for k in ['constraints','raw_default','cooked_default','identity','generated']),'unexpected column default/constraint')
constraint=ft['stmts'][1]['stmt']['AlterTableStmt']['cmds'][0]['AlterTableCmd']
require(constraint['subtype']=='AT_AddConstraint','constraint action')
d=constraint['def']['Constraint']
require(d['contype']=='CONSTR_CHECK' and d['conname']=='edge_retained_is_object' and d['initially_valid'] is True,'constraint definition')
require(c['modules'][0]['elements'][0]['extensions']['umf.postgresql']['source']==b['modules'][0]['elements'][0]['extensions']['umf.postgresql']['source'],'original archive preservation')
print(json.dumps({'scope':'source AST correspondence and explicit selected column/constraint shape only','baselineStatements':35,'candidateStatements':37,'originalArchivePreserved':True,'onlyExpectedAstChanges':True,'nativeExecuted':False,'installationReady':False},indent=2))
