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
def load_source(stem):
    r=json.loads((evidence/(stem+'-source.json')).read_text());o=r['observations'][0]
    for f,h in [('path','sourceSha256'),('artifactPath','artifactSha256'),('exportPath','exportSha256')]:require(hashlib.sha256(Path(o[f]).read_bytes()).hexdigest()==o[h],'stale artifact')
    m=json.loads(Path(o['artifactPath']).read_text());tree=decode(m['modules'][0]['elements'][0]['extensions']['umf.postgresql']['root']);require(len(tree['stmts'])==1,'single update');return strip(tree['stmts'][0]['stmt']['UpdateStmt'])
original=load_source('row-operation-generation-reset');candidate=load_source('journal-stage-generation-reset')
def col(alias,name):return {'ColumnRef':{'fields':[{'String':{'sval':alias}},{'String':{'sval':name}}]}}
def expression(left,right,kind='AEXPR_OP'):return {'A_Expr':{'kind':kind,'name':[{'String':{'sval':'='}}],'lexpr':left,'rexpr':right}}
def text(value):return {'A_Const':{'sval':{'sval':value}}}
expected=copy.deepcopy(original);args=expected['whereClause']['BoolExpr']['args']
require(len(args)==7,'original exact predicates')
args[4]=expression(col('o','phase'),text('admitted'))
sub={'targetList':[{'ResTarget':{'val':{'A_Const':{'ival':{'ival':1}}}}}],'fromClause':[{'RangeVar':{'schemaname':'truss','relname':'row_home_journal_stage','inh':True,'relpersistence':'p','alias':{'aliasname':'s'}}}],'whereClause':{'BoolExpr':{'boolop':'AND_EXPR','args':[expression(col('s','original_writer_xid'),col('o','original_writer_xid')),expression(col('s','operation_ordinal'),col('o','operation_ordinal')),expression(col('s','stage_name'),{'List':{'items':[text(x) for x in ['final','reserved','publication']]}},'AEXPR_IN')]}},'limitOption':'LIMIT_OPTION_DEFAULT','op':'SETOP_NONE'}
args.append({'BoolExpr':{'boolop':'NOT_EXPR','args':[{'SubLink':{'subLinkType':'EXISTS_SUBLINK','subselect':{'SelectStmt':sub}}}]}})
def verify(value):require(value==expected,'unexpected reset/predicate/projection change')
verify(candidate);controls=[]
for name in ['missing_frozen_guard','wrong_stage_relation','missing_operation_association','allowed_ready_phase','changed_increment','missing_returned_field']:
    x=copy.deepcopy(candidate)
    if name=='missing_frozen_guard':x['whereClause']['BoolExpr']['args'].pop()
    elif name in ['wrong_stage_relation','missing_operation_association']:
        sub=x['whereClause']['BoolExpr']['args'][-1]['BoolExpr']['args'][0]['SubLink']['subselect']['SelectStmt']
        if name=='wrong_stage_relation':sub['fromClause'][0]['RangeVar']['relname']='journal'
        else:sub['whereClause']['BoolExpr']['args'].pop(1)
    elif name=='allowed_ready_phase':x['whereClause']['BoolExpr']['args'][4]=original['whereClause']['BoolExpr']['args'][4]
    elif name=='changed_increment':x['targetList'][0]['ResTarget']['val']={}
    else:x['returningList'].pop()
    try:verify(x)
    except ValueError:controls.append(name)
    else:raise ValueError('missed '+name)
print(json.dumps({'scope':'full original update AST plus independently authored admitted/frozen-prefix guards only; no native timing, visibility, authority or effect proof','helperSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'returnedFields':len(candidate['returningList']),'negativeControls':controls,'nativeExecuted':False},indent=2))
