"""Complete original source column/projection parity only; no predicate/native proof."""
import copy,hashlib,json
from pathlib import Path
root=Path('docs/helix/02-design/contracts')
layout=json.loads((root/'feed-native-layout-v0.1.proposal.umf.json').read_text());lookup_path=root/'feed-original-custody-lookup-v0.1.proposal.umf.json';lookup=json.loads(lookup_path.read_text())
def require(ok,msg):
 if not ok:raise ValueError(msg)
def stmts(m):return m['modules'][0]['elements'][0]['extensions']['umf.postgresql']['root']['members']['stmts']['items']
def strings(n):return [v['members']['String']['members']['sval']['value'] for v in n['items']]
def column(n):
 x=n['members']['ColumnRef']['members'];require(strings(x['fields'])[0]=='t','original alias');require(len(strings(x['fields']))==2,'exact column');return strings(x['fields'])[1]
columns={}
for stmt in stmts(layout):
 n=stmt['members']['stmt']['members']['CreateStmt']['members'];table=n['relation']['members']['relname']['value'];columns[table]={}
 for elt in n['tableElts']['items']:
  if 'ColumnDef' in elt['members']:
   c=elt['members']['ColumnDef']['members'];columns[table][c['colname']['value']]=strings(c['typeName']['members']['names'])[-1]
def predicate_and_order(n,table):
 order={'feed_member':'registration_address','feed_prerequisite':'prerequisite_address','feed_configuration_prerequisite':'configuration_address'}.get(table)
 require(set(n)=={'targetList','fromClause','whereClause','limitOption','op'}|({'sortClause'} if order else set()),'closed complete collection statement')
 require(n['limitOption']['value']=='LIMIT_OPTION_DEFAULT' and n['op']['value']=='SETOP_NONE','no limit/set operation')
 b=n['whereClause']['members']['BoolExpr']['members'];require(set(b)=={'boolop','args','location'} and b['boolop']['value']=='AND_EXPR','complete conjunction')
 predicates=b['args']['items'];require(len(predicates)==3,'exact context predicates')
 for i,(expr,name) in enumerate(zip(predicates,['source_epoch','feed_profile','original_writer_xid'])):
  x=expr['members']['A_Expr']['members'];require(set(x)=={'kind','name','lexpr','rexpr','location'} and x['kind']['value']=='AEXPR_OP' and strings(x['name'])==['='] and column(x['lexpr'])==name,'original equality')
  if i<2:
   c=x['rexpr']['members']['TypeCast']['members'];require(set(c)=={'arg','typeName','location'} and strings(c['typeName']['members']['names'])==['pg_catalog','text'],'original context cast')
   q=c['arg']['members']['ParamRef']['members'];require(set(q)=={'number','location'} and q['number']['value']==str(i+1),'original ordered parameter')
  else:
   f=x['rexpr']['members']['FuncCall']['members'];require(set(f)=={'funcname','funcformat','location'} and strings(f['funcname'])==['pg_catalog','pg_current_xact_id_if_assigned'] and f['funcformat']['value']=='COERCE_EXPLICIT_CALL','original assigned transaction observation')
 if order:
  sorts=n['sortClause']['items'];require(len(sorts)==1,'single address collection order');x=sorts[0]['members']['SortBy']['members'];require(set(x)=={'node','sortby_dir','sortby_nulls','location'} and column(x['node'])==order and x['sortby_dir']['value']=='SORTBY_DEFAULT' and x['sortby_nulls']['value']=='SORTBY_NULLS_DEFAULT','original collection order')
