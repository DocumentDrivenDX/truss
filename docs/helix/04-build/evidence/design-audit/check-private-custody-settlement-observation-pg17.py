"""Independent intended SELECT structure only; no native settlement proof."""
import copy,json,hashlib
from pathlib import Path
base=Path('docs/helix/04-build/evidence/design-audit')
def require(v,m):
    if not v:raise ValueError(m)
def decode(n):
    if n['kind']=='object':return {k:decode(v) for k,v in n['members'].items()}
    if n['kind']=='array':return [decode(v) for v in n['items']]
    if n['kind']=='number':return int(n['value'])
    if n['kind']=='null':return None
    return n['value']
def strip(n):
    if isinstance(n,dict):return {k:strip(v) for k,v in n.items() if k!='location'}
    if isinstance(n,list):return [strip(v) for v in n]
    return n
def name(x):return {'String':{'sval':x}}
def cast(arg,t):return {'TypeCast':{'arg':arg,'typeName':{'names':[name('pg_catalog'),name(t)],'typemod':-1}}}
xid=cast({'ParamRef':{'number':1}},'xid8')
expected={'targetList':[{'ResTarget':{'name':'original_writer_xid','val':cast(xid,'text')}},{'ResTarget':{'name':'transaction_status','val':cast({'FuncCall':{'funcname':[name('pg_catalog'),name('pg_xact_status')],'args':[xid],'funcformat':'COERCE_EXPLICIT_CALL'}},'text')}}],'limitOption':'LIMIT_OPTION_DEFAULT','op':'SETOP_NONE'}
r=json.loads((base/'private-custody-settlement-observation-pg17-source.json').read_text());o=r['observations'][0]
for f,h in [('path','sourceSha256'),('artifactPath','artifactSha256'),('exportPath','exportSha256')]:require(hashlib.sha256(Path(o[f]).read_bytes()).hexdigest()==o[h],'stale source/model/export')
m=json.loads(Path(o['artifactPath']).read_text());root=decode(m['modules'][0]['elements'][0]['extensions']['umf.postgresql']['root'])
require(len(root['stmts'])==1,'one statement');require(set(root['stmts'][0]['stmt'])=={'SelectStmt'},'SELECT only');actual=strip(root['stmts'][0]['stmt']['SelectStmt'])
def verify(v):require(v==expected,'intended full original SELECT mismatch')
verify(actual);controls=[]
for n in ['foreign_function','unqualified_function','foreign_parameter','wrong_native_type','missing_status','added_relation','added_limit']:
    v=copy.deepcopy(actual)
    fn=v['targetList'][1]['ResTarget']['val']['TypeCast']['arg']['FuncCall']
    if n=='foreign_function':fn['funcname'][1]=name('pg_current_xact_id')
    elif n=='unqualified_function':fn['funcname'].pop(0)
    elif n=='foreign_parameter':fn['args'][0]['TypeCast']['arg']['ParamRef']['number']=2
    elif n=='wrong_native_type':fn['args'][0]['TypeCast']['typeName']['names'][1]=name('int8')
    elif n=='missing_status':v['targetList'].pop()
    elif n=='added_relation':v['fromClause']=[{'RangeVar':{'relname':'journal'}}]
    else:v['limitCount']={}
    try:verify(v)
    except ValueError:controls.append(n)
    else:raise ValueError('missed corruption '+n)
print(json.dumps({'scope':'full independently constructed intended two-projection SELECT AST plus source/model/export hash consistency; no native function/descriptor/status/authority qualification','helperSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'sourceReceiptSha256':hashlib.sha256((base/'private-custody-settlement-observation-pg17-source.json').read_bytes()).hexdigest(),'negativeControls':controls,'nativeExecuted':False},indent=2))
