"""Exact original DELETE/SELECT AST parity, not authority or execution proof."""
import copy,json,hashlib
from pathlib import Path
base=Path('docs/helix/02-design/contracts');evidence=Path('docs/helix/04-build/evidence/design-audit')
def require(value,message):
    if not value:raise ValueError(message)
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
r=json.loads((evidence/'journal-stage-cleanup-absence-source.json').read_text());o=r['observations'][0]
for field,h in [('path','sourceSha256'),('artifactPath','artifactSha256'),('exportPath','exportSha256')]:
    require(hashlib.sha256(Path(o[field]).read_bytes()).hexdigest()==o[h],'stale original artifact')
m=json.loads(Path(o['artifactPath']).read_text());tree=decode(m['modules'][0]['elements'][0]['extensions']['umf.postgresql']['root'])
require(len(tree['stmts'])==1,'exact statement count');s=tree['stmts'][0]['stmt']['SelectStmt']
def verify(candidate):
    require(set(candidate)=={'targetList','fromClause','whereClause','limitOption','op'},'unexpected select clauses')
    require(candidate['limitOption']=='LIMIT_OPTION_DEFAULT' and candidate['op']=='SETOP_NONE','limit/set operation')
    require(len(candidate['fromClause'])==1 and set(candidate['fromClause'][0])=={'RangeVar'},'parent-independent source')
    rel=candidate['fromClause'][0]['RangeVar'];require(rel['schemaname']=='truss' and rel['relname']=='row_home_journal_stage' and rel['alias']['aliasname']=='s','exact child source')
    names=[x['ResTarget']['name'] for x in candidate['targetList']]
    require(names==['original_writer_xid','operation_ordinal','stage_name','stage_ordinal','effect_generation','body_bytes_hex'],'complete ordered fields')
    require(strip(candidate['targetList'])==strip(s['targetList']),'original expressions')
    w=candidate['whereClause']['BoolExpr'];require(w['boolop']=='AND_EXPR' and len(w['args'])==2,'exact two-term cohort')
    for term,column,param,typename in zip(w['args'],['original_writer_xid','operation_ordinal'],[1,2],['xid8','int8']):
        e=term['A_Expr'];require(e['kind']=='AEXPR_OP' and e['name']==[{'String':{'sval':'='}}],'exact equality')
        require(e['lexpr']['ColumnRef']['fields']==[{'String':{'sval':'s'}},{'String':{'sval':column}}],'original typed address')
        cast=e['rexpr']['TypeCast'];require(cast['arg']['ParamRef']['number']==param and cast['typeName']['names']==[{'String':{'sval':'pg_catalog'}},{'String':{'sval':typename}}],'exact typed binding')
verify(s);controls=[]
for name in ['wrong_child','added_parent_join','missing_ordinal','wrong_operator','reversed_binding','missing_body','limit']:
    x=copy.deepcopy(s)
    if name=='wrong_child':x['fromClause'][0]['RangeVar']['relname']='journal'
    elif name=='added_parent_join':x['fromClause'].append(copy.deepcopy(x['fromClause'][0]))
    elif name=='missing_ordinal':x['whereClause']['BoolExpr']['args'].pop()
    elif name=='wrong_operator':x['whereClause']['BoolExpr']['args'][0]['A_Expr']['name'][0]['String']['sval']='>'
    elif name=='reversed_binding':x['whereClause']['BoolExpr']['args'][0]['A_Expr']['rexpr']['TypeCast']['arg']['ParamRef']['number']=2
    elif name=='missing_body':x['targetList'].pop()
    else:x['limitCount']={}
    try:verify(x)
    except ValueError:controls.append(name)
    else:raise ValueError('missed '+name)
print(json.dumps({'scope':'independent exact child source/address binding, clause and full original projection expectations only; no native absence proof','helperSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'sourceReceiptSha256':hashlib.sha256((evidence/'journal-stage-cleanup-absence-source.json').read_bytes()).hexdigest(),'negativeControls':controls,'nativeExecuted':False},indent=2))