def verify(model):
 seen=set();results=[]
 for stmt in stmts(model):
  n=stmt['members']['stmt']['members']['SelectStmt']['members'];sources=n['fromClause']['items'];require(len(sources)==1,'one original table');relation=sources[0]['members']['RangeVar']['members'];table=relation['relname']['value'];require(relation['schemaname']['value']=='truss' and relation['alias']['members']['aliasname']['value']=='t','source relation');require(table in columns and table not in seen,'table membership');seen.add(table);predicate_and_order(n,table);projected={};aliases=[]
  for target in n['targetList']['items']:
   t=target['members']['ResTarget']['members'];v=t['val'];kind=next(iter(v['members']))
   if kind=='ColumnRef':name=column(v);form='direct'
   elif kind=='TypeCast':
    x=v['members']['TypeCast']['members'];require(strings(x['typeName']['members']['names'])==['pg_catalog','text'],'exact text cast');name=column(x['arg']);form='text'
   elif kind=='FuncCall':
    x=v['members']['FuncCall']['members'];require(strings(x['funcname'])==['pg_catalog','encode'] and len(x['args']['items'])==2,'exact native encoder');name=column(x['args']['items'][0]);require(x['args']['items'][1]['members']['A_Const']['members']['sval']['members']['sval']['value']=='hex','exact hex');form='hex'
   else:raise ValueError('unsupported projection wrapper')
   require(name in columns[table] and name not in projected,'complete unique source column');projected[name]=form;native=columns[table][name];require(form==('hex' if native=='bytea' else 'direct' if native=='text' else 'text'),'independent native carrier mapping');alias=t.get('name',{}).get('value',name);require(alias==name+('_hex' if form=='hex' else ''),'exact alias');require(alias not in aliases,'unique result alias');aliases.append(alias)
  require(set(projected)==set(columns[table]),'complete authored columns');results.append({'table':table,'columnCount':len(projected),'orderedAliases':aliases})
 require(seen==set(columns),'complete table membership');return results
result=verify(lookup);controls=[]
for label,mutation in [('missing column',lambda x:stmts(x)[0]['members']['stmt']['members']['SelectStmt']['members']['targetList']['items'].pop()),('duplicate column',lambda x:stmts(x)[0]['members']['stmt']['members']['SelectStmt']['members']['targetList']['items'].append(copy.deepcopy(stmts(x)[0]['members']['stmt']['members']['SelectStmt']['members']['targetList']['items'][0]))),('substituted alias',lambda x:stmts(x)[0]['members']['stmt']['members']['SelectStmt']['members']['targetList']['items'][2]['members']['ResTarget']['members']['name'].update(value='wrong'))]:
 x=copy.deepcopy(lookup);mutation(x)
 try:verify(x)
 except ValueError:controls.append({'case':label,'refused':True})
 else:raise ValueError('accepted '+label)
for label,mutation in [
 ('extra narrowing predicate',lambda n:n['whereClause']['members']['BoolExpr']['members']['args']['items'].append(copy.deepcopy(n['whereClause']['members']['BoolExpr']['members']['args']['items'][0]))),
 ('wrong context parameter',lambda n:n['whereClause']['members']['BoolExpr']['members']['args']['items'][0]['members']['A_Expr']['members']['rexpr']['members']['TypeCast']['members']['arg']['members']['ParamRef']['members']['number'].update(value='2')),
 ('transaction assigning observation substituted',lambda n:n['whereClause']['members']['BoolExpr']['members']['args']['items'][2]['members']['A_Expr']['members']['rexpr']['members']['FuncCall']['members']['funcname']['items'][1]['members']['String']['members']['sval'].update(value='pg_current_xact_id')),
 ('invented LIMIT modifier',lambda n:n.update(limitCount={'kind':'number','value':'1'}))]:
 x=copy.deepcopy(lookup);mutation(stmts(x)[0]['members']['stmt']['members']['SelectStmt']['members'])
 try:verify(x)
 except ValueError:controls.append({'case':label,'refused':True})
 else:raise ValueError('accepted '+label)
r={'scope':'All 47 source columns project once with exact source-driven direct/text/hex carrier and alias correspondence. Exact three context predicates and private address collection order checked; native descriptor/null/clock/authority/resources not qualified.','lookupModelSha256':hashlib.sha256(lookup_path.read_bytes()).hexdigest(),'layoutModelSha256':hashlib.sha256((root/'feed-native-layout-v0.1.proposal.umf.json').read_bytes()).hexdigest(),'tables':result,'controls':controls,'nativeExecution':False,'complete':False}
Path('docs/helix/04-build/evidence/design-audit/feed-custody-projections.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'tables':len(result),'columns':sum(x['columnCount'] for x in result),'refusals':len(controls),'nativeExecution':False}))
