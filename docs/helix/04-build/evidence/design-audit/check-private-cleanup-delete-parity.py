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
def load(stem):
    receipt=json.loads((evidence/(stem+'-source.json')).read_text());o=receipt['observations'][0]
    for field,hashfield in [('path','sourceSha256'),('artifactPath','artifactSha256'),('exportPath','exportSha256')]:
        require(hashlib.sha256(Path(o[field]).read_bytes()).hexdigest()==o[hashfield],'original '+field+' hash')
    model=json.loads(Path(o['artifactPath']).read_text());root=decode(model['modules'][0]['elements'][0]['extensions']['umf.postgresql']['root'])
    require(len(root['stmts'])==2,'original two-statement membership')
    return [s['stmt'] for s in root['stmts']],o
selected,sp=load('private-custody-cleanup-selected-row-observation');deleted,dp=load('private-custody-cleanup-delete')
def verify(candidate):
    require(len(candidate)==2,'deletion membership')
    for observed,expected in zip(candidate,selected):
        require(set(observed)=={'DeleteStmt'} and set(expected)=={'SelectStmt'},'original statement kinds')
        d=observed['DeleteStmt'];s=expected['SelectStmt']
        require(set(d)=={'relation','whereClause','returningList'},'unexpected deletion modifier')
        require(strip(d['relation'])==strip(s['fromClause'][0]['RangeVar']),'original native relation')
        require(strip(d['whereClause'])==strip(s['whereClause']),'exact identity predicate')
        require(strip(d['returningList'])==strip(s['targetList']),'complete removed field projection')
verify(deleted)
controls=[]
for name,mutate in [('wrong relation',lambda x:x[0]['DeleteStmt']['relation'].update(relname='row_home_touch')),
 ('lost predicate',lambda x:x[0]['DeleteStmt'].pop('whereClause')),
 ('missing returned field',lambda x:x[0]['DeleteStmt']['returningList'].pop()),
 ('reordered fields',lambda x:x[0]['DeleteStmt']['returningList'].reverse()),
 ('extra modifier',lambda x:x[0]['DeleteStmt'].update(usingClause=[]))]:
    x=copy.deepcopy(deleted);mutate(x)
    try:verify(x)
    except ValueError:controls.append({'name':name,'expectedRefusal':True})
    else:raise ValueError('accepted corruption '+name)
receipt={'scope':'Original source/archive/export hashes and full native AST relation, identity predicate and RETURNING/SELECT projection parity after removing parser locations only. No native binding/authority, containment, settlement, deletion execution, capacity or atomicity qualification.','originalObservation':sp,'originalDeletion':dp,'statementPairs':2,'returnedFields':[16,12],'expectedRefusals':controls}
(evidence/'private-cleanup-delete-parity.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'statementPairs':2,'expectedRefusals':len(controls),'nativeExecution':False}))
