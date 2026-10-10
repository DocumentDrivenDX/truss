"""Independent exact predicate/order source oracle; no native proof."""
import copy,json,hashlib
from pathlib import Path
root=Path('docs/helix/02-design/contracts')
def require(ok,msg):
 if not ok:raise ValueError(msg)
def strings(n):return tuple(x['members']['String']['members']['sval']['value'] for x in n['items'])
def expr(n):
 require(len(n['members'])==1,'one expression kind');kind,x=next(iter(n['members'].items()));x=x['members']
 if kind=='ColumnRef':require(set(x)=={'fields','location'},'column shape');return ('column',)+strings(x['fields'])
 if kind=='ParamRef':require(set(x)=={'number','location'},'parameter shape');return ('parameter',x['number']['value'])
 if kind=='TypeCast':require(set(x)=={'arg','typeName','location'},'cast shape');return ('cast',expr(x['arg']),strings(x['typeName']['members']['names']))
 if kind=='FuncCall':require(set(x)=={'funcname','funcformat','location'} and x['funcformat']['value']=='COERCE_EXPLICIT_CALL','function shape');return ('function',strings(x['funcname']))
 if kind=='A_Expr':require(set(x)=={'kind','name','lexpr','rexpr','location'} and x['kind']['value']=='AEXPR_OP' and len(strings(x['name']))==1,'operator shape');return (strings(x['name'])[0],expr(x['lexpr']),expr(x['rexpr']))
 if kind=='A_Const':require(set(x)=={'ival','location'} and set(x['ival']['members']) in [set(),{'ival'}],'integer constant shape');return ('integer',x['ival']['members'].get('ival',{'value':'0'})['value'])
 if kind=='BoolExpr':require(set(x)=={'boolop','args','location'} and x['boolop']['value']=='AND_EXPR','conjunction shape');return ('and',tuple(expr(a) for a in x['args']['items']))
 if kind=='NullTest':require(set(x)=={'arg','nulltesttype','location'} and x['nulltesttype']['value']=='IS_NULL','null shape');return ('is_null',expr(x['arg']))
 if kind=='SubLink':
  require(set(x)=={'subLinkType','subselect','location'} and x['subLinkType']['value']=='EXISTS_SUBLINK','subquery shape');s=x['subselect']['members']['SelectStmt']['members'];require(set(s)=={'targetList','fromClause','whereClause','limitOption','op'} and s['limitOption']['value']=='LIMIT_OPTION_DEFAULT' and s['op']['value']=='SETOP_NONE','complete parent observation')
  require(len(s['targetList']['items'])==1 and expr(s['targetList']['items'][0]['members']['ResTarget']['members']['val'])==('integer','1'),'fixed existence projection');require(len(s['fromClause']['items'])==1,'single parent');r=s['fromClause']['items'][0]['members']['RangeVar']['members'];require(r['schemaname']['value']=='truss' and r['relname']['value']=='feed_tx' and r['alias']['members']['aliasname']['value']=='t','original parent source');return ('exists',expr(s['whereClause']))
 raise ValueError('unsupported predicate expression '+kind)
col=lambda alias,name:('column',alias,name)
param=lambda n,kind:('cast',('parameter',str(n)),('pg_catalog',kind))
eq=lambda a,b:('=',a,b)
context=lambda a:[eq(col(a,'source_epoch'),param(1,'text')),eq(col(a,'feed_profile'),param(2,'text')),eq(col(a,'original_writer_xid'),('function',('pg_catalog','pg_current_xact_id_if_assigned')))]
nulls=[('is_null',col('t',n)) for n in ['finalized_generation','manifest_bytes','manifest_sha256']]
parent=('and',tuple([eq(col('t',n),col('m',n)) for n in ['source_epoch','feed_profile','original_writer_xid']]+[eq(col('t','membership_generation'),param(3,'int8'))]+nulls))
expected=[('and',tuple(context('t')+[eq(col('t','membership_generation'),param(3,'int8'))])),('and',tuple(context('m'))),('and',tuple(context('m')+[eq(col('m','registration_address'),param(4,'int8')),('is_null',col('m','delivery_ordinal')),('>',param(4,'int8'),('integer','0')),('>=',param(5,'int8'),('integer','0')),('exists',parent)])),('and',tuple(context('t')+[eq(col('t','membership_generation'),param(3,'int8')),('>',param(3,'int8'),('integer','0'))]+nulls))]
nodes=[];pins=[]
for family in ['feed-finalization-clear','feed-finalization-assign-publish']:
 p=root/(family+'-v0.1.proposal.umf.json');m=json.loads(p.read_text());nodes += [s['members']['stmt']['members']['UpdateStmt']['members']['whereClause'] for s in m['modules'][0]['elements'][0]['extensions']['umf.postgresql']['root']['members']['stmts']['items']];pins.append({'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
def verify(candidate):require([expr(n) for n in candidate]==expected,'complete original predicates and correlated parent')
verify(nodes);controls=[]
for label,mutate in [('missing context predicate',lambda x:x[0]['members']['BoolExpr']['members']['args']['items'].pop(0)),('missing captured generation',lambda x:x[0]['members']['BoolExpr']['members']['args']['items'].pop()),('duplicate narrowing predicate',lambda x:x[1]['members']['BoolExpr']['members']['args']['items'].append(copy.deepcopy(x[1]['members']['BoolExpr']['members']['args']['items'][0]))),('omitted parent check',lambda x:x[2]['members']['BoolExpr']['members']['args']['items'].pop()),('omitted cleared hash check',lambda x:x[3]['members']['BoolExpr']['members']['args']['items'].pop())]:
 x=copy.deepcopy(nodes);mutate(x)
 try:verify(x)
 except ValueError:controls.append({'case':label,'refused':True})
 else:raise ValueError('accepted '+label)
r={'scope':'Four exact original context/generation/NULL/address/ordinal predicate trees and complete correlated parent EXISTS only. Returning descriptors, trigger/helper side effects, authority/resources/native semantics remain separate.','modelPins':pins,'statements':4,'controls':controls,'nativeExecution':False,'complete':False}
Path('docs/helix/04-build/evidence/design-audit/feed-finalization-predicates.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'statements':4,'refusals':len(controls),'nativeExecution':False}))
