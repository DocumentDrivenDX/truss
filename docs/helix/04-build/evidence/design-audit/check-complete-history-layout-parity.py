"""Source AST correspondence only; no native CHECK, privilege or producer evidence."""
import copy,hashlib,json
from pathlib import Path

def require(ok,message):
    if not ok: raise ValueError(message)
def plain(n):
    if n['kind']=='object': return {k:plain(v) for k,v in n['members'].items()}
    if n['kind']=='array': return [plain(v) for v in n['items']]
    if n['kind']=='number': return int(n['value'])
    return n.get('value')
def load(path):
    m=json.loads(Path(path).read_text())
    return m,plain(m['modules'][0]['elements'][0]['extensions']['umf.postgresql']['root'])
def normalize(x):
    if isinstance(x,dict): return {k:normalize(v) for k,v in x.items() if k not in ('location','stmt_location','stmt_len')}
    if isinstance(x,list): return [normalize(v) for v in x]
    return x
def find(x,key):
    if isinstance(x,dict):
        for k,v in x.items():
            if k==key: yield v
            yield from find(v,key)
    elif isinstance(x,list):
        for v in x: yield from find(v,key)
r=json.loads(Path('docs/helix/04-build/evidence/design-audit/complete-history-layout-model-source.json').read_text())
for item in r['inputs']+[{'path':r['modelPath'],'sha256':r['modelSha256']},{'path':r['exportPath'],'sha256':r['exportSha256']}]:
    require(hashlib.sha256(Path(item['path']).read_bytes()).hexdigest()==item['sha256'],'stale original artifact')
b,bt=load(r['inputs'][0]['path']);f,ft=load(r['inputs'][1]['path']);c,ct=load(r['modelPath'])
expected=copy.deepcopy(bt)
comments=[s['stmt']['CommentStmt'] for s in expected['stmts'] if s['stmt'].get('CommentStmt',{}).get('objtype')=='OBJECT_SCHEMA']
require(len(comments)==1 and comments[0]['comment']=='truss-layout edge-retained REVIEW ONLY - unqualified','original review marker')
comments[0]['comment']='truss-layout complete-history REVIEW ONLY - unqualified'
journals=[s['stmt']['CreateStmt'] for s in expected['stmts'] if s['stmt'].get('CreateStmt',{}).get('relation',{}).get('relname')=='journal']
require(len(journals)==1,'journal inventory')
ops=[e['ColumnDef'] for e in journals[0]['tableElts'] if e.get('ColumnDef',{}).get('colname')=='op']
require(len(ops)==1,'op column inventory')
checks=[v['Constraint'] for v in ops[0]['constraints'] if v['Constraint']['contype']=='CONSTR_CHECK']
require(len(checks)==1,'original op check')
items=checks[0]['raw_expr']['A_Expr']['rexpr']['List']['items']
require([v['A_Const']['sval']['sval'] for v in items]==['create','update','delete','retain','rebind','transform'],'original op members')
new=copy.deepcopy(items[-1]);new['A_Const']['sval']['sval']='metadata';items.append(new)
expected['stmts']+=ft['stmts']
require(len(bt['stmts'])==37 and len(ft['stmts'])==4 and len(ct['stmts'])==41,'statement counts')
require(normalize(expected)==normalize(ct),'unintended candidate changes')
names=[]
for index,s in enumerate(ft['stmts']):
    table=s['stmt']['AlterTableStmt']
    require(table['relation']['schemaname']=='truss' and table['relation']['relname']=='journal' and len(table['cmds'])==1,'constraint target')
    cmd=table['cmds'][0]['AlterTableCmd'];d=cmd['def']['Constraint']
    require(cmd['subtype']=='AT_AddConstraint' and d['contype']=='CONSTR_CHECK' and d['initially_valid'] is True,'constraint action')
    names.append(d['conname'])
    if index<3: require(any(v['booltesttype']=='IS_TRUE' for v in find(d['raw_expr'],'BooleanTest')),'missing NULL-safe true guard')
require(names==['journal_complete_payload','journal_complete_origin','journal_complete_property_mapping','journal_complete_positive_identity'],'complete added constraint inventory')
require(c['modules'][0]['elements'][0]['extensions']['umf.postgresql']['source']==b['modules'][0]['elements'][0]['extensions']['umf.postgresql']['source'],'original archive changed')
print(json.dumps({'scope':'full source AST correspondence and coarse constraint inventory/NULL-safe syntax only','helperSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'originalStatements':37,'candidateStatements':41,'addedConstraintNames':names,'onlyExpectedChanges':True,'nativeExecuted':False,'installationReady':False},indent=2))
