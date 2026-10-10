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
receipt=json.loads((evidence/'journal-stage-cleanup-source.json').read_text())
statements=[]
for o in receipt['observations']:
    for field,h in [('path','sourceSha256'),('artifactPath','artifactSha256'),('exportPath','exportSha256')]:
        require(hashlib.sha256(Path(o[field]).read_bytes()).hexdigest()==o[h],'stale source artifact')
    m=json.loads(Path(o['artifactPath']).read_text());root=decode(m['modules'][0]['elements'][0]['extensions']['umf.postgresql']['root'])
    require(len(root['stmts'])==1,'original single statement')
    statements.append(root['stmts'][0]['stmt'])
s=statements[0]['SelectStmt'];join=s['fromClause'][0]['JoinExpr']
require(join['jointype']=='JOIN_INNER','original inner parent association')
require([t['RangeVar']['relname'] for t in [join['larg'],join['rarg']]]==['row_home_journal_stage','row_home_operation'],'original stage/parent sources')
require([v['ResTarget']['name'] for v in s['targetList']]==['original_writer_xid','operation_ordinal','stage_name','stage_ordinal','effect_generation','body_bytes_hex'],'complete snapshot order')
require(len(join['quals']['BoolExpr']['args'])==5,'complete original association/context predicates')
def verify(candidate):
    require(set(candidate)=={'DeleteStmt'},'delete kind')
    d=candidate['DeleteStmt']
    require(set(d)=={'relation','usingClause','whereClause','returningList'},'delete modifiers')
    require(strip(d['relation'])==strip(join['larg']['RangeVar']),'exact stage target')
    require(strip(d['usingClause'])==strip([join['rarg']]),'exact original parent')
    require(strip(d['whereClause'])==strip(join['quals']),'complete original cohort predicate')
    require(strip(d['returningList'])==strip(s['targetList']),'complete exact returned snapshot')
verify(statements[1]);controls=[]
for name in ['wrong_stage','wrong_parent','missing_context','missing_body','reordered_fields','extra_modifier']:
    x=copy.deepcopy(statements[1]);d=x['DeleteStmt']
    if name=='wrong_stage':d['relation']['relname']='journal'
    elif name=='wrong_parent':d['usingClause'][0]['RangeVar']['relname']='another_operation'
    elif name=='missing_context':d['whereClause']['BoolExpr']['args'].pop()
    elif name=='missing_body':d['returningList'].pop()
    elif name=='reordered_fields':d['returningList'].reverse()
    else:d['withClause']={}
    try:verify(x)
    except ValueError:controls.append(name)
    else:raise ValueError('accepted '+name)
print(json.dumps({'scope':'original source/model/export hashes and full SELECT/DELETE stage/parent/cohort/projection AST parity ignoring locations only; no native eligibility, containment, settlement or execution','helperSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'sourceReceiptSha256':hashlib.sha256((evidence/'journal-stage-cleanup-source.json').read_bytes()).hexdigest(),'statementPairs':1,'returnedFields':6,'negativeControls':controls,'nativeExecuted':False},indent=2))
