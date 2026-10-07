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
inputs=['docs/helix/02-design/contracts/row-home-operation-v0.1.proposal.umf.json','docs/helix/02-design/contracts/row-home-journal-stage-v0.2.proposal.umf.json']
entries=[]
for path in inputs:
    model,tree=load(path)
    require(len(tree['stmts'])==1,'one original declaration required')
    table=tree['stmts'][0]['stmt']['CreateStmt'];name=table['relation']['relname'];qualified='truss.'+name
    require(table['relation']['schemaname']=='truss','namespace')
    entries.append({'id':qualified,'kind':'table','source':path,'pointer':'/stmts/0/stmt/CreateStmt','nativeStatus':'unresolved'})
    for index,node in enumerate(table['tableElts']):
        pointer='/stmts/0/stmt/CreateStmt/tableElts/'+str(index)
        if 'ColumnDef' in node:
            column=node['ColumnDef'];entry={'id':qualified+'.'+column['colname'],'kind':'column','parent':qualified,'source':path,'pointer':pointer+'/ColumnDef','originalDeclaration':normalize(column),'nativeStatus':'unresolved'}
        else:
            require('Constraint' in node,'unclassified declaration')
            constraint=node['Constraint'];entry={'id':qualified+'.'+constraint['conname'],'kind':'constraint','parent':qualified,'source':path,'pointer':pointer+'/Constraint','originalDeclaration':normalize(constraint),'nativeStatus':'unresolved'}
        entries.append(entry)
constraints=[e for e in entries if e['kind']=='constraint']
fks=[e for e in constraints if e['originalDeclaration']['contype']=='CONSTR_FOREIGN']
require(len(fks)==1,'exact stage FK inventory')
fk=fks[0]['originalDeclaration']
require(fk['pktable']['schemaname']=='truss' and fk['pktable']['relname']=='row_home_operation','FK original parent')
require(fk['fk_del_action']=='r','restrict delete')
print(json.dumps({'scope':'exact explicit parent/stage source declaration inventory only; not complete implicit/native dependency inventory','helperSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'inputs':[{'path':p,'sha256':hashlib.sha256(Path(p).read_bytes()).hexdigest()} for p in inputs],'entries':entries,'explicitEntryCount':len(entries),'dependencyEdges':[{'from':'truss.row_home_journal_stage','to':'truss.row_home_operation','kind':'foreign-key','constraint':fks[0]['id']}],'unresolvedNativeSurfaces':['PK supporting indexes and index definitions','FK enforcement triggers and dependency identities','native type/collation/operator/function resolution','namespace/object ownership and effective grants/policies','protected producer/observer/recovery/retention routines and accounts','complete retained conversion and installation effects'],'nativeExecuted':False,'installationReady':False},indent=2))
