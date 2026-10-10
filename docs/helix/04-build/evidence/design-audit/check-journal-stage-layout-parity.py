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
r=json.loads(Path('docs/helix/04-build/evidence/design-audit/journal-stage-layout-model-source.json').read_text())
for item in r['inputs']+[{'path':r['modelPath'],'sha256':r['modelSha256']},{'path':r['exportPath'],'sha256':r['exportSha256']}]:
    require(hashlib.sha256(Path(item['path']).read_bytes()).hexdigest()==item['sha256'],'stale artifact')
b,bt=load(r['inputs'][0]['path']);p,pt=load(r['inputs'][1]['path']);s,st=load(r['inputs'][2]['path']);c,ct=load(r['modelPath'])
expected=copy.deepcopy(bt)
comments=[x['stmt']['CommentStmt'] for x in expected['stmts'] if x['stmt'].get('CommentStmt',{}).get('objtype')=='OBJECT_SCHEMA']
require(len(comments)==1 and comments[0]['comment']=='truss-layout complete-history REVIEW ONLY - unqualified','original marker')
comments[0]['comment']='truss-layout journal-stage REVIEW ONLY - unqualified'
expected['stmts']+=pt['stmts']+st['stmts']
def verify(tree):
    require(len(tree['stmts'])==43,'statement inventory')
    require(normalize(tree)==normalize(expected),'unexpected AST/order/content change')
    tables=[tree['stmts'][i]['stmt']['CreateStmt'] for i in (41,42)]
    require([t['relation']['relname'] for t in tables]==['row_home_operation','row_home_journal_stage'],'parent before child')
    require(all(t['relation']['schemaname']=='truss' for t in tables),'namespace')
    require([len([v for v in t['tableElts'] if 'ColumnDef' in v]) for t in tables]==[16,6],'complete column inventories')
verify(ct)
negative=[]
for name in ['reversed_parent_child','missing_parent','changed_stage_body_column']:
    bad=copy.deepcopy(ct)
    if name=='reversed_parent_child': bad['stmts'][41],bad['stmts'][42]=bad['stmts'][42],bad['stmts'][41]
    elif name=='missing_parent': del bad['stmts'][41]
    else:
        columns=bad['stmts'][42]['stmt']['CreateStmt']['tableElts']
        next(v['ColumnDef'] for v in columns if v.get('ColumnDef',{}).get('colname')=='body_bytes')['colname']='substituted_body'
    try: verify(bad)
    except ValueError: negative.append(name)
    else: raise ValueError('missed negative '+name)
require(c['modules'][0]['elements'][0]['extensions']['umf.postgresql']['source']==b['modules'][0]['elements'][0]['extensions']['umf.postgresql']['source'],'original archive changed')
print(json.dumps({'scope':'independent complete source AST composition parity, parent/child order and columns only; no native execution or installation','helperSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'candidateStatements':43,'parentColumns':16,'stageColumns':6,'onlyExpectedChanges':True,'negativeControls':negative,'nativeExecuted':False,'installationReady':False},indent=2))
