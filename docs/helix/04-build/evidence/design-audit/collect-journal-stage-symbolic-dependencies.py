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
paths=['docs/helix/02-design/contracts/row-home-operation-v0.1.proposal.umf.json','docs/helix/02-design/contracts/row-home-journal-stage-v0.2.proposal.umf.json']
references=[]
def names(nodes):return [n['String']['sval'] for n in nodes]
def walk(node,path,source):
    if isinstance(node,dict):
        for key,value in node.items():
            pointer=path+'/'+key
            if key in ('TypeName','typeName'):references.append({'kind':'type-name','source':source,'pointer':pointer,'nameParts':names(value['names']),'nativeResolution':'unresolved'})
            if key=='FuncCall':references.append({'kind':'function-call','source':source,'pointer':pointer,'nameParts':names(value['funcname']),'argumentCount':len(value.get('args',[])),'nativeResolution':'unresolved'})
            if key in ('CollateClause','collClause'):references.append({'kind':'collation-name','source':source,'pointer':pointer,'nameParts':names(value['collname']),'nativeResolution':'unresolved'})
            if key=='A_Expr':references.append({'kind':'operator-expression','source':source,'pointer':pointer,'nameParts':names(value.get('name',[])),'expressionKind':value['kind'],'originalExpression':normalize(value),'nativeResolution':'unresolved'})
            walk(value,pointer,source)
    elif isinstance(node,list):
        for i,value in enumerate(node):walk(value,path+'/'+str(i),source)
for path in paths:
    _,tree=load(path);walk(tree,'',path)
require(len([r for r in references if r['kind']=='type-name'])==22,'one original type occurrence per column')
require(len({(r['source'],r['pointer']) for r in references})==len(references),'duplicate source occurrence')
print(json.dumps({'scope':'explicit syntactic type/collation/function/operator occurrences only; not overload/type/operator/dependency resolution or native completeness','helperSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'inputs':[{'path':p,'sha256':hashlib.sha256(Path(p).read_bytes()).hexdigest()} for p in paths],'references':references,'occurrenceCount':len(references),'unresolvedAdditionalSurfaces':['native operator overload and coercion dependencies from every original expression','native type/collation/function object identity and overload/privilege correspondence','PK index/access-method/operator-class dependencies','FK internal enforcement triggers and original parent-key correspondence','routine/role/account/grant and complete installation dependency closure'],'nativeExecuted':False},indent=2))
